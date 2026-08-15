"""Orchestrates one chat turn: AI requirement extraction -> deterministic
recommendation engine -> AI per-vehicle explanations.

Conversation state (message history + accumulated StructuredRequirements)
is held in a process-local in-memory dict, keyed by conversation_id. This
is a deliberate placeholder, not persisted, lost on restart, and won't
work past a single worker process - the DB schema doesn't have
conversation/message tables yet; adding them is a separate design
decision (see doc/api-contract.md "open items").
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.ai.explanation_generator import ExplanationGenerator, generator as default_generator
from app.ai.requirement_interpreter import RequirementInterpreter, interpreter as default_interpreter
from app.schemas.conversation import ChatMessage, MessageResponse
from app.schemas.requirement import StructuredRequirements, UserRequirement
from app.services.recommendation_engine import RecommendationEngine, engine as default_engine

# Czech, like every other user-facing string in this module - see
# doc/prompt/CLAUDE.md's language convention. This one in particular went
# unnoticed as English for a while: nothing rendered it live until the
# frontend was wired to the real API (frontend/src/api/conversation.ts) -
# the scripted frontend mock it replaced had its own separately-authored
# Czech copy, so a wrong language here was invisible until then.
INTRO_MESSAGE = (
    "Ahoj! Řekněte mi, jak budete své nové auto využívat — kde jezdíte, kdo s vámi jezdí, "
    "co je pro vás nejdůležitější — a já to přetavím do konkrétních parametrů a vyberu vám "
    "reálné vozy k porovnání."
)

_FIELD_LABELS = {
    "body_type": "Karoserie",
    "min_seats": "Počet míst",
    "budget_max": "Rozpočet",
    "fuel_type": "Palivo",
    "drivetrain": "Pohon",
    "priorities": "Priority",
}


@dataclass
class _ConversationState:
    history: list[ChatMessage] = field(default_factory=list)
    requirements: StructuredRequirements = field(default_factory=StructuredRequirements)


class UnknownConversationError(KeyError):
    pass


class ConversationOrchestrator:
    """Owns in-memory conversation state and drives one chat turn through
    the AI layer and recommendation engine, per
    `drivewise-ai-recommendations`'s Code style section. The
    `_conversations` dict is real per-instance state (not just an
    injected dependency), which is exactly the case for a class per
    `drivewise-architecture`'s Code style section - previously a bare
    module-level global, now encapsulated here instead.
    """

    def __init__(
        self,
        requirement_interpreter: RequirementInterpreter | None = None,
        recommendation_engine: RecommendationEngine | None = None,
        explanation_generator: ExplanationGenerator | None = None,
    ) -> None:
        """Args:
            requirement_interpreter: Turns conversation text into
                structured requirements. Defaults to the shared
                `app.ai.requirement_interpreter.interpreter` singleton.
            recommendation_engine: Filters and ranks the catalog. Defaults
                to the shared
                `app.services.recommendation_engine.engine` singleton.
            explanation_generator: Generates per-vehicle explanations.
                Defaults to the shared
                `app.ai.explanation_generator.generator` singleton.
        """
        self._requirement_interpreter = requirement_interpreter or default_interpreter
        self._recommendation_engine = recommendation_engine or default_engine
        self._explanation_generator = explanation_generator or default_generator
        self._conversations: dict[str, _ConversationState] = {}

    def start_conversation(self) -> tuple[str, str]:
        """Creates a new, empty conversation.

        Returns:
            A `(conversation_id, intro_message)` pair - `conversation_id`
            identifies this conversation for subsequent `handle_message`
            calls, `intro_message` is the assistant's opening line to
            show the user immediately.
        """
        conversation_id = str(uuid.uuid4())
        self._conversations[conversation_id] = _ConversationState()
        return conversation_id, INTRO_MESSAGE

    @staticmethod
    def _merge_requirements(
        existing: StructuredRequirements, update: StructuredRequirements
    ) -> tuple[StructuredRequirements, set[str]]:
        """Merges only the fields the AI actually populated this turn and
        reports which fields changed, so the UI can flash updated cards.

        Args:
            existing: Requirements accumulated so far this conversation.
            update: Newly extracted requirements from this turn - fields
                the model left unset are `None`/empty and ignored.

        Returns:
            A `(merged, changed)` pair: `merged` is `existing` with every
            non-empty field from `update` applied; `changed` is the set
            of field names whose value was actually different from
            `existing` (used to flag which requirement cards changed).
        """
        changed: set[str] = set()
        merged_data = existing.model_dump()
        for field_name, value in update.model_dump().items():
            if value in (None, [], ""):
                continue
            if merged_data.get(field_name) != value:
                changed.add(field_name)
            merged_data[field_name] = value
        return StructuredRequirements.model_validate(merged_data), changed

    @staticmethod
    def _to_user_requirements(
        requirements: StructuredRequirements, changed: set[str], source_message: str
    ) -> list[UserRequirement]:
        """Builds the human-readable "requirements drawer" cards for one
        turn's requirements snapshot.

        Args:
            requirements: The (possibly just-merged) requirements to
                render as cards - one card per populated field.
            changed: Field names to mark `changed=True` on their card
                (drives the UI's flash-on-update animation).
            source_message: The user message these requirements were
                extracted from, shown as the card's quoted source.

        Returns:
            One `UserRequirement` card per populated field of
            `requirements`, in `_FIELD_LABELS`'s display order.
        """
        cards = []
        for field_name, label in _FIELD_LABELS.items():
            value = getattr(requirements, field_name)
            if value in (None, [], ""):
                continue
            if field_name == "budget_max":
                display_value = f"{value.amount:,.0f} {value.currency}"
            elif field_name == "priorities":
                display_value = ", ".join(value)
            elif hasattr(value, "value"):
                display_value = str(value.value)
            else:
                display_value = str(value)
            cards.append(
                UserRequirement(
                    label=label,
                    value=display_value,
                    source=f'"{source_message}"',
                    changed=field_name in changed,
                )
            )
        return cards

    def handle_message(self, db: Session, conversation_id: str, text: str) -> MessageResponse:
        """Processes one user message: extracts/merges requirements, then
        (once there's enough to search on) filters, ranks, and explains
        matching vehicles.

        Args:
            db: Database session to query the catalog through.
            conversation_id: Id returned by an earlier `start_conversation`
                call.
            text: The user's new message.

        Returns:
            The assistant's reply for this turn: either a follow-up
            question (if requirements are still underspecified, in which
            case `vehicles` is empty and `searched` is `False`) or an
            updated shortlist (`searched=True`, though `vehicles` can
            still legitimately be empty - nothing matched) with
            explanations where the AI layer is configured.

        Raises:
            UnknownConversationError: `conversation_id` doesn't match any
                conversation started via `start_conversation` (e.g. it
                expired, or the process restarted - state isn't
                persisted, see the module docstring).
        """
        state = self._conversations.get(conversation_id)
        if state is None:
            raise UnknownConversationError(conversation_id)

        extraction = self._requirement_interpreter.interpret(state.history, text)
        state.history.append(ChatMessage(role="user", text=text))

        if extraction.requirements is None:
            assistant_text = extraction.follow_up_question or "Můžete mi prosím říct trochu více o tom, co potřebujete?"
            state.history.append(ChatMessage(role="assistant", text=assistant_text))
            return MessageResponse(
                assistant_text=assistant_text,
                requirements=self._to_user_requirements(state.requirements, set(), text),
                structured_requirements=state.requirements,
                vehicles=[],
                searched=False,
            )

        merged, changed = self._merge_requirements(state.requirements, extraction.requirements)
        state.requirements = merged

        vehicles = self._recommendation_engine.recommend(db, merged)

        explained = []
        for vehicle in vehicles:
            try:
                explanation = self._explanation_generator.explain(vehicle, merged)
            except RuntimeError:
                # AI layer not configured (no ANTHROPIC_API_KEY) - degrade to
                # an unexplained result rather than failing the whole request.
                explanation = None
            explained.append(vehicle.model_copy(update={"explanation": explanation}) if explanation else vehicle)

        assistant_text = (
            f"Na základě toho, co jste mi řekli, jsem aktualizoval váš výběr — aktuálně vyhovuje "
            f"{len(explained)} vozů."
            if explained
            else "Aktualizoval jsem vaše požadavky, ale v katalogu zatím nic nevyhovuje — chcete něco uvolnit?"
        )
        state.history.append(ChatMessage(role="assistant", text=assistant_text))

        return MessageResponse(
            assistant_text=assistant_text,
            requirements=self._to_user_requirements(merged, changed, text),
            structured_requirements=merged,
            vehicles=explained,
            searched=True,
        )


# Shared instance the API layer uses (app/api/conversations.py) - holds
# the actual conversation state, so unlike the AI-layer/engine singletons
# it isn't just a construction-is-cheap convenience; this one *must* be
# shared across requests within a process for conversations to work at
# all (see the module docstring on why that's a known limitation).
orchestrator = ConversationOrchestrator()
