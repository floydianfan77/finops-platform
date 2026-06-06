"""Tests for the API (endpoints over seeded gold tables) and budget evaluation."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from api_service.app import create_app
from api_service.budgets import evaluate, status_for
from api_service.config import Settings


def _seed_gold(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE agg_cost_by_provider (usage_date TEXT, provider_name TEXT,
            record_count INT, billed_cost REAL, effective_cost REAL);
        CREATE TABLE agg_cost_by_service (usage_date TEXT, service_name TEXT,
            service_category TEXT, record_count INT, billed_cost REAL,
            effective_cost REAL, list_cost REAL);
        CREATE TABLE agg_cost_by_account (usage_date TEXT, billing_account_id TEXT,
            billing_account_name TEXT, record_count INT, billed_cost REAL,
            effective_cost REAL);
        CREATE TABLE agg_cost_by_tag (usage_date TEXT, tag_key TEXT, tag_value TEXT,
            record_count INT, billed_cost REAL, effective_cost REAL);
        """
    )
    conn.executemany(
        "INSERT INTO agg_cost_by_provider VALUES (?,?,?,?,?)",
        [("2026-06-05", "AWS", 3, 100.0, 90.0), ("2026-06-05", "GCP", 2, 200.0, 200.0),
         ("2026-06-06", "AWS", 1, 50.0, 50.0)],
    )
    conn.executemany(
        "INSERT INTO agg_cost_by_service VALUES (?,?,?,?,?,?,?)",
        [("2026-06-05", "Amazon EC2", "Compute", 3, 120.0, 110.0, 130.0),
         ("2026-06-05", "BigQuery", "Analytics", 2, 230.0, 230.0, 250.0)],
    )
    conn.executemany(
        "INSERT INTO agg_cost_by_account VALUES (?,?,?,?,?,?)",
        [("2026-06-05", "acct-1", "Acme", 3, 100.0, 90.0),
         ("2026-06-05", "acct-2", "Globex", 2, 200.0, 200.0)],
    )
    conn.executemany(
        "INSERT INTO agg_cost_by_tag VALUES (?,?,?,?,?,?)",
        [("2026-06-05", "team", "payments", 3, 100.0, 90.0),
         ("2026-06-05", "team", "data", 2, 200.0, 200.0)],
    )
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path):
    db = tmp_path / "finops.db"
    _seed_gold(str(db))
    settings = Settings(db_path=str(db), budget_total=250.0,
                        budget_by_provider={"AWS": 50.0, "GCP": 1000.0})
    return TestClient(create_app(settings))


def test_health_reports_gold_ready(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["gold_ready"] is True


def test_summary_totals(client):
    r = client.get("/api/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_billed"] == 350.0  # 100 + 200 + 50
    assert body["providers"] == 2
    assert body["days"] == 2


def test_by_provider_sorted_desc(client):
    rows = client.get("/api/costs/by-provider").json()
    # AWS = 100 + 50 = 150, GCP = 200 -> GCP leads, sorted by billed_cost desc.
    assert [r["provider_name"] for r in rows] == ["GCP", "AWS"]
    assert rows[0]["billed_cost"] == 200.0
    assert rows[1]["billed_cost"] == 150.0


def test_by_tag_team(client):
    rows = client.get("/api/costs/by-tag?key=team").json()
    assert {r["tag_value"] for r in rows} == {"payments", "data"}


def test_dashboard_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "FinOps Dashboard" in r.text


def test_budgets_flags_over_and_warn(client):
    body = client.get("/api/budgets").json()
    # total spend 350 vs budget 250 -> OVER
    assert body["overall"]["status"] == "OVER"
    statuses = {p["name"]: p["status"] for p in body["providers"]}
    assert statuses["AWS"] == "OVER"   # 150 vs 50
    assert statuses["GCP"] == "OK"     # 200 vs 1000
    assert body["alert_count"] >= 2


def test_gold_not_ready_returns_503(tmp_path):
    empty = tmp_path / "empty.db"
    sqlite3.connect(str(empty)).close()
    c = TestClient(create_app(Settings(db_path=str(empty))))
    assert c.get("/api/summary").status_code == 503


def test_status_for_thresholds():
    assert status_for(10, 100)["status"] == "OK"
    assert status_for(85, 100)["status"] == "WARN"
    assert status_for(120, 100)["status"] == "OVER"


def test_evaluate_collects_alerts():
    result = evaluate(350.0, {"AWS": 150.0, "GCP": 200.0},
                      budget_total=250.0,
                      budget_by_provider={"AWS": 50.0, "GCP": 1000.0})
    assert result["overall"]["status"] == "OVER"
    assert result["alert_count"] == 2
