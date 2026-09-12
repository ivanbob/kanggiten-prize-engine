"""Integer-cent money helpers.

All engine arithmetic uses integer minor units so the prize pool can be
reconciled exactly. Major-unit inputs (EUR/USD) must have at most two
decimal places; they are never stored as floats.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import Union

Number = Union[int, float, str, Decimal]


class MoneyError(ValueError):
    """Invalid monetary amount."""


def major_to_cents(amount: Number) -> int:
    """Convert a major-unit amount (e.g. 20.50 EUR) to integer cents."""
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError) as exc:
        raise MoneyError(f"invalid monetary amount: {amount!r}") from exc
    if value < 0:
        raise MoneyError("monetary amounts cannot be negative")
    cents = value * Decimal(100)
    if cents != cents.to_integral_value():
        raise MoneyError(
            f"amount {amount!r} has more than 2 decimal places; "
            "the engine refuses silent rounding"
        )
    return int(cents)


def cents_to_major(cents: int) -> Decimal:
    """Convert integer cents to a Decimal major-unit amount."""
    return (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))


def cents_to_major_float(cents: int) -> float:
    """JSON-friendly major-unit float with exact 2-decimal representation."""
    return float(cents_to_major(cents))


# Display symbols for supported operator currencies (all use 2-decimal minor units).
CURRENCY_SYMBOLS: dict[str, str] = {
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "DKK": "kr",
    "NOK": "kr",
    "SEK": "kr",
    "CZK": "Kč",
    "TRY": "₺",
    "PLN": "zł",
}

SUPPORTED_CURRENCIES: tuple[str, ...] = tuple(CURRENCY_SYMBOLS.keys())


def currency_symbol(currency: str) -> str:
    code = currency.upper()
    return CURRENCY_SYMBOLS.get(code, f"{code} ")


def format_cents(cents: int, currency: str = "EUR") -> str:
    """Human-readable cashier amount, e.g. €10,000 or €20.50."""
    symbol = currency_symbol(currency)
    major = cents_to_major(cents)
    if cents % 100 == 0:
        body = f"{int(major):,}"
    else:
        body = f"{major:,.2f}"
    # Nordic/CEE codes that share "kr" read clearer with a trailing code when ambiguous.
    if symbol == "kr":
        return f"{body} {currency.upper()}"
    return f"{symbol}{body}"


def floor_div_cents(total: int, count: int) -> int:
    """Largest whole-cent share that `count` winners can receive from `total`."""
    if count <= 0:
        raise MoneyError("count must be positive")
    return int(Decimal(total) / Decimal(count) // 1)
