"""FX rate providers with a swappable interface for Kanggiten later."""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from payout_engine.core.money import SUPPORTED_CURRENCIES

# Prefer current host; keep legacy as fallback (Railway / DNS quirks).
FRANKFURTER_URLS = (
    "https://api.frankfurter.dev/v1/latest",
    "https://api.frankfurter.app/latest",
)

# Soft cache: serve last good rates if live fetch fails (ECB is daily anyway).
_CACHE_TTL_S = 12 * 60 * 60
_cache_lock = threading.Lock()
_rate_cache: dict[str, tuple[float, "FxRates"]] = {}


@dataclass(frozen=True)
class FxRates:
    base: str
    rates: dict[str, float]
    as_of: str
    source: str
    stale: bool = False
    fetched_at: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "base": self.base,
            "rates": dict(self.rates),
            "as_of": self.as_of,
            "source": self.source,
            "stale": self.stale,
        }
        if self.fetched_at:
            out["fetched_at"] = self.fetched_at
        return out


class FxProvider(ABC):
    @abstractmethod
    def get_rates(self, base: str = "EUR") -> FxRates:
        """Return rates as units of each currency per 1 unit of base."""


def _cache_get(base: str) -> FxRates | None:
    with _cache_lock:
        hit = _rate_cache.get(base)
        if not hit:
            return None
        _, rates = hit
        return rates


def _cache_put(base: str, rates: FxRates) -> None:
    with _cache_lock:
        _rate_cache[base] = (time.time(), rates)


def _cache_get_fresh(base: str, ttl_s: float = _CACHE_TTL_S) -> FxRates | None:
    with _cache_lock:
        hit = _rate_cache.get(base)
        if not hit:
            return None
        stored_at, rates = hit
        if time.time() - stored_at > ttl_s:
            return None
        return rates


def _http_get_json(url: str, timeout_s: float) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "KanggitenPrizeEngine/1.0 (+https://kanggiten.com)",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


class EcbFxProvider(FxProvider):
    """ECB reference rates via Frankfurter (EUR base)."""

    def __init__(
        self,
        urls: tuple[str, ...] = FRANKFURTER_URLS,
        timeout_s: float = 6.0,
    ) -> None:
        self.urls = urls
        self.timeout_s = timeout_s

    def get_rates(self, base: str = "EUR") -> FxRates:
        base = base.upper()
        fresh = _cache_get_fresh(base)
        if fresh is not None and not fresh.stale:
            return fresh

        wanted = [c for c in SUPPORTED_CURRENCIES if c != base]
        to_param = ",".join(wanted)
        errors: list[str] = []

        for url in self.urls:
            query = f"{url}?from={base}&to={to_param}"
            try:
                payload = _http_get_json(query, self.timeout_s)
                rates = self._parse_payload(base, payload)
                _cache_put(base, rates)
                return rates
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError) as exc:
                errors.append(f"{url}: {exc}")
                continue

        cached = _cache_get(base)
        if cached is not None:
            return FxRates(
                base=cached.base,
                rates=dict(cached.rates),
                as_of=cached.as_of,
                source=cached.source,
                stale=True,
                fetched_at=cached.fetched_at,
            )

        raise RuntimeError("FX fetch failed: " + " | ".join(errors))

    def _parse_payload(self, base: str, payload: dict[str, Any]) -> FxRates:
        rates_raw = payload.get("rates") or {}
        rates = {base: 1.0}
        for code, value in rates_raw.items():
            try:
                rates[str(code).upper()] = float(value)
            except (TypeError, ValueError):
                continue
        as_of = str(payload.get("date") or datetime.now(timezone.utc).date().isoformat())
        fetched_at = datetime.now(timezone.utc).isoformat()
        return FxRates(
            base=base,
            rates=rates,
            as_of=as_of,
            source="ECB",
            stale=False,
            fetched_at=fetched_at,
        )


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
            payload = _http_get_json(query, self.timeout_s)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError) as exc:
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
        return FxRates(
            base=base,
            rates=rates,
            as_of=as_of,
            source="Kanggiten",
            stale=False,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )


def get_default_provider() -> FxProvider:
    """Prefer Kanggiten when configured; otherwise ECB/Frankfurter."""
    if os.environ.get("KANGGITEN_FX_URL", "").strip():
        return KanggitenFxProvider()
    return EcbFxProvider()


def clear_fx_cache() -> None:
    """Test helper."""
    with _cache_lock:
        _rate_cache.clear()
