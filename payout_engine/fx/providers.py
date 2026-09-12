"""FX rate providers with a swappable interface for Kanggiten later."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from payout_engine.core.money import SUPPORTED_CURRENCIES

FRANKFURTER_URL = "https://api.frankfurter.app/latest"


@dataclass(frozen=True)
class FxRates:
    base: str
    rates: dict[str, float]
    as_of: str
    source: str

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "base": self.base,
            "rates": dict(self.rates),
            "as_of": self.as_of,
            "source": self.source,
        }


class FxProvider(ABC):
    @abstractmethod
    def get_rates(self, base: str = "EUR") -> FxRates:
        """Return rates as units of each currency per 1 unit of base."""


class EcbFxProvider(FxProvider):
    """ECB reference rates via Frankfurter (EUR base)."""

    def __init__(self, url: str = FRANKFURTER_URL, timeout_s: float = 8.0) -> None:
        self.url = url
        self.timeout_s = timeout_s

    def get_rates(self, base: str = "EUR") -> FxRates:
        base = base.upper()
        wanted = [c for c in SUPPORTED_CURRENCIES if c != base]
        query = f"{self.url}?from={base}&to={','.join(wanted)}"
        try:
            with urllib.request.urlopen(query, timeout=self.timeout_s) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f"FX fetch failed: {exc}") from exc

        rates_raw = payload.get("rates") or {}
        rates = {base: 1.0}
        for code, value in rates_raw.items():
            try:
                rates[str(code).upper()] = float(value)
            except (TypeError, ValueError):
                continue
        as_of = str(payload.get("date") or datetime.now(timezone.utc).date().isoformat())
        return FxRates(base=base, rates=rates, as_of=as_of, source="ECB")


class KanggitenFxProvider(FxProvider):
    """Placeholder for Kanggiten platform aggregator rates.

    Configure KANGGITEN_FX_URL to enable. Falls back is not automatic —
    callers choose the provider via get_default_provider().
    """

    def __init__(self, url: str | None = None, timeout_s: float = 8.0) -> None:
        self.url = url or os.environ.get("KANGGITEN_FX_URL", "").strip()
        self.timeout_s = timeout_s

    def get_rates(self, base: str = "EUR") -> FxRates:
        if not self.url:
            raise RuntimeError(
                "Kanggiten FX is not configured. Set KANGGITEN_FX_URL or use the ECB provider."
            )
        base = base.upper()
        query = f"{self.url.rstrip('/')}?base={base}"
        try:
            req = urllib.request.Request(query, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f"Kanggiten FX fetch failed: {exc}") from exc

        rates_raw = payload.get("rates") or {}
        rates = {base: 1.0}
        for code, value in rates_raw.items():
            try:
                rates[str(code).upper()] = float(value)
            except (TypeError, ValueError):
                continue
        as_of = str(
            payload.get("as_of")
            or payload.get("date")
            or datetime.now(timezone.utc).isoformat()
        )
        return FxRates(base=base, rates=rates, as_of=as_of, source="Kanggiten")


def get_default_provider() -> FxProvider:
    """Prefer Kanggiten when configured; otherwise ECB/Frankfurter."""
    if os.environ.get("KANGGITEN_FX_URL", "").strip():
        return KanggitenFxProvider()
    return EcbFxProvider()
