"""Read queries over the gold rollup tables produced by the aggregation service.

Every function raises :class:`GoldNotReady` if the required gold table is missing,
so the API can return a friendly "run the aggregation service first" message.
"""

from __future__ import annotations

import sqlite3

from api_service.db import table_exists


class GoldNotReady(RuntimeError):
    """Raised when a required ``agg_*`` table does not exist yet."""


def _require(conn: sqlite3.Connection, table: str) -> None:
    if not table_exists(conn, table):
        raise GoldNotReady(
            f"Gold table '{table}' not found. Run the aggregation service first "
            f"(make aggregate)."
        )


def summary(conn: sqlite3.Connection) -> dict:
    _require(conn, "agg_cost_by_provider")
    row = conn.execute(
        "SELECT ROUND(SUM(billed_cost), 2)    AS total_billed, "
        "       ROUND(SUM(effective_cost), 2) AS total_effective, "
        "       SUM(record_count)             AS record_count, "
        "       COUNT(DISTINCT usage_date)    AS days, "
        "       COUNT(DISTINCT provider_name) AS providers "
        "FROM agg_cost_by_provider"
    ).fetchone()
    return {
        "total_billed": row["total_billed"] or 0.0,
        "total_effective": row["total_effective"] or 0.0,
        "record_count": row["record_count"] or 0,
        "days": row["days"] or 0,
        "providers": row["providers"] or 0,
    }


def by_service(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    _require(conn, "agg_cost_by_service")
    rows = conn.execute(
        "SELECT service_name, "
        "       ROUND(SUM(billed_cost), 2)    AS billed_cost, "
        "       ROUND(SUM(effective_cost), 2) AS effective_cost, "
        "       SUM(record_count)             AS record_count "
        "FROM agg_cost_by_service GROUP BY service_name "
        "ORDER BY billed_cost DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def by_provider(conn: sqlite3.Connection) -> list[dict]:
    _require(conn, "agg_cost_by_provider")
    rows = conn.execute(
        "SELECT provider_name, "
        "       ROUND(SUM(billed_cost), 2)    AS billed_cost, "
        "       ROUND(SUM(effective_cost), 2) AS effective_cost "
        "FROM agg_cost_by_provider GROUP BY provider_name "
        "ORDER BY billed_cost DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def by_account(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    _require(conn, "agg_cost_by_account")
    rows = conn.execute(
        "SELECT billing_account_id, billing_account_name, "
        "       ROUND(SUM(billed_cost), 2) AS billed_cost "
        "FROM agg_cost_by_account GROUP BY billing_account_id, billing_account_name "
        "ORDER BY billed_cost DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def by_tag(conn: sqlite3.Connection, key: str) -> list[dict]:
    _require(conn, "agg_cost_by_tag")
    rows = conn.execute(
        "SELECT tag_value, "
        "       ROUND(SUM(billed_cost), 2) AS billed_cost "
        "FROM agg_cost_by_tag WHERE tag_key = ? GROUP BY tag_value "
        "ORDER BY billed_cost DESC",
        (key,),
    ).fetchall()
    return [dict(r) for r in rows]


def timeseries(conn: sqlite3.Connection) -> list[dict]:
    """Daily total billed cost across all providers (for the trend chart)."""
    _require(conn, "agg_cost_by_provider")
    rows = conn.execute(
        "SELECT usage_date, ROUND(SUM(billed_cost), 2) AS billed_cost "
        "FROM agg_cost_by_provider GROUP BY usage_date ORDER BY usage_date"
    ).fetchall()
    return [dict(r) for r in rows]


def provider_totals(conn: sqlite3.Connection) -> dict[str, float]:
    """{provider_name: total_billed} — used by the budget evaluator."""
    return {r["provider_name"]: r["billed_cost"] for r in by_provider(conn)}


def total_billed(conn: sqlite3.Connection) -> float:
    return float(summary(conn)["total_billed"])
