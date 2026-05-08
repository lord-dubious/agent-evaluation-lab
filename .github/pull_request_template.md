## Summary
- 

## Verification
- [ ] `uv run --extra dev ruff check src tests`
- [ ] `uv run --extra dev ruff format --check src tests`
- [ ] `uv run python -m compileall -q src tests`
- [ ] `uv run --extra dev pytest tests/ --cov=agent_evaluation_lab --cov-report=term-missing`

## Review Notes
- Are evaluation claims clearly marked as deterministic fixture data, not public benchmarks?
- Are failure modes and scoring dimensions visible to reviewers?
- Are screenshots generated from real local runs?
