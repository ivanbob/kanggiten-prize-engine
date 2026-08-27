"""Casino-weighted quality score (0–100). Validity is checked separately."""

from __future__ import annotations

import math

import numpy as np

from payout_engine.core.curves import PowerLawCurve
from payout_engine.core.defaults import CASINO_QUALITY_WEIGHTS, STYLE_P1_FRACTION
from payout_engine.core.models import PayoutStructure, QualityBreakdown
from payout_engine.core.nice_numbers import NiceNumberGenerator
from payout_engine.core.normalizer import NormalizedSpec


def score_structure(
    structure: PayoutStructure,
    spec: NormalizedSpec,
    ideal: np.ndarray | None = None,
) -> QualityBreakdown:
    nice = NiceNumberGenerator(
        profile=spec.nice_profile,
        custom_majors=list(spec.custom_nice_majors),
        max_cents=max(spec.prize_pool_cents, 100),
    )
    if ideal is None:
        ideal, _ = PowerLawCurve().payouts(
            spec.winner_count,
            spec.prize_pool_cents,
            spec.top_prize_cents,
            spec.min_prize_cents,
        )
    amounts = np.array(structure.as_rank_amounts(), dtype=np.float64)
    metrics = {
        "nice_numbers": _nice_score(structure, nice),
        "compactness": _compactness_score(len(structure.buckets), spec.winner_count),
        "marketing_p1": _marketing_p1_score(structure, spec, nice),
        "midfield": _midfield_score(amounts, spec),
        "curve_fit": _curve_fit_score(amounts, ideal),
        "smoothness": _smoothness_score(structure),
        "bucket_progression": _progression_score(structure),
    }
    weights = CASINO_QUALITY_WEIGHTS
    total_w = sum(weights[k] for k in metrics)
    score = sum(metrics[k] * weights[k] for k in metrics) / total_w
    return QualityBreakdown(score=round(float(score), 2), metrics={k: round(v, 2) for k, v in metrics.items()})


def _nice_score(structure: PayoutStructure, nice: NiceNumberGenerator) -> float:
    if not structure.buckets:
        return 0.0
    paid = structure.total_paid_cents() or 1
    good = sum(
        b.paid_cents for b in structure.buckets if nice.contains(b.amount_cents)
    )
    return 100.0 * good / paid


def _compactness_score(n_buckets: int, n_winners: int) -> float:
    if n_winners <= 8:
        return 100.0 if n_buckets <= n_winners else 70.0
    ideal = min(12, n_winners)
    return max(0.0, 100.0 - 8.0 * abs(n_buckets - ideal))


def _marketing_p1_score(
    structure: PayoutStructure, spec: NormalizedSpec, nice: NiceNumberGenerator
) -> float:
    p1 = structure.top_prize_cents
    nice_pts = 100.0 if nice.contains(p1) else 55.0
    target = STYLE_P1_FRACTION.get(spec.style, 0.15)
    actual = p1 / spec.prize_pool_cents if spec.prize_pool_cents else 0.0
    band = 100.0 * math.exp(-((actual - target) ** 2) / (2 * 0.04**2))
    return 0.6 * nice_pts + 0.4 * band


def _midfield_score(amounts: np.ndarray, spec: NormalizedSpec) -> float:
    n = len(amounts)
    if n <= 1:
        return 100.0
    cut = max(1, n // 10)
    mid_share = float(amounts[cut:].sum()) / spec.prize_pool_cents
    target = {"balanced": 0.50, "top_heavy": 0.35, "flat": 0.62}.get(spec.style, 0.50)
    return max(0.0, 100.0 - 280.0 * abs(mid_share - target))


def _curve_fit_score(amounts: np.ndarray, ideal: np.ndarray) -> float:
    n = min(len(amounts), len(ideal))
    if n == 0:
        return 0.0
    mse = float(np.mean((amounts[:n] - ideal[:n]) ** 2))
    scale = float(np.mean(ideal[:n] ** 2)) or 1.0
    rel = mse / scale
    return 100.0 * math.exp(-3.0 * rel)


def _smoothness_score(structure: PayoutStructure) -> float:
    prizes = [b.amount_cents for b in structure.buckets]
    if len(prizes) < 2:
        return 100.0
    penalties = 0.0
    for a, b in zip(prizes, prizes[1:]):
        if b <= 0:
            continue
        ratio = a / b
        if ratio > 3.5:
            penalties += min(40.0, (ratio - 3.5) * 8)
    return max(0.0, 100.0 - penalties)


def _progression_score(structure: PayoutStructure) -> float:
    sizes = [b.size for b in structure.buckets]
    if len(sizes) < 2:
        return 100.0
    inversions = sum(1 for a, b in zip(sizes, sizes[1:]) if b < a)
    return max(0.0, 100.0 - 15.0 * inversions)
