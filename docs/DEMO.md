# Demo Guide

## Run Locally

```bash
uv run --extra dev uvicorn agent_evaluation_lab.main:app --reload --port 8020
```

Then open `http://127.0.0.1:8020`.

## Suggested Walkthrough

1. Show the summary cards: suites, cases, runs, pass rate, latency, and regression count.
2. Select `Support Agent Quality Gate` and compare the baseline prompt against the guarded prompt.
3. Open a failed result and explain the visible scoring dimensions.
4. Select `Tool Planning Regression Pack` and show how tool-use and cost failures are separated from correctness.
5. Open API docs and show that the dashboard is backed by typed local JSON responses.

## Screenshot Honesty

The README screenshot is captured from a real local browser session using the deterministic demo database. It is not a mockup or generated marketing image.
