"""Ideal payout curves.

The optimizer consumes only a rank → ideal payout mapping. Power-law is the
MVP production curve; exponential and linear decay are available for later
style experiments.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class InfeasibleCurveError(ValueError):
    """Requested first prize / min prize cannot sum to the pool."""


class IdealCurveModel(ABC):
    name: str

    @abstractmethod
    def payouts(
        self,
        winner_count: int,
        prize_pool_cents: int,
        top_prize_cents: int,
        min_prize_cents: int,
    ) -> tuple[np.ndarray, dict]:
        """Return ideal per-rank payouts in cents (float64) plus metadata."""


class PowerLawCurve(IdealCurveModel):
    """π_i = E + (P1 - E) / i^α, with α chosen so the sum equals the pool."""

    name = "power_law"

    def __init__(self, alpha_iterations: int = 80) -> None:
        self.alpha_iterations = alpha_iterations

    def payouts(
        self,
        winner_count: int,
        prize_pool_cents: int,
        top_prize_cents: int,
        min_prize_cents: int,
    ) -> tuple[np.ndarray, dict]:
        n = winner_count
        pool = float(prize_pool_cents)
        p1 = float(top_prize_cents)
        e = float(min_prize_cents)
        if n < 1:
            raise InfeasibleCurveError("winner_count must be >= 1")
        if n == 1:
            if top_prize_cents != prize_pool_cents:
                raise InfeasibleCurveError(
                    "single-winner pool must equal the top prize"
                )
            return np.array([p1], dtype=np.float64), {"alpha": 0.0}

        min_sum = p1 + (n - 1) * e
        max_sum = n * p1
        if min_sum > pool + 1e-6:
            raise InfeasibleCurveError(
                "top prize plus minimums exceeds the prize pool"
            )
        if max_sum + 1e-6 < pool:
            raise InfeasibleCurveError(
                "even a flat top-prize curve cannot consume the prize pool"
            )
        if abs(p1 - e) < 1e-9:
            if abs(n * e - pool) > 1e-3:
                raise InfeasibleCurveError(
                    "flat min-prize curve does not match the prize pool"
                )
            return np.full(n, e, dtype=np.float64), {"alpha": 0.0}

        target_h = (pool - n * e) / (p1 - e)
        ranks = np.arange(1, n + 1, dtype=np.float64)
        lo, hi = 0.0, 80.0
        alpha = 0.0
        for _ in range(self.alpha_iterations):
            alpha = (lo + hi) / 2.0
            harmonic = float(np.sum(np.power(ranks, -alpha)))
            if harmonic > target_h:
                lo = alpha
            else:
                hi = alpha
        payouts = e + (p1 - e) / np.power(ranks, alpha)
        # Tiny numeric drift: scale extras so the float sum matches the pool.
        drift = pool - float(payouts.sum())
        if n > 1 and abs(drift) > 1e-6:
            payouts[1:] += drift / (n - 1)
            payouts[0] = p1
        return payouts, {"alpha": float(alpha), "target_h": target_h}


class ExponentialCurve(IdealCurveModel):
    """π_i ∝ q^{i-1} on the residual pool (top-heavy; not the casino default)."""

    name = "exponential"

    def payouts(
        self,
        winner_count: int,
        prize_pool_cents: int,
        top_prize_cents: int,
        min_prize_cents: int,
    ) -> tuple[np.ndarray, dict]:
        n = winner_count
        residual = prize_pool_cents - n * min_prize_cents
        extra_first = top_prize_cents - min_prize_cents
        if residual < extra_first:
            raise InfeasibleCurveError("exponential curve cannot hit the pool")
        if extra_first <= 0:
            return (
                np.full(n, float(min_prize_cents), dtype=np.float64),
                {"q": 1.0},
            )
        # Geometric extras: extra_i = extra_first * q^{i-1}, sum = residual.
        # Solve sum_{i=0}^{n-1} q^i = residual / extra_first.
        target = residual / extra_first
        lo, hi = 1e-9, 1.0
        q = 0.5
        for _ in range(80):
            q = (lo + hi) / 2.0
            geom = (1 - q**n) / (1 - q) if abs(1 - q) > 1e-12 else n
            if geom > target:
                hi = q
            else:
                lo = q
        extras = extra_first * (q ** np.arange(n, dtype=np.float64))
        payouts = min_prize_cents + extras
        payouts[0] = float(top_prize_cents)
        return payouts, {"q": float(q)}


class LinearDecayCurve(IdealCurveModel):
    name = "linear_decay"

    def payouts(
        self,
        winner_count: int,
        prize_pool_cents: int,
        top_prize_cents: int,
        min_prize_cents: int,
    ) -> tuple[np.ndarray, dict]:
        n = winner_count
        if n == 1:
            return np.array([float(prize_pool_cents)]), {"slope": 0.0}
        ranks = np.arange(n, dtype=np.float64)
        weights = (n - 1 - ranks) / (n - 1)
        extra_first = top_prize_cents - min_prize_cents
        residual = prize_pool_cents - n * min_prize_cents - extra_first
        rest_w = weights[1:]
        rest_sum = float(rest_w.sum()) or 1.0
        extras = np.zeros(n, dtype=np.float64)
        extras[0] = extra_first
        extras[1:] = residual * rest_w / rest_sum
        return min_prize_cents + extras, {"slope": float(extra_first / (n - 1))}


def get_curve(name: str = "power_law") -> IdealCurveModel:
    mapping = {
        PowerLawCurve.name: PowerLawCurve,
        ExponentialCurve.name: ExponentialCurve,
        LinearDecayCurve.name: LinearDecayCurve,
    }
    if name not in mapping:
        raise ValueError(f"unknown curve model: {name}")
    return mapping[name]()
