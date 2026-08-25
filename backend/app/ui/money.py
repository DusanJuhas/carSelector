"""Money formatting, ported from frontend/src/utils/money.ts."""

from babel.numbers import format_decimal, get_currency_symbol

from app.schemas.common import Money


def format_money(money: Money, locale: str = "cs_CZ") -> str:
    """Formats `money` as a localized currency string.

    Ported from the frontend's `Intl.NumberFormat('cs-CZ', {style:
    'currency', maximumFractionDigits: 0})`. Composed from
    `format_decimal` + `get_currency_symbol` rather than
    `babel.numbers.format_currency` directly: that function always
    renders the currency's standard fraction digits (2, for CZK)
    regardless of a custom `format` pattern or `decimal_quantization`
    (verified empirically - neither suppresses the ",00"), so there's no
    single-call way to get a "no decimals" currency string out of it.

    Args:
        money: Amount + ISO 4217 currency code to format.
        locale: Babel locale to format for. 'cs_CZ' is the only locale
            this app ships today - see `app/ui/i18n.py`'s module docstring
            for why there's no language switcher yet.

    Returns:
        The formatted string, e.g. "824 900 Kč".
    """
    amount = format_decimal(round(money.amount), locale=locale)
    symbol = get_currency_symbol(money.currency, locale=locale)
    return f"{amount} {symbol}"
