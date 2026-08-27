"""Nice-number generators.

A nice number is a cashier/widget denomination, not merely a rounded value.
The default CASINO profile is for slot-race prize tables. STANDARD follows
Musco et al. Definition 2.1 on whole major-currency units.
"""

from __future__ import annotations

from functools import lru_cache

from payout_engine.core.models import NiceNumberProfile


# Major-unit coefficients reused at every power of 10.
_CASINO_COEFFS = (
    1, 2, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100,
    125, 150, 200, 250, 300, 400, 500, 750,
)

# Sub-euro cashier amounts (cents) so flash races can still pay min-cash.
_CASINO_SUB_EURO_CENTS = (1, 2, 5, 10, 20, 25, 50)


class NiceNumberGenerator:
    """Deterministic floor/ceil lookup over a profiled denomination set."""

    def __init__(
        self,
        profile: NiceNumberProfile | str = NiceNumberProfile.CASINO,
        custom_majors: list[float] | None = None,
        max_cents: int = 10**12,
    ) -> None:
        self.profile = NiceNumberProfile(profile)
        self.custom_majors = custom_majors or []
        self.max_cents = max_cents
        self._values = self._build(max_cents)

    def _build(self, max_cents: int) -> tuple[int, ...]:
        values: set[int] = {0}
        if self.profile is NiceNumberProfile.CUSTOM:
            for major in self.custom_majors:
                cents = int(round(float(major) * 100))
                if 0 < cents <= max_cents:
                    values.add(cents)
        elif self.profile is NiceNumberProfile.CASINO:
            values.update(_CASINO_SUB_EURO_CENTS)
            k = 0
            while True:
                scale = 10 ** k
                added = False
                for coeff in _CASINO_COEFFS:
                    cents = coeff * scale * 100
                    if cents <= max_cents:
                        values.add(cents)
                        added = True
                if not added:
                    break
                k += 1
                if k > 12:
                    break
        else:
            values.update(_CASINO_SUB_EURO_CENTS)
            values.update(_standard_major_cents(max_cents))
        return tuple(sorted(values))

    def floor(self, amount_cents: int) -> int:
        """Largest nice number <= amount_cents (0 if none)."""
        if amount_cents <= 0:
            return 0
        vals = self._values
        lo, hi = 0, len(vals) - 1
        best = 0
        while lo <= hi:
            mid = (lo + hi) // 2
            if vals[mid] <= amount_cents:
                best = vals[mid]
                lo = mid + 1
            else:
                hi = mid - 1
        return best

    def ceil(self, amount_cents: int) -> int:
        """Smallest nice number >= amount_cents, or the amount itself if above the table."""
        if amount_cents <= 0:
            return 0
        vals = self._values
        lo, hi = 0, len(vals) - 1
        best = None
        while lo <= hi:
            mid = (lo + hi) // 2
            if vals[mid] >= amount_cents:
                best = vals[mid]
                hi = mid - 1
            else:
                lo = mid + 1
        return best if best is not None else amount_cents

    def nearest(self, amount_cents: int) -> int:
        down = self.floor(amount_cents)
        up = self.ceil(amount_cents)
        if abs(up - amount_cents) < abs(amount_cents - down):
            return up
        return down

    def contains(self, amount_cents: int) -> bool:
        if amount_cents == 0:
            return True
        return self.floor(amount_cents) == amount_cents

    def between(self, low_cents: int, high_cents: int) -> list[int]:
        return [v for v in self._values if low_cents <= v <= high_cents]


def _standard_major_cents(max_cents: int) -> set[int]:
    """Musco Definition 2.1 applied to whole major-currency units, in cents."""
    values: set[int] = set()
    max_major = max(1, max_cents // 100)
    k = 0
    while True:
        scale = 10 ** k
        if scale > max_major:
            break
        for a in range(1, 1001):
            if a >= 10 and a % 5 != 0:
                continue
            if a >= 100 and a % 25 != 0:
                continue
            if a >= 250 and a % 50 != 0:
                continue
            major = a * scale
            cents = major * 100
            if cents <= max_cents:
                values.add(cents)
        k += 1
        if k > 12:
            break
    return values


@lru_cache(maxsize=16)
def default_generator(profile: str, max_cents: int) -> NiceNumberGenerator:
    return NiceNumberGenerator(profile=profile, max_cents=max_cents)
