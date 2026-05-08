.PHONY: test lint format run

lint:
	uv run --extra dev ruff check src tests

format:
	uv run --extra dev ruff format src tests

test:
	uv run --extra dev pytest tests/ --cov=agent_evaluation_lab --cov-report=term-missing

run:
	uv run uvicorn agent_evaluation_lab.main:app --reload
