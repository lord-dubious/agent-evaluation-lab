"""SQLite repository for deterministic evaluation lab data."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from agent_evaluation_lab import demo_data
from agent_evaluation_lab.models import (
    AgentRun,
    Citation,
    DashboardSummary,
    EvalCase,
    EvalResult,
    EvaluationSuite,
    RunDetail,
    SuiteDetail,
    ToolCall,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


class EvaluationRepository:
    """Small SQLite repository with deterministic seed data."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS suites (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cases (
                    id TEXT PRIMARY KEY,
                    suite_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    suite_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS results (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    case_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id TEXT PRIMARY KEY,
                    result_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS citations (
                    id TEXT PRIMARY KEY,
                    result_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                """
            )

    def reset_demo_data(self) -> None:
        self.initialize()
        with self.connect() as connection:
            for table in ["citations", "tool_calls", "results", "runs", "cases", "suites"]:
                connection.execute(f"DELETE FROM {table}")
            self._insert_many(connection, "suites", demo_data.demo_suites())
            self._insert_many(connection, "cases", demo_data.demo_cases())
            self._insert_many(connection, "runs", demo_data.demo_runs())
            self._insert_many(connection, "results", demo_data.demo_results())
            self._insert_many(connection, "tool_calls", demo_data.demo_tool_calls())
            self._insert_many(connection, "citations", demo_data.demo_citations())

    def ensure_seeded(self) -> None:
        self.initialize()
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM suites").fetchone()
            if row and row["count"] == 0:
                self.reset_demo_data()

    def list_suites(self) -> list[EvaluationSuite]:
        self.ensure_seeded()
        with self.connect() as connection:
            rows = connection.execute("SELECT payload FROM suites ORDER BY id").fetchall()
        return [self._load_model(EvaluationSuite, row["payload"]) for row in rows]

    def get_suite(self, suite_id: str) -> EvaluationSuite | None:
        self.ensure_seeded()
        with self.connect() as connection:
            row = connection.execute(
                "SELECT payload FROM suites WHERE id = ?", (suite_id,)
            ).fetchone()
        return self._load_model(EvaluationSuite, row["payload"]) if row else None

    def suite_detail(self, suite_id: str) -> SuiteDetail | None:
        suite = self.get_suite(suite_id)
        if suite is None:
            return None
        return SuiteDetail(
            suite=suite,
            cases=self.cases_for_suite(suite_id),
            runs=self.runs_for_suite(suite_id),
        )

    def cases_for_suite(self, suite_id: str) -> list[EvalCase]:
        self.ensure_seeded()
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM cases WHERE suite_id = ? ORDER BY id", (suite_id,)
            ).fetchall()
        return [self._load_model(EvalCase, row["payload"]) for row in rows]

    def list_runs(self) -> list[AgentRun]:
        self.ensure_seeded()
        with self.connect() as connection:
            rows = connection.execute("SELECT payload FROM runs ORDER BY id").fetchall()
        return [self._load_model(AgentRun, row["payload"]) for row in rows]

    def runs_for_suite(self, suite_id: str) -> list[AgentRun]:
        self.ensure_seeded()
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM runs WHERE suite_id = ? ORDER BY id", (suite_id,)
            ).fetchall()
        return [self._load_model(AgentRun, row["payload"]) for row in rows]

    def get_run(self, run_id: str) -> AgentRun | None:
        self.ensure_seeded()
        with self.connect() as connection:
            row = connection.execute("SELECT payload FROM runs WHERE id = ?", (run_id,)).fetchone()
        return self._load_model(AgentRun, row["payload"]) if row else None

    def run_detail(self, run_id: str) -> RunDetail | None:
        run = self.get_run(run_id)
        if run is None:
            return None
        suite = self.get_suite(run.suite_id)
        if suite is None:
            return None
        return RunDetail(
            run=run,
            suite=suite,
            results=self.results_for_run(run_id),
            tool_calls=self.tool_calls_for_run(run_id),
            citations=self.citations_for_run(run_id),
        )

    def results_for_run(self, run_id: str) -> list[EvalResult]:
        self.ensure_seeded()
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM results WHERE run_id = ? ORDER BY id", (run_id,)
            ).fetchall()
        return [self._load_model(EvalResult, row["payload"]) for row in rows]

    def tool_calls_for_run(self, run_id: str) -> list[ToolCall]:
        result_ids = [result.id for result in self.results_for_run(run_id)]
        if not result_ids:
            return []
        placeholders = ",".join("?" for _ in result_ids)
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT payload FROM tool_calls WHERE result_id IN ({placeholders}) ORDER BY id",
                result_ids,
            ).fetchall()
        return [self._load_model(ToolCall, row["payload"]) for row in rows]

    def citations_for_run(self, run_id: str) -> list[Citation]:
        result_ids = [result.id for result in self.results_for_run(run_id)]
        if not result_ids:
            return []
        placeholders = ",".join("?" for _ in result_ids)
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT payload FROM citations WHERE result_id IN ({placeholders}) ORDER BY id",
                result_ids,
            ).fetchall()
        return [self._load_model(Citation, row["payload"]) for row in rows]

    def summary(self) -> DashboardSummary:
        self.ensure_seeded()
        runs = self.list_runs()
        results = self._all_results()
        suite_count = len(self.list_suites())
        case_count = len(self._all_cases())
        average_pass_rate = round(sum(run.pass_rate for run in runs) / len(runs), 3) if runs else 0
        average_score = (
            round(sum(result.average_score for result in results) / len(results), 3)
            if results
            else 0
        )
        return DashboardSummary(
            suite_count=suite_count,
            case_count=case_count,
            run_count=len(runs),
            result_count=len(results),
            average_pass_rate=average_pass_rate,
            average_score=average_score,
            total_cost_usd=round(sum(run.total_cost_usd for run in runs), 4),
            total_latency_ms=sum(run.total_latency_ms for run in runs),
            regressions=sum(run.regression_count for run in runs),
        )

    def _all_cases(self) -> list[EvalCase]:
        self.ensure_seeded()
        with self.connect() as connection:
            rows = connection.execute("SELECT payload FROM cases ORDER BY id").fetchall()
        return [self._load_model(EvalCase, row["payload"]) for row in rows]

    def _all_results(self) -> list[EvalResult]:
        self.ensure_seeded()
        with self.connect() as connection:
            rows = connection.execute("SELECT payload FROM results ORDER BY id").fetchall()
        return [self._load_model(EvalResult, row["payload"]) for row in rows]

    def _insert_many(self, connection: sqlite3.Connection, table: str, rows: Iterable[Any]) -> None:
        for row in rows:
            payload = row.model_dump_json()
            if table == "cases":
                connection.execute(
                    "INSERT INTO cases (id, suite_id, payload) VALUES (?, ?, ?)",
                    (row.id, row.suite_id, payload),
                )
            elif table == "runs":
                connection.execute(
                    "INSERT INTO runs (id, suite_id, payload) VALUES (?, ?, ?)",
                    (row.id, row.suite_id, payload),
                )
            elif table == "results":
                connection.execute(
                    "INSERT INTO results (id, run_id, case_id, payload) VALUES (?, ?, ?, ?)",
                    (row.id, row.run_id, row.case_id, payload),
                )
            elif table == "tool_calls":
                connection.execute(
                    "INSERT INTO tool_calls (id, result_id, payload) VALUES (?, ?, ?)",
                    (row.id, row.result_id, payload),
                )
            elif table == "citations":
                connection.execute(
                    "INSERT INTO citations (id, result_id, payload) VALUES (?, ?, ?)",
                    (row.id, row.result_id, payload),
                )
            else:
                connection.execute(
                    "INSERT INTO suites (id, payload) VALUES (?, ?)",
                    (row.id, payload),
                )

    @staticmethod
    def _load_model(model_type: type[ModelT], payload: str) -> ModelT:
        data = json.loads(payload)
        return model_type.model_validate(data)
