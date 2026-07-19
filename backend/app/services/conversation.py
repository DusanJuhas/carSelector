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

from app.ai import explanation_generator, requirement_interpreter
from app.schemas.conversation import ChatMessage, MessageResponse
from app.schemas.requirement import StructuredRequirements, UserRequirement
from app.services import recommendation_engine

INTRO_MESSAGE = (
    "Hi! Tell me about how you'll use your next car - where you drive, who's riding along, "
    "what matters most - and I'll translate that into the right specs and shortlist real cars "
    "for you."
)

_FIELD_LABELS = {
    "body_type": "Body type",
    "min_seats": "Seating",
    "budget_max": "Budget",
    "fuel_type": "Fuel type",
    "drivetrain": "Drivetrain",
    "priorities": "Priorities",
}


@dataclass
class _ConversationState:
    history: list[ChatMessage] = field(default_factory=list)
    requirements: StructuredRequirements = field(default_factory=StructuredRequirements)


_conversations: dict[str, _ConversationState] = {}


class UnknownConversationError(KeyError):
    pass


def start_conversation() -> tuple[str, str]:
    conversation_id = str(uuid.uuid4())
    _conversations[conversation_id] = _ConversationState()
    return conversation_id, INTRO_MESSAGE


def _merge_requirements(
    existing: StructuredRequirements, update: StructuredRequirements
) -> tuple[StructuredRequirements, set[str]]:
    """Merges only the fields the AI actually populated this turn and
    reports which fields changed, so the UI can flash updated cards.
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


def _to_user_requirements(
    requirements: StructuredRequirements, changed: set[str], source_message: str
) -> list[UserRequirement]:
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


def handle_message(db: Session, conversation_id: str, text: str) -> MessageResponse:
    state = _conversations.get(conversation_id)
    if state is None:
        raise UnknownConversationError(conversation_id)

    extraction = requirement_interpreter.extract_requirements(state.history, text)
    state.history.append(ChatMessage(role="user", text=text))

    if extraction.requirements is None:
        assistant_text = extraction.follow_up_question or "Could you tell me a bit more about what you need?"
        state.history.append(ChatMessage(role="assistant", text=assistant_text))
        return MessageResponse(
            assistant_text=assistant_text,
            requirements=_to_user_requirements(state.requirements, set(), text),
            structured_requirements=state.requirements,
            vehicles=[],
        )

    merged, changed = _merge_requirements(state.requirements, extraction.requirements)
    state.requirements = merged

    vehicles = recommendation_engine.recommend(db, merged)

    explained = []
    for vehicle in vehicles:
        try:
            explanation = explanation_generator.explain(vehicle, merged)
        except RuntimeError:
            # AI layer not configured (no ANTHROPIC_API_KEY) - degrade to
            # an unexplained result rather than failing the whole request.
            explanation = None
        explained.append(vehicle.model_copy(update={"explanation": explanation}) if explanation else vehicle)

    assistant_text = (
        f"Updated your shortlist based on what you've told me - {len(explained)} vehicles match so far."
        if explained
        else "I've updated your requirements, but nothing in the catalog matches yet - want to loosen anything?"
    )
    state.history.append(ChatMessage(role="assistant", text=assistant_text))

    return MessageResponse(
        assistant_text=assistant_text,
        requirements=_to_user_requirements(merged, changed, text),
        structured_requirements=merged,
        vehicles=explained,
    )
