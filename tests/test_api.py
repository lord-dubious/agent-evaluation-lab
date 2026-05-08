from pathlib import Path

from fastapi.testclient import TestClient

from agent_evaluation_lab.config import Settings
from agent_evaluation_lab.main import create_app


def create_client(tmp_path: Path) -> TestClient:
    app = create_app(Settings(database_path=tmp_path / "eval.sqlite3"))
    return TestClient(app)


def test_health(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_summary_uses_seeded_data(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    response = client.get("/api/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["suite_count"] == 3
    assert payload["case_count"] == 9
    assert payload["run_count"] == 4
    assert payload["result_count"] == 12
    assert payload["regressions"] == 3
    assert payload["average_score"] > 0.7


def test_suites_include_cases_and_runs(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    response = client.get("/api/suites")
    assert response.status_code == 200
    suites = response.json()
    assert len(suites) == 3
    support = next(item for item in suites if item["suite"]["id"] == "suite_support_quality")
    assert len(support["cases"]) == 3
    assert len(support["runs"]) == 2


def test_run_detail_includes_results_tools_and_citations(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    response = client.get("/api/runs/run_tool_budget")
    assert response.status_code == 200
    payload = response.json()
    assert payload["run"]["status"] == "regressed"
    assert len(payload["results"]) == 3
    assert len(payload["tool_calls"]) == 3
    assert len(payload["citations"]) == 3
    assert any(result["failure_reason"] for result in payload["results"])


def test_missing_resources_return_404(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    assert client.get("/api/suites/missing").status_code == 404
    assert client.get("/api/runs/missing").status_code == 404


def test_demo_reset_restores_seed_data(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    assert response.json()["run_count"] == 4
