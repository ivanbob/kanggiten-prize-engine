"""Import and comment on an existing casino payout table."""

from __future__ import annotations

from payout_engine.core.models import (
    Bucket,
    ExistingPayoutInput,
    PayoutStructure,
    Style,
)
from payout_engine.core.money import major_to_cents
from payout_engine.core.normalizer import NormalizedSpec, normalize
from payout_engine.core.models import (
    ConstraintsSpec,
    MinPrizeSpec,
    MinPrizeMode,
    TopPrizeSpec,
    TopPrizeMode,
    TournamentInput,
    WinnersSpec,
    WinnerMode,
)


def buckets_from_rows(rows: list[dict], currency: str = "EUR") -> list[Bucket]:
    buckets: list[Bucket] = []
    for row in rows:
        start = int(row.get("from", row.get("start")))
        end = int(row.get("to", row.get("end", start)))
        amount = row.get("amount", row.get("amount_cents"))
        if "amount_cents" in row and "amount" not in row:
            cents = int(row["amount_cents"])
        else:
            cents = major_to_cents(amount)
        buckets.append(Bucket(start=start, end=end, amount_cents=cents))
    buckets.sort(key=lambda b: b.start)
    return buckets


def structure_from_existing(inp: ExistingPayoutInput) -> PayoutStructure:
    buckets = buckets_from_rows(inp.payouts, inp.currency)
    winner_count = buckets[-1].end if buckets else 0
    pool = (
        major_to_cents(inp.prize_pool)
        if inp.prize_pool is not None
        else sum(b.paid_cents for b in buckets)
    )
    return PayoutStructure(
        buckets=buckets,
        currency=inp.currency,
        prize_pool_cents=pool,
        winner_count=winner_count,
        top_prize_cents=buckets[0].amount_cents if buckets else 0,
        min_prize_cents=buckets[-1].amount_cents if buckets else 0,
        style=inp.style.value,
        nice_profile=inp.constraints.nice_number_profile.value,
        backend="imported",
    )


def spec_from_existing(inp: ExistingPayoutInput, structure: PayoutStructure) -> NormalizedSpec:
    winners = structure.winner_count
    entrants = inp.entrants or winners
    pool_major = structure.prize_pool_cents / 100.0
    top_major = structure.top_prize_cents / 100.0
    min_major = structure.min_prize_cents / 100.0
    tournament = TournamentInput(
        currency=inp.currency,
        prize_pool=inp.prize_pool if inp.prize_pool is not None else pool_major,
        entrants=entrants,
        entry_fee=inp.entry_fee,
        winners=WinnersSpec(mode=WinnerMode.COUNT, value=float(winners)),
        top_prize=TopPrizeSpec(mode=TopPrizeMode.FIXED, value=top_major),
        minimum_prize=MinPrizeSpec(mode=MinPrizeMode.FIXED, value=min_major),
        style=inp.style,
        constraints=inp.constraints,
    )
    return normalize(tournament)


def describe_issues(structure: PayoutStructure, spec: NormalizedSpec) -> list[str]:
    notes: list[str] = []
    prizes = [b.amount_cents for b in structure.buckets]
    for a, b in zip(prizes, prizes[1:]):
        if b and a / b > 4:
            notes.append("large discontinuity between adjacent prize tiers")
            break
    sizes = [b.size for b in structure.buckets]
    if any(b < a for a, b in zip(sizes, sizes[1:])):
        notes.append("bucket sizes shrink toward lower ranks")
    if len(structure.buckets) > spec.max_buckets:
        notes.append("more tiers than a compact casino widget typically shows")
    if structure.total_paid_cents() != spec.prize_pool_cents:
        notes.append("published table does not sum to the prize pool")
    if not notes:
        notes.append("no structural red flags beyond metric sub-scores")
    return notes
