"""Heuristic geo benchmarks until ops supplies real sample ladders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GeoProfile:
    id: str
    title: str
    currencies: tuple[str, ...]
    pool_eur_lo: float
    pool_eur_hi: float
    p1_share_lo: float
    p1_share_hi: float
    paid_places_lo: int
    paid_places_hi: int
    preferred_styles: tuple[str, ...]
    advice_default: str
    recipe_hints: tuple[str, ...]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "currencies": list(self.currencies),
            "pool_eur_band": [self.pool_eur_lo, self.pool_eur_hi],
            "p1_share_band": [self.p1_share_lo, self.p1_share_hi],
            "paid_places_band": [self.paid_places_lo, self.paid_places_hi],
            "preferred_styles": list(self.preferred_styles),
            "advice_default": self.advice_default,
            "recipe_hints": list(self.recipe_hints),
        }


GEO_PROFILES: dict[str, GeoProfile] = {
    "tier1_eu": GeoProfile(
        id="tier1_eu",
        title="Tier-1 EU",
        currencies=("EUR", "GBP"),
        pool_eur_lo=5_000,
        pool_eur_hi=250_000,
        p1_share_lo=0.12,
        p1_share_hi=0.18,
        paid_places_lo=12,
        paid_places_hi=100,
        preferred_styles=("balanced", "flat"),
        advice_default="Engage the field is the default for Tier-1 EU dailies.",
        recipe_hints=("daily", "weekly", "flash"),
    ),
    "nordics": GeoProfile(
        id="nordics",
        title="Nordics",
        currencies=("DKK", "NOK", "SEK", "EUR"),
        pool_eur_lo=3_000,
        pool_eur_hi=150_000,
        p1_share_lo=0.06,
        p1_share_hi=0.14,
        paid_places_lo=20,
        paid_places_hi=150,
        preferred_styles=("flat", "balanced"),
        advice_default="Nordic boards often run wider with a flatter top prize.",
        recipe_hints=("weekly", "daily"),
    ),
    "cee": GeoProfile(
        id="cee",
        title="CEE",
        currencies=("CZK", "PLN", "EUR"),
        pool_eur_lo=1_000,
        pool_eur_hi=80_000,
        p1_share_lo=0.14,
        p1_share_hi=0.28,
        paid_places_lo=8,
        paid_places_hi=50,
        preferred_styles=("balanced", "top_heavy"),
        advice_default="CEE races often use tighter paid places and a stronger marketing P1.",
        recipe_hints=("flash", "jackpot", "micro"),
    ),
    "tr": GeoProfile(
        id="tr",
        title="Turkey",
        currencies=("TRY", "EUR", "USD"),
        pool_eur_lo=1_000,
        pool_eur_hi=100_000,
        p1_share_lo=0.18,
        p1_share_hi=0.32,
        paid_places_lo=10,
        paid_places_hi=40,
        preferred_styles=("top_heavy", "balanced"),
        advice_default="TR promos lean on a hero 1st prize and a compact widget.",
        recipe_hints=("jackpot", "daily", "flash"),
    ),
}


def list_geo_profiles() -> list[dict[str, Any]]:
    return [p.to_public_dict() for p in GEO_PROFILES.values()]
