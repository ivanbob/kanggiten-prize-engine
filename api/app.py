"""Thin HTTP adapter. The engine does not import this package."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from payout_engine.core.models import (
    AnalyzeResult,
    ExistingPayoutInput,
    GenerateResult,
    OptimizeResult,
    RecalibrateRequest,
    TournamentInput,
)
from payout_engine.core.normalizer import NormalizationError
from payout_engine.operations import analyze, generate, optimize, recalibrate
from payout_engine.optimizers.heuristic import HeuristicError

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="Casino Payout Engine", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/v1/payouts/generate", response_model=GenerateResult)
def generate_endpoint(body: TournamentInput) -> GenerateResult:
    return _run(lambda: generate(body))


@app.post("/v1/payouts/analyze", response_model=AnalyzeResult)
def analyze_endpoint(body: ExistingPayoutInput) -> AnalyzeResult:
    return _run(lambda: analyze(body))


@app.post("/v1/payouts/optimize", response_model=OptimizeResult)
def optimize_endpoint(body: ExistingPayoutInput) -> OptimizeResult:
    return _run(lambda: optimize(body))


@app.post("/v1/payouts/recalibrate", response_model=GenerateResult)
def recalibrate_endpoint(body: RecalibrateRequest) -> GenerateResult:
    return _run(lambda: recalibrate(body))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


def _run(fn):
    try:
        return fn()
    except (NormalizationError, HeuristicError, ValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
