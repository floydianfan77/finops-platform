"""Configuration for the billing generator.

Settings are read from environment variables (prefixed ``BILLING_`` / ``BROKER_``)
and can be overridden by CLI flags. This keeps local dev, Docker, and CI consistent.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BrokerSettings(BaseSettings):
    """Message-broker settings (used only when sink == 'broker', i.e. step 2)."""

    model_config = SettingsConfigDict(env_prefix="BROKER_", extra="ignore")

    bootstrap_servers: str = "localhost:9092"
    topic: str = "finops.billing.raw"
    client_id: str = "billing-generator"


class Settings(BaseSettings):
    """Top-level generator settings."""

    model_config = SettingsConfigDict(env_prefix="BILLING_", extra="ignore")

    # Output destination: "stdout" | "file" | "broker"
    sink: str = "stdout"

    # Generation cadence
    batch_size: int = Field(default=5, ge=1)
    interval_seconds: float = Field(default=2.0, ge=0)

    # Simulated tenant population
    num_accounts: int = Field(default=8, ge=1)

    # Reproducibility (None => random each run)
    seed: int | None = None

    # File sink target
    file_path: str = "./data/billing.ndjson"

    broker: BrokerSettings = Field(default_factory=BrokerSettings)
