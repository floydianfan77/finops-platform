"""Configuration for the API service (env prefix ``API_``).

Budgets are monthly spend limits (USD). ``budget_total`` is the overall cap;
``budget_by_provider`` caps individual providers. Override via env, e.g.:

    API_DB_PATH=../ingestion-service/data/finops.db
    API_BUDGET_TOTAL=60000
    API_BUDGET_BY_PROVIDER={"AWS": 40000, "Azure": 12000, "GCP": 12000}
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="API_", extra="ignore")

    # The SQLite database written by ingestion (raw) + aggregation (gold tables).
    db_path: str = "./data/finops.db"

    host: str = "127.0.0.1"
    port: int = 8000

    # Budget thresholds (USD). warn_ratio is the fraction of budget that flips a
    # budget from OK to WARN (before it goes OVER at >= 1.0).
    budget_total: float = 60000.0
    budget_by_provider: dict[str, float] = {
        "AWS": 45000.0,
        "Azure": 12000.0,
        "GCP": 12000.0,
    }
    warn_ratio: float = 0.8
