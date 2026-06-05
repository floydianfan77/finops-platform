"""Configuration for the ingestion service.

Read from environment variables (prefix ``INGEST_``) and overridable by CLI flags.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from finops_common.topics import RAW_BILLING_TOPIC


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INGEST_", extra="ignore")

    # Broker connection
    bootstrap_servers: str = "localhost:9092"
    topic: str = RAW_BILLING_TOPIC
    group_id: str = "finops-ingestion"

    # Where a brand-new consumer group starts reading: "earliest" or "latest".
    auto_offset_reset: str = "earliest"

    # How long each poll waits for a message, in seconds.
    poll_timeout: float = Field(default=1.0, ge=0)

    # Stop after N messages (None => run until interrupted). Handy for demos/tests.
    max_messages: int | None = None

    # Storage targets
    db_path: str = "./data/finops.db"
    dlq_path: str = "./data/dead_letter.ndjson"
