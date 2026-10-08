"""Covers `catalog.list_trim_alternatives` - one configuration per trim,
for comparing a model's trims side by side."""

from app.services import catalog
from tests.conftest import SeededData


def test_lists_every_trim_once_with_the_origin_for_its_own_trim(seeded_session: SeededData) -> None:
    choices = catalog.list_trim_alternatives(seeded_session.session, seeded_session.config_people_fwd_id)

    assert [choice.trim_name for choice in choices] == ["People", "R-Line People"]
    current, other = choices
    assert current.is_current and current.same_engine
    assert current.vehicle.configuration_id == seeded_session.config_people_fwd_id
    # The seeded R-Line only comes with the AWD petrol engine - no same
    # engine to match, so its cheapest (only) configuration stands in.
    assert not other.is_current and not other.same_engine
    assert other.vehicle.configuration_id == seeded_session.config_rline_awd_id


def test_unknown_configuration_has_no_alternatives(seeded_session: SeededData) -> None:
    assert catalog.list_trim_alternatives(seeded_session.session, 999_999) == []
