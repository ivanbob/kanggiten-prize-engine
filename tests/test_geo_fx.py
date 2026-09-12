from __future__ import annotations

from payout_engine.geo.fit import GeoFitRequest, score_geo_fit
from payout_engine.geo.profiles import GEO_PROFILES, list_geo_profiles
from payout_engine.fx.providers import EcbFxProvider, KanggitenFxProvider, get_default_provider
from payout_engine.core.money import SUPPORTED_CURRENCIES, currency_symbol, format_cents


def test_currency_symbols_cover_operator_list():
    for code in ("EUR", "USD", "GBP", "DKK", "NOK", "SEK", "CZK", "TRY"):
        assert code in SUPPORTED_CURRENCIES
        assert currency_symbol(code)
    assert "€" in format_cents(100000, "EUR")


def test_geo_profiles_list():
    profiles = list_geo_profiles()
    assert {p["id"] for p in profiles} >= {"tier1_eu", "nordics", "cee", "tr"}


def test_geo_fit_balanced_tier1():
    result = score_geo_fit(
        GeoFitRequest(
            geo="tier1_eu",
            currency="EUR",
            prize_pool=50000,
            winner_count=50,
            top_prize_cents=750_000,  # 15% of 50k
            style="balanced",
        )
    )
    assert result.score >= 80
    assert result.geo == "tier1_eu"


def test_geo_fit_high_p1_flags_nordics():
    result = score_geo_fit(
        GeoFitRequest(
            geo="nordics",
            currency="DKK",
            prize_pool=50000,
            winner_count=30,
            top_prize_cents=1_500_000,  # 30%
            style="top_heavy",
        )
    )
    assert result.breakdown["p1_share"] < 70
    assert any("P1" in tip or "p1" in tip.lower() or "high" in tip.lower() for tip in result.advice)


def test_geo_unknown_raises():
    try:
        score_geo_fit(GeoFitRequest(geo="mars", prize_pool=1000, winner_count=10, top_prize_cents=15000))
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "unknown geo" in str(exc)


def test_kanggiten_provider_requires_url():
    provider = KanggitenFxProvider(url="")
    try:
        provider.get_rates()
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "not configured" in str(exc)


def test_default_provider_is_ecb_without_env(monkeypatch):
    monkeypatch.delenv("KANGGITEN_FX_URL", raising=False)
    assert isinstance(get_default_provider(), EcbFxProvider)


def test_geo_profiles_constant():
    assert "tr" in GEO_PROFILES
