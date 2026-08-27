"""Four-stage casino heuristic (Musco et al. adapted for slot-race widgets)."""

from __future__ import annotations

import math
from dataclasses import replace

from payout_engine.core.curves import InfeasibleCurveError, PowerLawCurve
from payout_engine.core.defaults import PODIUM_SINGLETONS, STYLE_P1_BAND
from payout_engine.core.models import Bucket, PayoutStructure
from payout_engine.core.nice_numbers import NiceNumberGenerator
from payout_engine.core.normalizer import NormalizedSpec


class HeuristicError(RuntimeError):
    """Heuristic could not produce a feasible payout table."""


class HeuristicOptimizer:
    backend = "heuristic"

    def __init__(self, curve: PowerLawCurve | None = None) -> None:
        self.curve = curve or PowerLawCurve()

    def optimize(self, spec: NormalizedSpec) -> PayoutStructure:
        structures = self.candidates(spec)
        if not structures:
            raise HeuristicError("heuristic produced no feasible payout tables")
        return structures[0]

    def candidates(self, spec: NormalizedSpec) -> list[PayoutStructure]:
        nice = NiceNumberGenerator(
            profile=spec.nice_profile,
            custom_majors=list(spec.custom_nice_majors),
            max_cents=max(spec.prize_pool_cents, spec.top_prize_cents, 100),
        )
        results: list[PayoutStructure] = []
        seen: set[tuple] = set()
        for top in _top_prize_grid(spec, nice):
            for max_buckets in _bucket_grid(spec):
                trial = replace(spec, top_prize_cents=top, max_buckets=max_buckets)
                try:
                    structure = self._run(trial, nice)
                except (HeuristicError, InfeasibleCurveError):
                    continue
                key = tuple((b.start, b.end, b.amount_cents) for b in structure.buckets)
                if key in seen:
                    continue
                seen.add(key)
                results.append(structure)
        return results

    def _run(self, spec: NormalizedSpec, nice: NiceNumberGenerator) -> PayoutStructure:
        n = spec.winner_count
        pool = spec.prize_pool_cents
        p1 = spec.top_prize_cents
        e = spec.min_prize_cents
        if n * e > pool:
            raise HeuristicError("minimum prizes exceed the pool")
        if p1 + (n - 1) * e > pool:
            raise HeuristicError("top prize plus minimums exceed the pool")

        ideal, meta = self.curve.payouts(n, pool, p1, e)
        sizes = _initial_bucket_sizes(n, spec.max_buckets)
        sizes, prizes, warnings = _assign_prizes(sizes, ideal, nice, e, p1)
        sizes, prizes, warnings = _repair_bucket_sizes(sizes, prizes, warnings)
        sizes, prizes, warnings = _spend_leftover(
            sizes, prizes, pool, e, nice, p1_locked=spec.top_prize_mode == "fixed",
            warnings=warnings,
        )
        buckets = _to_buckets(sizes, prizes)
        if not buckets:
            raise HeuristicError("empty structure")
        return PayoutStructure(
            buckets=buckets,
            currency=spec.currency,
            prize_pool_cents=pool,
            winner_count=n,
            top_prize_cents=buckets[0].amount_cents,
            min_prize_cents=e,
            style=spec.style,
            nice_profile=spec.nice_profile,
            curve_model="power_law",
            alpha=float(meta.get("alpha", 0.0)),
            backend=self.backend,
            warnings=warnings,
        )


def _top_prize_grid(spec: NormalizedSpec, nice: NiceNumberGenerator) -> list[int]:
    min_top = spec.min_prize_cents if spec.winner_count == 1 else spec.min_prize_cents + 1
    max_top = spec.prize_pool_cents - (spec.winner_count - 1) * spec.min_prize_cents
    if spec.top_prize_mode == "fixed":
        return [spec.top_prize_cents]
    lo_f, hi_f = STYLE_P1_BAND.get(spec.style, (0.12, 0.18))
    pool = spec.prize_pool_cents
    fracs = (lo_f, (lo_f + hi_f) / 2.0, hi_f, spec.top_prize_cents / pool)
    values = {spec.top_prize_cents}
    for frac in fracs:
        values.add(nice.nearest(int(round(pool * frac))))
    out = [v for v in sorted(values) if min_top <= v <= max_top]
    return out or [min(max(spec.top_prize_cents, min_top), max_top)]


def _bucket_grid(spec: NormalizedSpec) -> list[int]:
    r = min(spec.max_buckets, spec.winner_count)
    options = {max(PODIUM_SINGLETONS, min(r, spec.winner_count))}
    options.add(max(6, r - 2) if spec.winner_count >= 6 else r)
    options.add(r)
    return sorted(o for o in options if 1 <= o <= spec.winner_count)


def _solve_beta(remaining: int, terms: int) -> float:
    if terms <= 0:
        return 1.0
    if terms == 1:
        return float(max(remaining, 1))
    lo, hi = 1.0, float(max(remaining, 2))
    for _ in range(70):
        mid = (lo + hi) / 2.0
        total = sum(mid ** i for i in range(1, terms + 1))
        if total < remaining:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _initial_bucket_sizes(n: int, max_buckets: int, podium: int = PODIUM_SINGLETONS) -> list[int]:
    r = min(max_buckets, n)
    podium = min(podium, n, r)
    if n <= r:
        if n <= podium:
            return [1] * n
        sizes = [1] * podium
        rest = n - podium
        leftover_buckets = r - podium
        if leftover_buckets <= 0:
            sizes[-1] += rest
            return sizes
        beta = _solve_beta(rest, leftover_buckets)
        last = 1
        remaining = rest
        while remaining > 0 and len(sizes) < r:
            nxt = max(1, int(math.ceil(beta * last)))
            if len(sizes) == r - 1 or nxt >= remaining:
                sizes.append(remaining)
                remaining = 0
                break
            nxt = min(nxt, remaining - (r - len(sizes) - 1))
            nxt = max(1, nxt)
            sizes.append(nxt)
            remaining -= nxt
            last = nxt
        if remaining:
            sizes[-1] += remaining
        return sizes

    beta = _solve_beta(n - podium, max(1, r - podium))
    for _ in range(50):
        sizes = _grow_sizes(n, r, podium, beta)
        if sizes is not None and len(sizes) <= r and sum(sizes) == n:
            return sizes
        beta *= 1.06
    sizes = _grow_sizes(n, r, podium, beta) or [1] * podium
    drift = n - sum(sizes)
    if drift:
        sizes.append(drift) if drift > 0 else None
        if drift < 0:
            sizes[-1] += drift
    return [s for s in sizes if s > 0]


def _grow_sizes(n: int, r: int, podium: int, beta: float) -> list[int] | None:
    sizes = [1] * podium
    last = 1
    while sum(sizes) < n and len(sizes) < r:
        nxt = max(1, int(math.ceil(beta * last)))
        used = sum(sizes)
        two_step = int(math.ceil(beta * nxt)) + nxt
        if two_step + used > n and nxt + used <= n and len(sizes) + 2 <= r:
            rem = n - used
            a, b = rem // 2, rem - rem // 2
            if a <= 0:
                sizes.append(rem)
            else:
                sizes.extend([a, b] if a <= b else [b, a])
            break
        if nxt + used > n:
            sizes.append(n - used)
            break
        sizes.append(nxt)
        last = nxt
    if sum(sizes) != n:
        extra = n - sum(sizes)
        if extra > 0:
            sizes[-1] += extra
        elif extra < 0:
            return None
    if len(sizes) > r:
        return None
    return sizes


def _assign_prizes(
    sizes: list[int],
    ideal,
    nice: NiceNumberGenerator,
    min_prize: int,
    top_prize: int,
) -> tuple[list[int], list[int], list[str]]:
    prizes: list[int] = []
    leftover = 0.0
    idx = 0
    warnings: list[str] = []
    i = 0
    work = list(sizes)
    while i < len(work):
        sz = work[i]
        chunk = ideal[idx : idx + sz]
        budget = float(chunk.sum()) + leftover
        mean = budget / sz
        if i == 0:
            prize = nice.floor(int(mean)) if sz == 1 else nice.floor(int(mean))
            prize = max(prize, min_prize)
            # Prefer the requested marketing first prize when it is nice.
            if sz == 1 and nice.contains(top_prize):
                prize = min(top_prize, int(mean) if mean >= top_prize else max(prize, nice.floor(top_prize)))
                prize = nice.floor(min(top_prize, max(int(mean), min_prize)))
            prize = max(min(prize, int(mean) if mean >= min_prize else prize), min_prize)
            if sz == 1:
                prize = min(top_prize, max(nice.floor(int(max(mean, min_prize))), min_prize))
                if prize < min_prize:
                    prize = min_prize
        else:
            prize = max(nice.floor(int(mean)), min_prize)
            if prize >= prizes[-1]:
                work[i - 1] += sz
                leftover = budget - prizes[-1] * sz
                work.pop(i)
                idx += sz
                continue
        prizes.append(int(prize))
        leftover = budget - prize * sz
        idx += sz
        i += 1
    return work, prizes, warnings


def _repair_bucket_sizes(
    sizes: list[int], prizes: list[int], warnings: list[str]
) -> tuple[list[int], list[int], list[str]]:
    sizes = list(sizes)
    prizes = list(prizes)
    for t in range(len(sizes) - 1):
        while sizes[t] > sizes[t + 1] and sizes[t] > 1:
            sizes[t] -= 1
            sizes[t + 1] += 1
    merged_sizes: list[int] = []
    merged_prizes: list[int] = []
    for sz, prize in zip(sizes, prizes):
        if merged_prizes and prize == merged_prizes[-1]:
            merged_sizes[-1] += sz
        else:
            merged_sizes.append(sz)
            merged_prizes.append(prize)
    return merged_sizes, merged_prizes, warnings


def _spend_leftover(
    sizes: list[int],
    prizes: list[int],
    pool: int,
    min_prize: int,
    nice: NiceNumberGenerator,
    p1_locked: bool,
    warnings: list[str],
) -> tuple[list[int], list[int], list[str]]:
    sizes = list(sizes)
    prizes = list(prizes)
    paid = sum(s * p for s, p in zip(sizes, prizes))
    leftover = pool - paid
    if leftover < 0:
        sizes, prizes, leftover, warnings = _reduce_overpay(
            sizes, prizes, leftover, min_prize, warnings
        )

    for i in range(1, min(len(prizes), PODIUM_SINGLETONS)):
        if leftover <= 0 or sizes[i] != 1:
            continue
        cap = (prizes[i - 1] + prizes[i]) // 2
        target = min(prizes[i] + leftover, cap)
        bumped = nice.floor(target)
        if bumped > prizes[i]:
            leftover -= (bumped - prizes[i]) * sizes[i]
            prizes[i] = bumped

    # Prefer the next cashier denomination on the last tier when leftover covers it.
    if leftover > 0 and len(prizes) >= 1:
        nxt_nice = nice.ceil(prizes[-1] + 1)
        cost = (nxt_nice - prizes[-1]) * sizes[-1]
        prev = prizes[-2] if len(prizes) > 1 else nxt_nice + leftover + 1
        if 0 < cost <= leftover and nxt_nice < prev:
            leftover -= cost
            prizes[-1] = nxt_nice

    if leftover > 0 and not p1_locked:
        prizes[0] += leftover
        leftover = 0
        snapped = nice.floor(prizes[0])
        extra = prizes[0] - snapped
        if extra > 0 and snapped >= (prizes[1] + extra if len(prizes) > 1 else 0):
            prizes[0] = snapped
            for i in range(1, min(len(prizes), PODIUM_SINGLETONS)):
                if extra <= 0 or sizes[i] != 1:
                    continue
                cap = prizes[i - 1] - 1
                take = min(extra, cap - prizes[i])
                if take <= 0:
                    continue
                prizes[i] += take
                extra -= take
            leftover = extra
        if leftover == 0 and not nice.contains(prizes[0]):
            warnings.append("added leftover cents to 1st prize to hit the pool exactly")
        elif extra == 0 and snapped != prizes[0]:
            pass

    # Last resort when 1st is a locked marketing number: spend cent-by-cent.
    while leftover >= sizes[-1] and leftover > 0:
        nxt = prizes[-1] + 1
        if len(prizes) > 1 and nxt >= prizes[-2]:
            break
        prizes[-1] = nxt
        leftover -= sizes[-1]
        if not nice.contains(nxt):
            msg = "last-tier prize left nice-number profile to spend leftover cents"
            if msg not in warnings:
                warnings.append(msg)

    if leftover > 0 and (
        len(prizes) == 1 or prizes[-1] + 1 < prizes[-2]
    ) and leftover < sizes[-1]:
        last = sizes[-1]
        high = leftover
        low = last - leftover
        old = prizes[-1]
        sizes[-1] = high
        prizes[-1] = old + 1
        sizes.append(low)
        prizes.append(old)
        leftover = 0
        warnings.append("split bottom tier by leftover cents to hit the pool exactly")

    if leftover != 0:
        raise HeuristicError(f"could not reconcile leftover {leftover} cents")

    sizes, prizes, warnings = _repair_bucket_sizes(sizes, prizes, warnings)
    if sum(s * p for s, p in zip(sizes, prizes)) != pool:
        raise HeuristicError("pool changed during leftover spend")
    if any(p < min_prize for p in prizes):
        raise HeuristicError("min prize violated during leftover spend")
    return sizes, prizes, warnings


def _reduce_overpay(
    sizes: list[int],
    prizes: list[int],
    leftover: int,  # negative
    min_prize: int,
    warnings: list[str],
) -> tuple[list[int], list[int], int, list[str]]:
    i = len(prizes) - 1
    while leftover < 0 and i >= 0:
        room = prizes[i] - min_prize
        if room <= 0:
            i -= 1
            continue
        drop = min(room, math.ceil((-leftover) / sizes[i]))
        prizes[i] -= drop
        leftover += drop * sizes[i]
        warnings.append("reduced a lower-tier prize to stay within the pool")
        i -= 1
    if leftover < 0:
        raise HeuristicError("unable to repair over-allocation")
    return sizes, prizes, leftover, warnings


def _to_buckets(sizes: list[int], prizes: list[int]) -> list[Bucket]:
    buckets: list[Bucket] = []
    rank = 1
    for sz, prize in zip(sizes, prizes):
        buckets.append(Bucket(start=rank, end=rank + sz - 1, amount_cents=prize))
        rank += sz
    return buckets
