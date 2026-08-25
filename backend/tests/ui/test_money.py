"""Covers app/ui/money.py directly - not a port of anything in the old
frontend suite (it relied on the browser's own `Intl.NumberFormat`,
nothing to unit test there), added because `format_currency`'s
undocumented always-shows-cents behavior (see money.py's docstring) is
exactly the kind of thing worth a regression test.
"""

from app.schemas.common import Money
from app.ui.money import format_money


def test_formats_whole_amount_with_grouping_and_no_decimals() -> None:
    result = format_money(Money(amount=824_900, currency="CZK"))
    assert "824" in result and "900" in result
    assert "," not in result and "." not in result


def test_rounds_to_whole_units() -> None:
    result = format_money(Money(amount=824_900.6, currency="CZK"))
    assert "824" in result and "901" in result


def test_includes_currency_symbol() -> None:
    result = format_money(Money(amount=1000, currency="CZK"))
    assert "Kč" in result
