from __future__ import annotations

from payout_engine.core.models import PayoutStructure
from payout_engine.core.normalizer import NormalizedSpec


class ExactOptimizer:
    """Placeholder for a future CP-SAT / IP backend. Not part of the casino MVP."""

    backend = "exact"

    def optimize(self, spec: NormalizedSpec) -> PayoutStructure:
        raise NotImplementedError(
            "Exact integer-program optimizer is intentionally out of MVP scope"
        )
