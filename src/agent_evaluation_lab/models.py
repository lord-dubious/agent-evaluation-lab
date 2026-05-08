"""Typed API models for evaluation suites, runs, and scoring results."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(UTC)


class RunStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    REGRESSED = "regressed"
    IMPROVED = "improved"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ToolStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class EvaluationSuite(BaseModel):
    id: str
    name: str
    description: str
    domain: str
    created_at: datetime
    tags: list[str] = Field(default_factory=list)


class EvalCase(BaseModel):
    id: str
    suite_id: str
    name: str
    prompt: str
    expected_answer: str
    reference_context: str
    expected_citations: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    difficulty: Difficulty = Difficulty.MEDIUM


class AgentRun(BaseModel):
    id: str
    suite_id: str
    agent_name: str
    model_name: str
    run_label: str
    status: RunStatus
    started_at: datetime
    completed_at: datetime
    total_latency_ms: int = Field(ge=0)
    total_cost_usd: float = Field(ge=0)
    pass_rate: float = Field(ge=0, le=1)
    regression_count: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalResult(BaseModel):
    id: str
    run_id: str
    case_id: str
    agent_answer: str
    correctness_score: float = Field(ge=0, le=1)
    safety_score: float = Field(ge=0, le=1)
    groundedness_score: float = Field(ge=0, le=1)
    citation_score: float = Field(ge=0, le=1)
    tool_use_score: float = Field(ge=0, le=1)
    latency_ms: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    passed: bool
    failure_reason: str | None = None
    created_at: datetime

    @property
    def average_score(self) -> float:
        scores = [
            self.correctness_score,
            self.safety_score,
            self.groundedness_score,
            self.citation_score,
            self.tool_use_score,
        ]
        return round(sum(scores) / len(scores), 3)


class ToolCall(BaseModel):
    id: str
    result_id: str
    tool_name: str
    input_summary: str
    output_summary: str
    latency_ms: int = Field(ge=0)
    status: ToolStatus
    error_message: str | None = None


class Citation(BaseModel):
    id: str
    result_id: str
    source_label: str
    excerpt: str
    matched: bool


class SuiteDetail(BaseModel):
    suite: EvaluationSuite
    cases: list[EvalCase]
    runs: list[AgentRun]


class RunDetail(BaseModel):
    run: AgentRun
    suite: EvaluationSuite
    results: list[EvalResult]
    tool_calls: list[ToolCall]
    citations: list[Citation]


class DashboardSummary(BaseModel):
    suite_count: int
    case_count: int
    run_count: int
    result_count: int
    average_pass_rate: float
    average_score: float
    total_cost_usd: float
    total_latency_ms: int
    regressions: int


class DimensionSummary(BaseModel):
    correctness: float
    safety: float
    groundedness: float
    citations: float
    tool_use: float
