from __future__ import annotations

from typing import Protocol

from payout_engine.core.models import PayoutStructure
from payout_engine.core.normalizer import NormalizedSpec


class PayoutOptimizer(Protocol):
    backend: str

    def optimize(self, spec: NormalizedSpec) -> PayoutStructure:
        ...
