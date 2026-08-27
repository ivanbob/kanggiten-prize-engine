"""Hard-constraint validator with structured error codes."""

from __future__ import annotations

from payout_engine.core.models import (
    BucketMonotonicity,
    PayoutStructure,
    ValidationIssue,
    ValidationResult,
)
from payout_engine.core.nice_numbers import NiceNumberGenerator
from payout_engine.core.normalizer import NormalizedSpec


def validate_structure(
    structure: PayoutStructure,
    spec: NormalizedSpec | None = None,
    *,
    require_nice: bool = False,
) -> ValidationResult:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    buckets = structure.buckets

    if not buckets:
        errors.append(
            ValidationIssue(code="EMPTY_STRUCTURE", message="no payout buckets")
        )
        return ValidationResult(valid=False, errors=errors)

    if buckets[0].start != 1:
        errors.append(
            ValidationIssue(
                code="RANK_GAP",
                message="ranks must start at 1",
                expected=1,
                actual=buckets[0].start,
            )
        )

    expected_start = 1
    prev_amount: int | None = None
    prev_size = 0
    monotonicity = (
        spec.bucket_size_monotonicity
        if spec is not None
        else BucketMonotonicity.PREFERRED.value
    )

    for i, bucket in enumerate(buckets):
        if bucket.start != expected_start:
            code = "RANK_GAP" if bucket.start > expected_start else "RANK_OVERLAP"
            errors.append(
                ValidationIssue(
                    code=code,
                    message=f"bucket {i} is not consecutive",
                    expected=expected_start,
                    actual=bucket.start,
                )
            )
        if prev_amount is not None and bucket.amount_cents > prev_amount:
            errors.append(
                ValidationIssue(
                    code="NON_MONOTONE_PRIZE",
                    message="a lower rank receives a higher prize",
                    expected=prev_amount,
                    actual=bucket.amount_cents,
                )
            )
        if i > 0 and bucket.size < prev_size:
            issue = ValidationIssue(
                code="BUCKET_SIZE_NON_MONOTONE",
                message="bucket sizes should not shrink toward lower ranks",
                expected=f">={prev_size}",
                actual=bucket.size,
            )
            if monotonicity == BucketMonotonicity.STRICT.value:
                errors.append(issue)
            elif monotonicity != BucketMonotonicity.DISABLED.value:
                warnings.append(issue)
        expected_start = bucket.end + 1
        prev_amount = bucket.amount_cents
        prev_size = bucket.size

    covered = buckets[-1].end
    if covered != structure.winner_count:
        errors.append(
            ValidationIssue(
                code="WINNER_COUNT_MISMATCH",
                message="structure winner_count does not match covered ranks",
                expected=structure.winner_count,
                actual=covered,
            )
        )
    if spec is not None and covered != spec.winner_count:
        errors.append(
            ValidationIssue(
                code="WINNER_COUNT",
                message="paid places do not match the requested winner count",
                expected=spec.winner_count,
                actual=covered,
            )
        )

    paid = structure.total_paid_cents()
    if paid != structure.prize_pool_cents:
        errors.append(
            ValidationIssue(
                code="POOL_MISMATCH",
                message="payouts do not consume the prize pool exactly",
                expected=structure.prize_pool_cents,
                actual=paid,
            )
        )
    if spec is not None and paid != spec.prize_pool_cents:
        errors.append(
            ValidationIssue(
                code="POOL_MISMATCH",
                message="payouts do not match the requested prize pool",
                expected=spec.prize_pool_cents,
                actual=paid,
            )
        )

    min_prize = spec.min_prize_cents if spec is not None else structure.min_prize_cents
    lowest = buckets[-1].amount_cents
    if lowest < min_prize:
        errors.append(
            ValidationIssue(
                code="MIN_PRIZE",
                message="lowest prize is below the minimum",
                expected=min_prize,
                actual=lowest,
            )
        )

    max_buckets = spec.max_buckets if spec is not None else 40
    if len(buckets) > max_buckets:
        errors.append(
            ValidationIssue(
                code="MAX_BUCKETS",
                message="too many payout tiers for a casino widget",
                expected=max_buckets,
                actual=len(buckets),
            )
        )

    if spec is not None:
        nice = NiceNumberGenerator(
            profile=spec.nice_profile,
            custom_majors=list(spec.custom_nice_majors),
            max_cents=max(structure.prize_pool_cents, 100),
        )
        for bucket in buckets:
            if not nice.contains(bucket.amount_cents):
                issue = ValidationIssue(
                    code="NON_NICE_NUMBER",
                    message="prize is not a cashier-friendly denomination",
                    actual=bucket.amount_cents,
                )
                if require_nice:
                    errors.append(issue)
                else:
                    warnings.append(issue)

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)
