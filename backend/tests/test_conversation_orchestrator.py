"""Covers `ConversationOrchestrator.handle_wizard_answers` - the wizard's
entry point into the same conversation state, recommend, and explain
pipeline `handle_message` uses for chat turns (see
`app/services/conversation.py` and `app/ui/components/wizard.py`).
Exercises the real recommendation engine against the seeded catalog
(same fixture the API test suite uses), not a mock, since ranking
correctness is the point.
"""

import pytest

from app.models.enums import Drivetrain
from app.schemas.common import Money
from app.schemas.requirement import StructuredRequirements
from app.services.conversation import ConversationOrchestrator, UnknownConversationError
from tests.conftest import SeededData


def test_handle_wizard_answers_searches_without_ai_extraction(seeded_session: SeededData) -> None:
    # No ANTHROPIC_API_KEY in the test environment - unlike handle_message,
    # this must still succeed and return ranked vehicles, since the wizard
    # skips the AI requirement-extraction step entirely (see
    # WizardState.to_structured_requirements). Only the per-vehicle
    # explanation step (best-effort) touches the AI layer.
    orchestrator = ConversationOrchestrator()
    conversation_id, _ = orchestrator.start_conversation()

    requirements = StructuredRequirements(
        body_type="SUV",
        budget_max=Money(amount=1_100_000, currency="CZK"),
        fuel_type="petrol",
        drivetrain=Drivetrain.awd,
    )

    result = orchestrator.handle_wizard_answers(
        seeded_session.session, conversation_id, requirements, "Vyplnil(a) jsem průvodce: ..."
    )

    assert result.searched is True
    assert len(result.vehicles) == 2
    # AWD is a soft preference (see RecommendationEngine._score) - the AWD
    # configuration should outrank the FWD one and be flagged top_pick.
    assert result.vehicles[0].configuration_id == seeded_session.config_centre_awd_id
    assert result.vehicles[0].top_pick is True
    assert result.vehicles[0].explanation is None  # AI layer not configured - degrades gracefully.


def test_handle_wizard_answers_records_requirements_for_the_drawer(seeded_session: SeededData) -> None:
    orchestrator = ConversationOrchestrator()
    conversation_id, _ = orchestrator.start_conversation()

    requirements = StructuredRequirements(
        budget_max=Money(amount=1_100_000, currency="CZK"), notes="Preference značky: Škoda"
    )

    result = orchestrator.handle_wizard_answers(seeded_session.session, conversation_id, requirements, "summary")

    labels = {card.label: card.value for card in result.requirements}
    assert labels["Rozpočet"] == "1,100,000 CZK"
    assert labels["Poznámky"] == "Preference značky: Škoda"


def test_handle_wizard_answers_merges_onto_a_prior_chat_turn(seeded_session: SeededData) -> None:
    # A wizard turn after a chat turn (or vice versa) should merge onto the
    # same accumulated StructuredRequirements, not reset it - the wizard is
    # an alternate input channel into one conversation, not a separate flow.
    orchestrator = ConversationOrchestrator()
    conversation_id, _ = orchestrator.start_conversation()

    orchestrator.handle_wizard_answers(
        seeded_session.session, conversation_id, StructuredRequirements(body_type="SUV"), "first"
    )
    result = orchestrator.handle_wizard_answers(
        seeded_session.session,
        conversation_id,
        StructuredRequirements(budget_max=Money(amount=900_000, currency="CZK")),
        "second",
    )

    labels = {card.label for card in result.requirements}
    assert "Karoserie" in labels
    assert "Rozpočet" in labels


def test_handle_wizard_answers_raises_for_unknown_conversation(seeded_session: SeededData) -> None:
    orchestrator = ConversationOrchestrator()
    with pytest.raises(UnknownConversationError):
        orchestrator.handle_wizard_answers(
            seeded_session.session, "not-a-real-id", StructuredRequirements(), "summary"
        )
