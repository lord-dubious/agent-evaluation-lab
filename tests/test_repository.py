from pathlib import Path

from agent_evaluation_lab.repository import EvaluationRepository


def test_seed_is_idempotent(tmp_path: Path) -> None:
    repository = EvaluationRepository(tmp_path / "eval.sqlite3")
    repository.ensure_seeded()
    repository.ensure_seeded()

    assert len(repository.list_suites()) == 3
    assert len(repository.list_runs()) == 4
    assert repository.summary().result_count == 12


def test_suite_detail_uses_suite_boundary(tmp_path: Path) -> None:
    repository = EvaluationRepository(tmp_path / "eval.sqlite3")
    detail = repository.suite_detail("suite_support_quality")

    assert detail is not None
    assert {case.suite_id for case in detail.cases} == {"suite_support_quality"}
    assert {run.suite_id for run in detail.runs} == {"suite_support_quality"}


def test_run_detail_loads_related_rows(tmp_path: Path) -> None:
    repository = EvaluationRepository(tmp_path / "eval.sqlite3")
    detail = repository.run_detail("run_support_baseline")

    assert detail is not None
    assert detail.suite.id == "suite_support_quality"
    assert len(detail.results) == 3
    assert len(detail.tool_calls) == 3
    assert len(detail.citations) == 3
