from __future__ import annotations

from payout_engine.geo.fit import GeoFitRequest, score_geo_fit
from payout_engine.geo.profiles import GEO_PROFILES, list_geo_profiles
from payout_engine.fx.providers import (
    EcbFxProvider,
    FxRates,
    KanggitenFxProvider,
    clear_fx_cache,
    get_default_provider,
)
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


def test_ecb_provider_parses_and_caches(monkeypatch):
    clear_fx_cache()
    payload = {
        "amount": 1.0,
        "base": "EUR",
        "date": "2026-09-23",
        "rates": {"USD": 1.1, "TRY": 55.0, "DKK": 7.4},
    }
    calls = {"n": 0}

    def fake_get(url, timeout_s):
        calls["n"] += 1
        return payload

    monkeypatch.setattr("payout_engine.fx.providers._http_get_json", fake_get)
    provider = EcbFxProvider(urls=("https://example.test/latest",), timeout_s=1)
    first = provider.get_rates("EUR")
    assert first.rates["TRY"] == 55.0
    assert first.source == "ECB"
    assert first.stale is False
    second = provider.get_rates("EUR")
    assert calls["n"] == 1  # served from fresh cache
    assert second.rates["TRY"] == 55.0


def test_ecb_provider_serves_stale_on_failure(monkeypatch):
    clear_fx_cache()
    good = {
        "base": "EUR",
        "date": "2026-09-23",
        "rates": {"USD": 1.1, "TRY": 50.0},
    }
    state = {"fail": False}

    def fake_get(url, timeout_s):
        if state["fail"]:
            raise TimeoutError("boom")
        return good

    monkeypatch.setattr("payout_engine.fx.providers._http_get_json", fake_get)
    provider = EcbFxProvider(urls=("https://example.test/latest",), timeout_s=1)
    seeded = provider.get_rates("EUR")
    assert seeded.stale is False

    import payout_engine.fx.providers as fxmod

    with fxmod._cache_lock:
        stored_at, rates = fxmod._rate_cache["EUR"]
        fxmod._rate_cache["EUR"] = (stored_at - fxmod._CACHE_TTL_S - 1, rates)

    state["fail"] = True
    stale = provider.get_rates("EUR")
    assert stale.stale is True
    assert stale.rates["TRY"] == 50.0
    assert isinstance(stale, FxRates)
