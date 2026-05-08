"""FastAPI routes for the local evaluation lab."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from agent_evaluation_lab.models import DashboardSummary, RunDetail, SuiteDetail
from agent_evaluation_lab.repository import EvaluationRepository

router = APIRouter(prefix="/api", tags=["evaluation-lab"])


def get_repository(request: Request) -> EvaluationRepository:
    return request.app.state.repository


RepositoryDep = Annotated[EvaluationRepository, Depends(get_repository)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/summary", response_model=DashboardSummary)
def summary(repository: RepositoryDep) -> DashboardSummary:
    return repository.summary()


@router.post("/demo/reset", response_model=DashboardSummary)
def reset_demo(repository: RepositoryDep) -> DashboardSummary:
    repository.reset_demo_data()
    return repository.summary()


@router.get("/suites", response_model=list[SuiteDetail])
def suites(repository: RepositoryDep) -> list[SuiteDetail]:
    return [
        detail
        for suite in repository.list_suites()
        if (detail := repository.suite_detail(suite.id))
    ]


@router.get("/suites/{suite_id}", response_model=SuiteDetail)
def suite_detail(suite_id: str, repository: RepositoryDep) -> SuiteDetail:
    detail = repository.suite_detail(suite_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suite not found")
    return detail


@router.get("/runs", response_model=list[RunDetail])
def runs(repository: RepositoryDep) -> list[RunDetail]:
    return [detail for run in repository.list_runs() if (detail := repository.run_detail(run.id))]


@router.get("/runs/{run_id}", response_model=RunDetail)
def run_detail(run_id: str, repository: RepositoryDep) -> RunDetail:
    detail = repository.run_detail(run_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return detail
