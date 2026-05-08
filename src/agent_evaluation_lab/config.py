"""Runtime configuration for Agent Evaluation Lab."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    database_path: Path = Path("agent_eval_demo.sqlite3")

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            database_path=Path(os.getenv("EVAL_LAB_DATABASE_PATH", "agent_eval_demo.sqlite3"))
        )
