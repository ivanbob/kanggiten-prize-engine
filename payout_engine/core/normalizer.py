"""Normalize operator JSON into a frozen integer-cent spec."""

from __future__ import annotations

from dataclasses import dataclass

from payout_engine.core.defaults import (
    DEFAULT_MIN_PRIZE_ENTRY_MULTIPLE,
    DEFAULT_WINNER_PERCENT,
    ENGINE_PROFILE_NAME,
    STYLE_P1_FRACTION,
    STYLE_WINNER_PERCENT,
)
from payout_engine.core.models import (
    MinPrizeMode,
    NiceNumberProfile,
    TopPrizeMode,
    TournamentInput,
    WinnerMode,
)
from payout_engine.core.money import major_to_cents
from payout_engine.core.nice_numbers import NiceNumberGenerator


class NormalizationError(ValueError):
    """Input cannot be turned into a feasible integer-cent spec."""


@dataclass(frozen=True)
class NormalizedSpec:
    currency: str
    prize_pool_cents: int
    entrants: int
    entry_fee_cents: int
    winner_count: int
    top_prize_cents: int
    min_prize_cents: int
    style: str
    max_buckets: int
    bucket_size_monotonicity: str
    nice_profile: str
    custom_nice_majors: tuple[float, ...]
    top_prize_mode: str
    min_prize_mode: str
    winner_mode: str
    profile: str = ENGINE_PROFILE_NAME

    def to_public_dict(self) -> dict:
        return {
            "currency": self.currency,
            "prize_pool_cents": self.prize_pool_cents,
            "entrants": self.entrants,
            "entry_fee_cents": self.entry_fee_cents,
            "winner_count": self.winner_count,
            "top_prize_cents": self.top_prize_cents,
            "min_prize_cents": self.min_prize_cents,
            "style": self.style,
            "max_buckets": self.max_buckets,
            "bucket_size_monotonicity": self.bucket_size_monotonicity,
            "nice_profile": self.nice_profile,
            "top_prize_mode": self.top_prize_mode,
            "profile": self.profile,
        }


def normalize(inp: TournamentInput) -> NormalizedSpec:
    pool = major_to_cents(inp.prize_pool)
    entry = major_to_cents(inp.entry_fee)
    style = inp.style.value
    winners = _winner_count(inp, style)
    min_prize = _min_prize_cents(inp, entry, pool, winners)
    nice = NiceNumberGenerator(
        profile=inp.constraints.nice_number_profile,
        custom_majors=inp.constraints.custom_nice_numbers,
        max_cents=pool,
    )
    top = _top_prize_cents(inp, pool, min_prize, winners, nice)
    _assert_feasible(pool, winners, top, min_prize)
    return NormalizedSpec(
        currency=inp.currency.upper(),
        prize_pool_cents=pool,
        entrants=inp.entrants,
        entry_fee_cents=entry,
        winner_count=winners,
        top_prize_cents=top,
        min_prize_cents=min_prize,
        style=style,
        max_buckets=min(inp.constraints.max_buckets, winners),
        bucket_size_monotonicity=inp.constraints.bucket_size_monotonicity.value,
        nice_profile=inp.constraints.nice_number_profile.value,
        custom_nice_majors=tuple(inp.constraints.custom_nice_numbers),
        top_prize_mode=inp.top_prize.mode.value,
        min_prize_mode=inp.minimum_prize.mode.value,
        winner_mode=inp.winners.mode.value,
    )


def _winner_count(inp: TournamentInput, style: str) -> int:
    if inp.winners.mode is WinnerMode.COUNT:
        if inp.winners.value is None:
            raise NormalizationError("winners.value is required for count mode")
        count = int(inp.winners.value)
    else:
        pct = (
            inp.winners.value
            if inp.winners.value is not None
            else STYLE_WINNER_PERCENT.get(style, DEFAULT_WINNER_PERCENT)
        )
        if pct <= 0 or pct > 100:
            raise NormalizationError("winner percentage must be in (0, 100]")
        count = max(1, int(round(inp.entrants * pct / 100.0)))
    if count < 1:
        raise NormalizationError("winner_count must be >= 1")
    if count > inp.entrants:
        raise NormalizationError("winner_count cannot exceed entrants")
    return count


def _min_prize_cents(
    inp: TournamentInput, entry_cents: int, pool: int, winners: int
) -> int:
    mode = inp.minimum_prize.mode
    if mode is MinPrizeMode.FIXED:
        if inp.minimum_prize.value is None:
            raise NormalizationError("minimum_prize.value required for fixed mode")
        value = major_to_cents(inp.minimum_prize.value)
    elif mode is MinPrizeMode.PERCENTAGE:
        if inp.minimum_prize.value is None:
            raise NormalizationError("minimum_prize.value required for percentage mode")
        value = int(round(pool * float(inp.minimum_prize.value) / 100.0))
    elif mode is MinPrizeMode.AUTOMATIC:
        value = max(entry_cents, int(round(entry_cents * DEFAULT_MIN_PRIZE_ENTRY_MULTIPLE)))
    else:
        multiple = (
            inp.minimum_prize.value
            if inp.minimum_prize.value is not None
            else DEFAULT_MIN_PRIZE_ENTRY_MULTIPLE
        )
        value = int(round(entry_cents * float(multiple)))
    if value < 0:
        raise NormalizationError("minimum prize cannot be negative")
    if winners * value > pool:
        raise NormalizationError("minimum prizes exceed the prize pool")
    return max(value, 0)


def _top_prize_cents(
    inp: TournamentInput,
    pool: int,
    min_prize: int,
    winners: int,
    nice: NiceNumberGenerator,
) -> int:
    max_top = pool - (winners - 1) * min_prize
    min_top = min_prize if winners == 1 else min_prize + 1
    mode = inp.top_prize.mode
    if mode is TopPrizeMode.FIXED:
        if inp.top_prize.value is None:
            raise NormalizationError("top_prize.value required for fixed mode")
        top = major_to_cents(inp.top_prize.value)
    elif mode is TopPrizeMode.POOL_PERCENTAGE:
        if inp.top_prize.value is None:
            raise NormalizationError("top_prize.value required for pool_percentage mode")
        raw = int(round(pool * float(inp.top_prize.value) / 100.0))
        top = nice.nearest(raw)
    else:
        frac = STYLE_P1_FRACTION.get(inp.style.value, 0.15)
        top = nice.nearest(int(round(pool * frac)))
        # Few paid places + low P1 fraction (e.g. flat @ 8%) can leave
        # winners * P1 < pool. Lift auto P1 just enough to consume the pool.
        min_consumable = (pool + winners - 1) // winners
        if top < min_consumable:
            top = nice.ceil(min_consumable)
    top = min(max(top, min_top), max_top)
    if top < min_top:
        raise NormalizationError("top prize is below the minimum prize")
    return top


def _assert_feasible(pool: int, winners: int, top: int, min_prize: int) -> None:
    if top + (winners - 1) * min_prize > pool:
        raise NormalizationError(
            "top prize plus remaining minimums exceeds the prize pool"
        )
    if winners * top < pool:
        raise NormalizationError(
            "top prize is too small to consume the prize pool even if every winner is paid that amount"
        )
