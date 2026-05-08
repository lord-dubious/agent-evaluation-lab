# Architecture

Agent Evaluation Lab is a local-first FastAPI application backed by SQLite. It avoids external model providers in the base demo so every dashboard, API response, and test run is reproducible.

## Data Flow

```mermaid
flowchart TB
    subgraph Authoring[Evaluation authoring]
        Suites[Suites]
        Cases[Cases with expected answers]
        Rubrics[Dimension rubrics]
    end

    subgraph Persistence[Local persistence]
        Seed[Deterministic demo seed]
        SQLite[(SQLite)]
        Repo[Repository boundary]
    end

    subgraph API[FastAPI API]
        Summary[/summary/]
        SuiteAPI[/suites/]
        RunAPI[/runs/]
        Reset[/demo/reset/]
    end

    subgraph Review[Review surface]
        Dashboard[Dashboard]
        Compare[Run comparison]
        Failures[Failure drilldown]
        Evidence[Tool calls and citations]
    end

    Suites --> Seed
    Cases --> Seed
    Rubrics --> Seed
    Seed --> SQLite
    SQLite --> Repo
    Repo --> Summary
    Repo --> SuiteAPI
    Repo --> RunAPI
    Reset --> Seed
    Summary --> Dashboard
    SuiteAPI --> Compare
    RunAPI --> Failures
    RunAPI --> Evidence

    classDef author fill:#dbeafe,stroke:#2563eb,color:#0f172a
    classDef store fill:#fef3c7,stroke:#b45309,color:#111827
    classDef api fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef ui fill:#f3e8ff,stroke:#9333ea,color:#1f103a
    class Suites,Cases,Rubrics author
    class Seed,SQLite,Repo store
    class Summary,SuiteAPI,RunAPI,Reset api
    class Dashboard,Compare,Failures,Evidence ui
```

## Main Components

- `models.py`: Pydantic models for suites, cases, runs, results, tool calls, citations, and summary rollups.
- `demo_data.py`: deterministic fixture data with fixed timestamps, costs, pass rates, and scoring outcomes.
- `repository.py`: SQLite table creation, seed/reset behavior, query methods, and summary aggregation.
- `api.py`: FastAPI routes for dashboard data and demo reset.
- `web_assets/`: vanilla HTML/CSS/JS dashboard served by the FastAPI app.

## Boundaries

The project intentionally does not call an LLM judge. That keeps the base demo deterministic and honest. A later PR can add optional imports from real trace/eval exports while preserving deterministic fixtures for CI.
