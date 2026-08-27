from __future__ import annotations

from payout_engine.operations import analyze, generate, optimize, recalibrate


def _flash_input() -> dict:
    return {
        "currency": "EUR",
        "prize_pool": 5000,
        "entrants": 80,
        "entry_fee": 50,
        "winners": {"mode": "count", "value": 12},
        "style": "balanced",
    }


def test_flash_race_exact_pool_and_monotone():
    result = generate(_flash_input())
    best = result.candidates[0]
    assert best.validation.valid
    struct = best.structure
    assert struct.total_paid_cents() == 5000 * 100
    amounts = struct.as_rank_amounts()
    assert amounts == sorted(amounts, reverse=True)
    assert amounts[-1] >= struct.min_prize_cents
    assert len(struct.buckets) <= 12


def test_daily_slot_race_valid():
    result = generate(
        {
            "currency": "EUR",
            "prize_pool": 50000,
            "entrants": 2000,
            "entry_fee": 25,
            "winners": {"mode": "percentage", "value": 15},
            "style": "balanced",
        }
    )
    best = result.candidates[0]
    assert best.validation.valid
    assert best.structure.winner_count == 300
    assert best.structure.total_paid_cents() == 5_000_000


def test_determinism():
    payload = _flash_input()
    a = generate(payload).model_dump()
    b = generate(payload).model_dump()
    a.pop("runtime_ms")
    b.pop("runtime_ms")
    assert a == b


def test_analyze_existing_table():
    result = analyze(
        {
            "currency": "EUR",
            "prize_pool": 10000,
            "entrants": 100,
            "entry_fee": 100,
            "payouts": [
                {"from": 1, "to": 1, "amount": 2500},
                {"from": 2, "to": 2, "amount": 1500},
                {"from": 3, "to": 3, "amount": 1000},
                {"from": 4, "to": 5, "amount": 750},
                {"from": 6, "to": 10, "amount": 400},
                {"from": 11, "to": 20, "amount": 175},
            ],
        }
    )
    assert result.quality.score >= 0
    assert result.inferred["winner_count"] == 20


def test_recalibrate_grows_pool():
    existing = {
        "currency": "EUR",
        "prize_pool": 10000,
        "entrants": 100,
        "entry_fee": 100,
        "payouts": [
            {"from": 1, "to": 1, "amount": 2500},
            {"from": 2, "to": 2, "amount": 1500},
            {"from": 3, "to": 3, "amount": 1000},
            {"from": 4, "to": 10, "amount": 500},
            {"from": 11, "to": 20, "amount": 250},
        ],
    }
    result = recalibrate({"existing": existing, "new_prize_pool": 25000})
    best = result.candidates[0]
    assert best.validation.valid
    assert best.structure.prize_pool_cents == 2_500_000


def test_optimize_returns_candidate():
    result = optimize(
        {
            "currency": "EUR",
            "prize_pool": 10000,
            "entrants": 100,
            "entry_fee": 100,
            "payouts": [
                {"from": 1, "to": 1, "amount": 2500},
                {"from": 2, "to": 2, "amount": 1500},
                {"from": 3, "to": 3, "amount": 1000},
                {"from": 4, "to": 10, "amount": 500},
                {"from": 11, "to": 20, "amount": 250},
            ],
        }
    )
    assert result.optimized.structure.total_paid_cents() == 1_000_000


def test_nice_numbers_casino_floor():
    from payout_engine.core.nice_numbers import NiceNumberGenerator

    gen = NiceNumberGenerator(profile="casino", max_cents=10_000_000)
    assert gen.floor(10_100) == 10_000  # €101 -> €100
    assert gen.contains(25_000)  # €250
    assert not gen.contains(10_100)


def test_flat_few_winners_auto_lifts_top_prize():
    """Flat auto P1 is ~8%; with 12 places that cannot consume a large pool.

    Auto mode must lift first prize just enough so the pool is feasible.
    """
    result = generate(
        {
            "currency": "EUR",
            "prize_pool": 500_000,
            "entrants": 12,
            "entry_fee": 0,
            "winners": {"mode": "count", "value": 12},
            "style": "flat",
            "minimum_prize": {"mode": "fixed", "value": 1},
            "constraints": {"max_buckets": 10, "nice_number_profile": "casino"},
        }
    )
    best = result.candidates[0]
    assert best.validation.valid
    assert best.structure.total_paid_cents() == 500_000 * 100
    assert best.structure.top_prize_cents * 12 >= 500_000 * 100


def test_impossible_constraints_raise():
    import pytest
    from payout_engine.core.normalizer import NormalizationError

    with pytest.raises(NormalizationError):
        generate(
            {
                "prize_pool": 100,
                "entrants": 50,
                "entry_fee": 1,
                "winners": {"mode": "count", "value": 40},
                "minimum_prize": {"mode": "fixed", "value": 10},
                "top_prize": {"mode": "fixed", "value": 50},
            }
        )
