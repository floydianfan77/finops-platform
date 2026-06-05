"""Tests for the gold-layer aggregation (correct sums, tag expansion, idempotency)."""

from __future__ import annotations

import json
import sqlite3

from aggregation_service.transform import gold_table_names, rebuild_all

_CREATE = """
CREATE TABLE billing_records (
    record_id TEXT PRIMARY KEY,
    provider_name TEXT,
    billing_account_id TEXT,
    billing_account_name TEXT,
    service_name TEXT,
    service_category TEXT,
    charge_category TEXT,
    region_id TEXT,
    resource_id TEXT,
    billed_cost REAL,
    effective_cost REAL,
    list_cost REAL,
    charge_period_start TEXT,
    tags TEXT
)
"""


def _seed(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE)
    rows = [
        ("r1", "AWS", "acct-1", "Acme", "Amazon EC2", "Compute", "2026-06-05T10:00:00+00:00",
         100.0, 90.0, 100.0, {"team": "payments", "environment": "prod"}),
        ("r2", "AWS", "acct-1", "Acme", "Amazon EC2", "Compute", "2026-06-05T11:00:00+00:00",
         50.0, 45.0, 50.0, {"team": "payments", "environment": "dev"}),
        ("r3", "GCP", "acct-2", "Globex", "BigQuery", "Analytics", "2026-06-05T12:00:00+00:00",
         200.0, 200.0, 220.0, {"team": "data", "environment": "prod"}),
    ]
    for r in rows:
        *cols, tags = r
        conn.execute(
            "INSERT INTO billing_records (record_id, provider_name, billing_account_id, "
            "billing_account_name, service_name, service_category, charge_period_start, "
            "billed_cost, effective_cost, list_cost, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (*cols, json.dumps(tags)),
        )
    conn.commit()


def test_rebuild_creates_all_gold_tables(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "f.db"))
    _seed(conn)
    counts = rebuild_all(conn)
    for name in gold_table_names():
        assert name in counts
    # EC2 (2 rows -> 1 service/day group) + BigQuery (1) = 2 service rows.
    assert counts["agg_cost_by_service"] == 2


def test_service_billed_cost_sum(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "f.db"))
    _seed(conn)
    rebuild_all(conn)
    ec2 = conn.execute(
        "SELECT billed_cost FROM agg_cost_by_service WHERE service_name = 'Amazon EC2'"
    ).fetchone()[0]
    assert ec2 == 150.0  # 100 + 50


def test_tag_rollup_expands_tags(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "f.db"))
    _seed(conn)
    rebuild_all(conn)
    payments = conn.execute(
        "SELECT SUM(billed_cost) FROM agg_cost_by_tag "
        "WHERE tag_key = 'team' AND tag_value = 'payments'"
    ).fetchone()[0]
    assert payments == 150.0  # r1 + r2


def test_rebuild_is_idempotent(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "f.db"))
    _seed(conn)
    first = rebuild_all(conn)
    second = rebuild_all(conn)  # run again -> must not double
    assert first == second
