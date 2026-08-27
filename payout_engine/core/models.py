"""Pydantic input/output models for the payout engine."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from payout_engine.core.defaults import (
    DEFAULT_CURRENCY,
    DEFAULT_MAX_BUCKETS,
    DEFAULT_NICE_PROFILE,
    DEFAULT_STYLE,
)
from payout_engine.core.money import cents_to_major_float, format_cents


class WinnerMode(str, Enum):
    COUNT = "count"
    PERCENTAGE = "percentage"


class TopPrizeMode(str, Enum):
    AUTO = "auto"
    FIXED = "fixed"
    POOL_PERCENTAGE = "pool_percentage"


class MinPrizeMode(str, Enum):
    FIXED = "fixed"
    ENTRY_MULTIPLE = "entry_multiple"
    PERCENTAGE = "percentage"
    AUTOMATIC = "automatic"


class Style(str, Enum):
    BALANCED = "balanced"
    TOP_HEAVY = "top_heavy"
    FLAT = "flat"


class BucketMonotonicity(str, Enum):
    STRICT = "strict"
    PREFERRED = "preferred"
    DISABLED = "disabled"


class NiceNumberProfile(str, Enum):
    CASINO = "casino"
    STANDARD = "standard"
    CUSTOM = "custom"


class WinnersSpec(BaseModel):
    mode: WinnerMode = WinnerMode.PERCENTAGE
    value: float | None = None


class TopPrizeSpec(BaseModel):
    mode: TopPrizeMode = TopPrizeMode.AUTO
    value: float | None = None


class MinPrizeSpec(BaseModel):
    mode: MinPrizeMode = MinPrizeMode.ENTRY_MULTIPLE
    value: float | None = 1.5


class ConstraintsSpec(BaseModel):
    max_buckets: int = Field(default=DEFAULT_MAX_BUCKETS, ge=1, le=40)
    bucket_size_monotonicity: BucketMonotonicity = BucketMonotonicity.PREFERRED
    nice_number_profile: NiceNumberProfile = NiceNumberProfile.CASINO
    custom_nice_numbers: list[float] = Field(default_factory=list)


class TournamentInput(BaseModel):
    """Operator-facing generate request. Amounts are major currency units."""

    currency: str = DEFAULT_CURRENCY
    prize_pool: float
    entrants: int = Field(ge=1)
    entry_fee: float = Field(ge=0)
    winners: WinnersSpec = Field(default_factory=WinnersSpec)
    top_prize: TopPrizeSpec = Field(default_factory=TopPrizeSpec)
    minimum_prize: MinPrizeSpec = Field(default_factory=MinPrizeSpec)
    style: Style = Style.BALANCED
    constraints: ConstraintsSpec = Field(default_factory=ConstraintsSpec)

    @model_validator(mode="after")
    def _check_pool(self) -> TournamentInput:
        if self.prize_pool <= 0:
            raise ValueError("prize_pool must be positive")
        return self


class Bucket(BaseModel):
    start: int = Field(ge=1)
    end: int = Field(ge=1)
    amount_cents: int = Field(ge=0)

    @model_validator(mode="after")
    def _range(self) -> Bucket:
        if self.end < self.start:
            raise ValueError("bucket end must be >= start")
        return self

    @property
    def size(self) -> int:
        return self.end - self.start + 1

    @property
    def paid_cents(self) -> int:
        return self.size * self.amount_cents


class PayoutStructure(BaseModel):
    buckets: list[Bucket]
    currency: str = DEFAULT_CURRENCY
    prize_pool_cents: int
    winner_count: int
    top_prize_cents: int
    min_prize_cents: int
    style: str = DEFAULT_STYLE
    nice_profile: str = DEFAULT_NICE_PROFILE
    curve_model: str = "power_law"
    alpha: float | None = None
    backend: str = "heuristic"
    warnings: list[str] = Field(default_factory=list)

    def total_paid_cents(self) -> int:
        return sum(b.paid_cents for b in self.buckets)

    def as_rank_amounts(self) -> list[int]:
        amounts: list[int] = []
        for bucket in self.buckets:
            amounts.extend([bucket.amount_cents] * bucket.size)
        return amounts


class ValidationIssue(BaseModel):
    code: str
    message: str
    expected: Any = None
    actual: Any = None


class ValidationResult(BaseModel):
    valid: bool
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)


class QualityBreakdown(BaseModel):
    score: float
    metrics: dict[str, float]


class GenerateCandidate(BaseModel):
    structure: PayoutStructure
    quality: QualityBreakdown
    validation: ValidationResult
    human_table: list[str] = Field(default_factory=list)


class GenerateResult(BaseModel):
    engine_version: str
    profile: str
    normalized: dict[str, Any]
    candidates: list[GenerateCandidate]
    runtime_ms: float


class ExistingPayoutInput(BaseModel):
    currency: str = DEFAULT_CURRENCY
    prize_pool: float | None = None
    entrants: int | None = None
    entry_fee: float = 0
    payouts: list[dict[str, Any]]
    style: Style = Style.BALANCED
    constraints: ConstraintsSpec = Field(default_factory=ConstraintsSpec)


class AnalyzeResult(BaseModel):
    engine_version: str
    validation: ValidationResult
    quality: QualityBreakdown
    issues: list[str]
    inferred: dict[str, Any]


class OptimizeResult(BaseModel):
    engine_version: str
    original_score: float
    optimized_score: float
    preserved: list[str]
    changed: list[str]
    original: GenerateCandidate
    optimized: GenerateCandidate


class RecalibrateRequest(BaseModel):
    existing: ExistingPayoutInput
    new_prize_pool: float
    style: Style | None = None


def bucket_table(structure: PayoutStructure) -> list[str]:
    """Human-readable widget rows."""
    rows: list[str] = []
    for bucket in structure.buckets:
        amount = format_cents(bucket.amount_cents, structure.currency)
        if bucket.start == bucket.end:
            rank = f"{bucket.start}"
        else:
            rank = f"{bucket.start}–{bucket.end}"
        rows.append(f"{rank:<12} {amount}")
    return rows


def structure_public_dict(structure: PayoutStructure) -> dict[str, Any]:
    return {
        "currency": structure.currency,
        "prize_pool": cents_to_major_float(structure.prize_pool_cents),
        "winner_count": structure.winner_count,
        "top_prize": cents_to_major_float(structure.top_prize_cents),
        "min_prize": cents_to_major_float(structure.min_prize_cents),
        "buckets": [
            {
                "from": b.start,
                "to": b.end,
                "amount": cents_to_major_float(b.amount_cents),
            }
            for b in structure.buckets
        ],
        "warnings": structure.warnings,
        "backend": structure.backend,
        "curve_model": structure.curve_model,
        "alpha": structure.alpha,
    }
