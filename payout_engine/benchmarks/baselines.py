"""Simple formula baselines used in casino-shaped benchmarks."""

from __future__ import annotations

import numpy as np

from payout_engine.core.curves import ExponentialCurve, PowerLawCurve
from payout_engine.core.models import Bucket, PayoutStructure
from payout_engine.core.normalizer import NormalizedSpec


def baseline_geometric(spec: NormalizedSpec) -> PayoutStructure:
    ideal, _ = ExponentialCurve().payouts(
        spec.winner_count,
        spec.prize_pool_cents,
        spec.top_prize_cents,
        spec.min_prize_cents,
    )
    return _cents_per_rank(spec, np.rint(ideal).astype(int), backend="baseline_geometric")


def baseline_raw_power_law(spec: NormalizedSpec) -> PayoutStructure:
    ideal, meta = PowerLawCurve().payouts(
        spec.winner_count,
        spec.prize_pool_cents,
        spec.top_prize_cents,
        spec.min_prize_cents,
    )
    amounts = np.rint(ideal).astype(int)
    structure = _cents_per_rank(spec, amounts, backend="baseline_raw_power_law")
    structure.alpha = float(meta.get("alpha", 0.0))
    return structure


def baseline_rounded_power_law(spec: NormalizedSpec) -> PayoutStructure:
    """Power-law then round each rank to whole euros (100 cents)."""
    ideal, meta = PowerLawCurve().payouts(
        spec.winner_count,
        spec.prize_pool_cents,
        spec.top_prize_cents,
        spec.min_prize_cents,
    )
    amounts = (np.rint(ideal / 100.0) * 100).astype(int)
    amounts = np.maximum(amounts, spec.min_prize_cents)
    amounts[0] = spec.top_prize_cents
    structure = _cents_per_rank(spec, amounts, backend="baseline_rounded_power_law")
    structure.alpha = float(meta.get("alpha", 0.0))
    return structure


def _cents_per_rank(
    spec: NormalizedSpec, amounts: np.ndarray, backend: str
) -> PayoutStructure:
    amounts = [int(x) for x in amounts]
    drift = spec.prize_pool_cents - sum(amounts)
    if amounts:
        amounts[0] += drift
    buckets: list[Bucket] = []
    start = 1
    current = amounts[0]
    for i, amt in enumerate(amounts, start=1):
        if amt != current:
            buckets.append(Bucket(start=start, end=i - 1, amount_cents=current))
            start = i
            current = amt
    buckets.append(Bucket(start=start, end=len(amounts), amount_cents=current))
    return PayoutStructure(
        buckets=buckets,
        currency=spec.currency,
        prize_pool_cents=spec.prize_pool_cents,
        winner_count=spec.winner_count,
        top_prize_cents=buckets[0].amount_cents,
        min_prize_cents=spec.min_prize_cents,
        style=spec.style,
        nice_profile=spec.nice_profile,
        backend=backend,
    )
