"""SQLite store: lands validated billing records into a queryable SQL table."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from finops_common.models import FocusBillingRecord

from ingestion_service.storage.base import Store

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS billing_records (
    record_id            TEXT PRIMARY KEY,
    provider_name        TEXT,
    billing_account_id   TEXT,
    billing_account_name TEXT,
    service_name         TEXT,
    service_category     TEXT,
    charge_category      TEXT,
    region_id            TEXT,
    resource_id          TEXT,
    pricing_quantity     REAL,
    pricing_unit         TEXT,
    list_unit_price      REAL,
    list_cost            REAL,
    effective_cost       REAL,
    billed_cost          REAL,
    billing_currency     TEXT,
    billing_period_start TEXT,
    billing_period_end   TEXT,
    charge_period_start  TEXT,
    charge_period_end    TEXT,
    tags                 TEXT,
    ingested_at          TEXT
)
"""

# INSERT OR REPLACE makes writes idempotent: re-delivering the same RecordId
# (at-least-once delivery) overwrites rather than duplicating.
_UPSERT = """
INSERT OR REPLACE INTO billing_records (
    record_id, provider_name, billing_account_id, billing_account_name,
    service_name, service_category, charge_category, region_id, resource_id,
    pricing_quantity, pricing_unit, list_unit_price, list_cost, effective_cost,
    billed_cost, billing_currency, billing_period_start, billing_period_end,
    charge_period_start, charge_period_end, tags, ingested_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class SQLiteStore(Store):
    def __init__(self, db_path: str) -> None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()

    def write(self, record: FocusBillingRecord) -> None:
        r = record
        self._conn.execute(
            _UPSERT,
            (
                r.RecordId,
                r.ProviderName,
                r.BillingAccountId,
                r.BillingAccountName,
                r.ServiceName,
                r.ServiceCategory,
                r.ChargeCategory,
                r.RegionId,
                r.ResourceId,
                r.PricingQuantity,
                r.PricingUnit,
                r.ListUnitPrice,
                r.ListCost,
                r.EffectiveCost,
                r.BilledCost,
                r.BillingCurrency,
                r.BillingPeriodStart.isoformat(),
                r.BillingPeriodEnd.isoformat(),
                r.ChargePeriodStart.isoformat(),
                r.ChargePeriodEnd.isoformat(),
                json.dumps(r.Tags),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def count(self) -> int:
        """Number of records currently stored (handy for tests/demos)."""
        cur = self._conn.execute("SELECT COUNT(*) FROM billing_records")
        return int(cur.fetchone()[0])

    def close(self) -> None:
        self._conn.close()
