"""Configuration for the aggregation service (env prefix ``AGG_``)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGG_", extra="ignore")

    # The SQLite database produced by the ingestion service. Gold tables are written
    # back into the same database alongside the raw ``billing_records`` table.
    db_path: str = "./data/finops.db"
