"""Typer CLI for casino tournament payouts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from payout_engine.core.models import TournamentInput
from payout_engine.operations import analyze, generate, optimize, recalibrate

app = typer.Typer(no_args_is_help=True, help="Casino slot-race payout engine")


@app.command("generate")
def generate_cmd(
    pool: float = typer.Option(..., help="Net prize pool in major currency units"),
    entrants: int = typer.Option(..., help="Number of participants"),
    winners: Optional[int] = typer.Option(None, help="Paid places (count)"),
    winner_pct: Optional[float] = typer.Option(None, help="Paid places as % of field"),
    style: str = typer.Option("balanced"),
    currency: str = typer.Option("EUR"),
    entry_fee: float = typer.Option(0.0),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    payload: dict = {
        "currency": currency,
        "prize_pool": pool,
        "entrants": entrants,
        "entry_fee": entry_fee,
        "style": style,
    }
    if winners is not None:
        payload["winners"] = {"mode": "count", "value": winners}
    elif winner_pct is not None:
        payload["winners"] = {"mode": "percentage", "value": winner_pct}
    _print_generate(generate(payload), json_out)


@app.command("analyze")
def analyze_cmd(
    payout_json: Path = typer.Argument(..., help="JSON file with existing payouts"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    data = json.loads(payout_json.read_text(encoding="utf-8"))
    result = analyze(data)
    if json_out:
        typer.echo(result.model_dump_json(indent=2))
        return
    typer.echo(f"valid: {result.validation.valid}  score: {result.quality.score}")
    for issue in result.issues:
        typer.echo(f"- {issue}")
    for err in result.validation.errors:
        typer.echo(f"error {err.code}: {err.message}")


@app.command("optimize")
def optimize_cmd(
    payout_json: Path = typer.Argument(...),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    data = json.loads(payout_json.read_text(encoding="utf-8"))
    result = optimize(data)
    if json_out:
        typer.echo(result.model_dump_json(indent=2))
        return
    typer.echo(f"original {result.original_score} -> optimized {result.optimized_score}")
    for row in result.optimized.human_table:
        typer.echo(row)


@app.command("recalibrate")
def recalibrate_cmd(
    payout_json: Path = typer.Argument(...),
    new_pool: float = typer.Option(...),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    existing = json.loads(payout_json.read_text(encoding="utf-8"))
    _print_generate(
        recalibrate({"existing": existing, "new_prize_pool": new_pool}),
        json_out,
    )


@app.command("benchmark")
def benchmark_cmd(spec_json: Path = typer.Argument(..., help="TournamentInput JSON")) -> None:
    from payout_engine.benchmarks.baselines import (
        baseline_geometric,
        baseline_raw_power_law,
        baseline_rounded_power_law,
    )
    from payout_engine.core.normalizer import normalize
    from payout_engine.scoring.quality import score_structure

    inp = TournamentInput.model_validate_json(spec_json.read_text(encoding="utf-8"))
    spec = normalize(inp)
    heuristic = generate(inp).candidates[0]
    rows = [("heuristic", heuristic.quality.score)]
    for name, fn in (
        ("geometric", baseline_geometric),
        ("raw_power_law", baseline_raw_power_law),
        ("rounded_power_law", baseline_rounded_power_law),
    ):
        quality = score_structure(fn(spec), spec)
        rows.append((name, quality.score))
    typer.echo(f"{'backend':<22} {'score':>8}")
    for name, score in rows:
        typer.echo(f"{name:<22} {score:>8.2f}")


def _print_generate(result, json_out: bool) -> None:
    if json_out:
        typer.echo(result.model_dump_json(indent=2))
        return
    best = result.candidates[0]
    typer.echo(
        f"score {best.quality.score}  valid={best.validation.valid}  {best.structure.backend}"
    )
    for row in best.human_table:
        typer.echo(row)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
