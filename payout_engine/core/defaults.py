"""Casino-first default optimization profile.

These values are starting points for slot races and other non-poker
operator tournaments. They are not claimed to be universally optimal.
"""

from __future__ import annotations

from typing import Final

ENGINE_PROFILE_NAME: Final = "casino_slot"

DEFAULT_CURRENCY: Final = "EUR"
DEFAULT_STYLE: Final = "balanced"
DEFAULT_NICE_PROFILE: Final = "casino"
DEFAULT_MAX_BUCKETS: Final = 12
DEFAULT_MAX_BUCKETS_CAP: Final = 20
DEFAULT_WINNER_PERCENT: Final = 15.0
DEFAULT_MIN_PRIZE_ENTRY_MULTIPLE: Final = 1.5
PODIUM_SINGLETONS: Final = 3

# Auto first-prize bands as a fraction of the net prize pool.
STYLE_P1_FRACTION: Final[dict[str, float]] = {
    "balanced": 0.15,
    "top_heavy": 0.28,
    "flat": 0.08,
}

STYLE_P1_BAND: Final[dict[str, tuple[float, float]]] = {
    "balanced": (0.12, 0.18),
    "top_heavy": (0.20, 0.35),
    "flat": (0.05, 0.12),
}

# Used only when the caller omits an explicit winner count/percentage.
STYLE_WINNER_PERCENT: Final[dict[str, float]] = {
    "balanced": 15.0,
    "top_heavy": 10.0,
    "flat": 25.0,
}

# Casino quality weights (0–1). Tunable via scoring profile JSON later.
CASINO_QUALITY_WEIGHTS: Final[dict[str, float]] = {
    "nice_numbers": 0.22,
    "compactness": 0.16,
    "marketing_p1": 0.16,
    "midfield": 0.16,
    "curve_fit": 0.12,
    "smoothness": 0.10,
    "bucket_progression": 0.08,
}
