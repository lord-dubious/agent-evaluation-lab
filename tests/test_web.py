from pathlib import Path

from fastapi.testclient import TestClient

from agent_evaluation_lab.config import Settings
from agent_evaluation_lab.main import create_app


def create_client(tmp_path: Path) -> TestClient:
    app = create_app(Settings(database_path=tmp_path / "eval.sqlite3"))
    return TestClient(app)


def test_dashboard_shell_renders(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert "Agent Evaluation Lab" in response.text
    assert "metrics-grid" in response.text
    assert "/static/app.js" in response.text


def test_static_assets_are_served(tmp_path: Path) -> None:
    client = create_client(tmp_path)
    css = client.get("/static/styles.css")
    js = client.get("/static/app.js")

    assert css.status_code == 200
    assert js.status_code == 200
    assert "signal-ring" in css.text
    assert "loadDashboard" in js.text
