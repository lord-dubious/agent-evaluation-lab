"""Application factory and CLI entry point."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from agent_evaluation_lab.api import router as api_router
from agent_evaluation_lab.config import Settings
from agent_evaluation_lab.repository import EvaluationRepository
from agent_evaluation_lab.web import ASSET_ROOT
from agent_evaluation_lab.web import router as web_router


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    repository = EvaluationRepository(resolved_settings.database_path)
    repository.ensure_seeded()

    app = FastAPI(
        title="Agent Evaluation Lab",
        version="0.1.0",
        summary="Local-first scoring dashboard for AI agent evaluation fixtures.",
    )
    app.state.repository = repository
    app.mount("/static", StaticFiles(directory=ASSET_ROOT), name="static")
    app.include_router(web_router)
    app.include_router(api_router)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("agent_evaluation_lab.main:app", host="127.0.0.1", port=8020, reload=False)
