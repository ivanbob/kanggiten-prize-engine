"""Score how well a ladder fits a geo market profile."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from payout_engine.core.models import PayoutStructure
from payout_engine.geo.profiles import GEO_PROFILES, GeoProfile


class GeoFitRequest(BaseModel):
    geo: str
    currency: str = "EUR"
    prize_pool: float | None = None
    prize_pool_cents: int | None = None
    winner_count: int | None = None
    top_prize_cents: int | None = None
    style: str | None = None
    pool_eur_estimate: float | None = Field(
        default=None,
        description="Pool converted to EUR for geo banding when currency is not EUR.",
    )
    # Optional full structure fields for richer advice
    buckets: list[dict[str, Any]] | None = None


class GeoFitResult(BaseModel):
    geo: str
    geo_title: str
    score: float
    breakdown: dict[str, float]
    advice: list[str]
    preferred_styles: list[str]
    recipe_hints: list[str]


def _band_score(value: float, lo: float, hi: float) -> float:
    if lo <= value <= hi:
        return 100.0
    if value < lo:
        span = max(lo, 1e-9)
        ratio = value / span
        return max(0.0, min(100.0, 100.0 * ratio))
    # above hi
    over = (value - hi) / max(hi, 1e-9)
    return max(0.0, 100.0 - min(100.0, over * 80.0))


def score_geo_fit(req: GeoFitRequest) -> GeoFitResult:
    profile = GEO_PROFILES.get(req.geo)
    if profile is None:
        known = ", ".join(GEO_PROFILES)
        raise ValueError(f"unknown geo {req.geo!r}; expected one of: {known}")

    pool_cents = req.prize_pool_cents
    if pool_cents is None and req.prize_pool is not None:
        pool_cents = int(round(req.prize_pool * 100))
    pool_cents = pool_cents or 0
    pool_major = pool_cents / 100.0

    # Prefer explicit EUR estimate (FX-converted); else assume amount is already EUR-ish for banding
    pool_eur = req.pool_eur_estimate if req.pool_eur_estimate is not None else pool_major

    winners = int(req.winner_count or 0)
    top = int(req.top_prize_cents or 0)
    p1_share = (top / pool_cents) if pool_cents > 0 else 0.0
    style = (req.style or "balanced").lower()

    pool_score = _band_score(pool_eur, profile.pool_eur_lo, profile.pool_eur_hi)
    p1_score = _band_score(p1_share, profile.p1_share_lo, profile.p1_share_hi)
    paid_score = _band_score(float(winners), float(profile.paid_places_lo), float(profile.paid_places_hi))
    currency_score = 100.0 if req.currency.upper() in profile.currencies else 45.0
    style_score = 100.0 if style in profile.preferred_styles else 55.0

    weights = {
        "pool_size": 0.25,
        "p1_share": 0.30,
        "paid_places": 0.20,
        "currency": 0.15,
        "style": 0.10,
    }
    breakdown = {
        "pool_size": round(pool_score, 1),
        "p1_share": round(p1_score, 1),
        "paid_places": round(paid_score, 1),
        "currency": round(currency_score, 1),
        "style": round(style_score, 1),
    }
    score = sum(breakdown[k] * weights[k] for k in weights)

    advice = _advice(profile, req, p1_share, winners, pool_eur, style, currency_score)
    return GeoFitResult(
        geo=profile.id,
        geo_title=profile.title,
        score=round(score, 1),
        breakdown=breakdown,
        advice=advice,
        preferred_styles=list(profile.preferred_styles),
        recipe_hints=list(profile.recipe_hints),
    )


def score_structure_for_geo(
    structure: PayoutStructure,
    geo: str,
    *,
    pool_eur_estimate: float | None = None,
) -> GeoFitResult:
    return score_geo_fit(
        GeoFitRequest(
            geo=geo,
            currency=structure.currency,
            prize_pool_cents=structure.prize_pool_cents,
            winner_count=structure.winner_count,
            top_prize_cents=structure.top_prize_cents,
            style=structure.style,
            pool_eur_estimate=pool_eur_estimate,
        )
    )


def _advice(
    profile: GeoProfile,
    req: GeoFitRequest,
    p1_share: float,
    winners: int,
    pool_eur: float,
    style: str,
    currency_score: float,
) -> list[str]:
    tips: list[str] = []
    if currency_score < 80:
        tips.append(
            f"{req.currency.upper()} is uncommon for {profile.title}; "
            f"typical currencies: {', '.join(profile.currencies)}."
        )
    if p1_share > profile.p1_share_hi:
        tips.append(
            f"P1 at {p1_share:.0%} is high for {profile.title} "
            f"(typical {profile.p1_share_lo:.0%}–{profile.p1_share_hi:.0%}) — try Wide board or Engage the field."
        )
    elif p1_share < profile.p1_share_lo and p1_share > 0:
        tips.append(
            f"P1 at {p1_share:.0%} is soft for {profile.title} — Hero 1st may fit marketing better."
        )
    if winners and winners < profile.paid_places_lo:
        tips.append(
            f"Only {winners} paid places — {profile.title} boards often pay "
            f"{profile.paid_places_lo}–{profile.paid_places_hi}."
        )
    elif winners > profile.paid_places_hi:
        tips.append(
            f"{winners} paid places is wide for {profile.title} "
            f"(typical {profile.paid_places_lo}–{profile.paid_places_hi})."
        )
    if pool_eur < profile.pool_eur_lo * 0.5:
        tips.append(f"Pool looks small vs typical {profile.title} guarantees.")
    elif pool_eur > profile.pool_eur_hi * 1.5:
        tips.append(f"Pool is large vs typical {profile.title} dailies — check weekend/network templates.")
    if style not in profile.preferred_styles:
        preferred = " / ".join(profile.preferred_styles)
        tips.append(f"Preferred styles for {profile.title}: {preferred}.")
    if not tips:
        tips.append(profile.advice_default)
    return tips[:4]
