"""Public engine operations: generate, analyze, optimize, recalibrate."""

from __future__ import annotations

import time
from dataclasses import replace

from payout_engine.analysis.existing import (
    describe_issues,
    spec_from_existing,
    structure_from_existing,
)
from payout_engine.core.models import (
    AnalyzeResult,
    ExistingPayoutInput,
    GenerateCandidate,
    GenerateResult,
    MinPrizeMode,
    MinPrizeSpec,
    OptimizeResult,
    RecalibrateRequest,
    Style,
    TopPrizeMode,
    TopPrizeSpec,
    TournamentInput,
    WinnersSpec,
    WinnerMode,
    bucket_table,
)
from payout_engine.core.normalizer import NormalizedSpec, normalize
from payout_engine.core.validation import validate_structure
from payout_engine.optimizers.heuristic import HeuristicOptimizer
from payout_engine.scoring.quality import score_structure
from payout_engine.core.defaults import ENGINE_PROFILE_NAME
from payout_engine.version import ENGINE_VERSION


def generate(data: TournamentInput | dict, *, max_candidates: int = 5) -> GenerateResult:
    inp = data if isinstance(data, TournamentInput) else TournamentInput.model_validate(data)
    started = time.perf_counter()
    spec = normalize(inp)
    optimizer = HeuristicOptimizer()
    structures = optimizer.candidates(spec)
    if not structures:
        structures = [optimizer.optimize(spec)]
    scored: list[GenerateCandidate] = []
    for structure in structures:
        validation = validate_structure(structure, spec)
        quality = score_structure(structure, spec)
        scored.append(
            GenerateCandidate(
                structure=structure,
                quality=quality,
                validation=validation,
                human_table=bucket_table(structure),
            )
        )
    scored.sort(key=lambda c: (c.validation.valid, c.quality.score), reverse=True)
    return GenerateResult(
        engine_version=ENGINE_VERSION,
        profile=ENGINE_PROFILE_NAME,
        normalized=spec.to_public_dict(),
        candidates=scored[:max_candidates],
        runtime_ms=(time.perf_counter() - started) * 1000.0,
    )


def analyze(data: ExistingPayoutInput | dict) -> AnalyzeResult:
    inp = (
        data
        if isinstance(data, ExistingPayoutInput)
        else ExistingPayoutInput.model_validate(data)
    )
    structure = structure_from_existing(inp)
    spec = spec_from_existing(inp, structure)
    validation = validate_structure(structure, spec)
    quality = score_structure(structure, spec)
    return AnalyzeResult(
        engine_version=ENGINE_VERSION,
        validation=validation,
        quality=quality,
        issues=describe_issues(structure, spec),
        inferred=spec.to_public_dict(),
    )


def optimize(data: ExistingPayoutInput | dict) -> OptimizeResult:
    inp = (
        data
        if isinstance(data, ExistingPayoutInput)
        else ExistingPayoutInput.model_validate(data)
    )
    original_structure = structure_from_existing(inp)
    spec = spec_from_existing(inp, original_structure)
    original = GenerateCandidate(
        structure=original_structure,
        quality=score_structure(original_structure, spec),
        validation=validate_structure(original_structure, spec),
        human_table=bucket_table(original_structure),
    )
    tournament = TournamentInput(
        currency=inp.currency,
        prize_pool=spec.prize_pool_cents / 100.0,
        entrants=spec.entrants,
        entry_fee=spec.entry_fee_cents / 100.0,
        winners=WinnersSpec(mode=WinnerMode.COUNT, value=float(spec.winner_count)),
        top_prize=TopPrizeSpec(mode=TopPrizeMode.AUTO),
        minimum_prize=MinPrizeSpec(
            mode=MinPrizeMode.FIXED, value=spec.min_prize_cents / 100.0
        ),
        style=inp.style,
        constraints=inp.constraints,
    )
    generated = generate(tournament)
    best = generated.candidates[0]
    preserved, changed = _diff_buckets(original_structure, best.structure)
    return OptimizeResult(
        engine_version=ENGINE_VERSION,
        original_score=original.quality.score,
        optimized_score=best.quality.score,
        preserved=preserved,
        changed=changed,
        original=original,
        optimized=best,
    )


def recalibrate(data: RecalibrateRequest | dict) -> GenerateResult:
    req = (
        data
        if isinstance(data, RecalibrateRequest)
        else RecalibrateRequest.model_validate(data)
    )
    existing = structure_from_existing(req.existing)
    spec = spec_from_existing(req.existing, existing)
    style = req.style or Style(spec.style)
    winner_pct = 100.0 * spec.winner_count / spec.entrants
    min_multiple = (
        spec.min_prize_cents / spec.entry_fee_cents if spec.entry_fee_cents else None
    )
    tournament = TournamentInput(
        currency=spec.currency,
        prize_pool=req.new_prize_pool,
        entrants=spec.entrants,
        entry_fee=spec.entry_fee_cents / 100.0,
        winners=WinnersSpec(mode=WinnerMode.PERCENTAGE, value=winner_pct),
        top_prize=TopPrizeSpec(mode=TopPrizeMode.AUTO),
        minimum_prize=(
            MinPrizeSpec(mode=MinPrizeMode.ENTRY_MULTIPLE, value=min_multiple)
            if min_multiple
            else MinPrizeSpec(mode=MinPrizeMode.FIXED, value=spec.min_prize_cents / 100.0)
        ),
        style=style,
        constraints=req.existing.constraints,
    )
    return generate(tournament)


def reverse_p1(data: TournamentInput | dict) -> GenerateResult:
    """Search marketing-friendly first prizes; generate() already grids P1 when auto."""
    inp = data if isinstance(data, TournamentInput) else TournamentInput.model_validate(data)
    if inp.top_prize.mode is not TopPrizeMode.AUTO:
        inp = inp.model_copy(
            update={"top_prize": TopPrizeSpec(mode=TopPrizeMode.AUTO)}
        )
    return generate(inp)


def _diff_buckets(old, new) -> tuple[list[str], list[str]]:
    old_map = {(b.start, b.end, b.amount_cents) for b in old.buckets}
    new_map = {(b.start, b.end, b.amount_cents) for b in new.buckets}
    preserved = [f"{s}–{e}" for s, e, _ in sorted(old_map & new_map)]
    changed = []
    for b in new.buckets:
        key = (b.start, b.end, b.amount_cents)
        if key not in old_map:
            changed.append(f"{b.start}–{b.end}")
    return preserved, changed
