"""Build pre-aggregated 'gold' cost rollups from the raw ``billing_records`` table.

Each rollup is rebuilt with CREATE TABLE AS SELECT (drop + recreate), which makes the
whole transformation **idempotent**: running it twice yields identical tables, never
doubled numbers. Costs are bucketed by usage day (``date(charge_period_start)``).
"""

from __future__ import annotations

import sqlite3

# (table_name, SQL) pairs. Each SELECT aggregates billing_records into one gold table.
_ROLLUPS: list[tuple[str, str]] = [
    (
        "agg_cost_by_service",
        """
        SELECT
            date(charge_period_start) AS usage_date,
            service_name,
            service_category,
            COUNT(*)                  AS record_count,
            ROUND(SUM(billed_cost), 6)    AS billed_cost,
            ROUND(SUM(effective_cost), 6) AS effective_cost,
            ROUND(SUM(list_cost), 6)      AS list_cost
        FROM billing_records
        GROUP BY usage_date, service_name, service_category
        """,
    ),
    (
        "agg_cost_by_account",
        """
        SELECT
            date(charge_period_start) AS usage_date,
            billing_account_id,
            billing_account_name,
            COUNT(*)                  AS record_count,
            ROUND(SUM(billed_cost), 6)    AS billed_cost,
            ROUND(SUM(effective_cost), 6) AS effective_cost
        FROM billing_records
        GROUP BY usage_date, billing_account_id, billing_account_name
        """,
    ),
    (
        "agg_cost_by_provider",
        """
        SELECT
            date(charge_period_start) AS usage_date,
            provider_name,
            COUNT(*)                  AS record_count,
            ROUND(SUM(billed_cost), 6)    AS billed_cost,
            ROUND(SUM(effective_cost), 6) AS effective_cost
        FROM billing_records
        GROUP BY usage_date, provider_name
        """,
    ),
    (
        # json_each expands the JSON tags column into one row per key/value, so we can
        # allocate cost by tag (e.g. team, environment, cost_center).
        "agg_cost_by_tag",
        """
        SELECT
            date(b.charge_period_start) AS usage_date,
            t.key                       AS tag_key,
            t.value                     AS tag_value,
            COUNT(*)                    AS record_count,
            ROUND(SUM(b.billed_cost), 6)    AS billed_cost,
            ROUND(SUM(b.effective_cost), 6) AS effective_cost
        FROM billing_records AS b, json_each(b.tags) AS t
        GROUP BY usage_date, tag_key, tag_value
        """,
    ),
]


def rebuild_all(conn: sqlite3.Connection) -> dict[str, int]:
    """(Re)build every gold table. Returns {table_name: row_count}."""
    counts: dict[str, int] = {}
    for table, select_sql in _ROLLUPS:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.execute(f"CREATE TABLE {table} AS {select_sql}")
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.commit()
    return counts


def gold_table_names() -> list[str]:
    return [name for name, _ in _ROLLUPS]
