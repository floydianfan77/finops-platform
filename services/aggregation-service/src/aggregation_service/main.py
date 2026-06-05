"""CLI entry point for the aggregation service.

Examples:
    aggregation-service --db-path ../ingestion-service/data/finops.db
    aggregation-service --report
"""

from __future__ import annotations

import argparse
import sqlite3
import sys

from aggregation_service import __version__
from aggregation_service.config import Settings
from aggregation_service.transform import rebuild_all


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aggregation-service",
        description="Build pre-aggregated (gold) cost rollups from landed billing data.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--db-path", dest="db_path", help="SQLite database to read/write.")
    parser.add_argument("--report", action="store_true",
                        help="Print a short summary of the rebuilt rollups.")
    return parser


def _print_report(conn: sqlite3.Connection) -> None:
    print("\n--- Top services by billed cost ---", file=sys.stderr)
    rows = conn.execute(
        "SELECT service_name, ROUND(SUM(billed_cost), 2) AS c "
        "FROM agg_cost_by_service GROUP BY service_name ORDER BY c DESC LIMIT 5"
    ).fetchall()
    for name, cost in rows:
        print(f"  {name:<26} USD {cost:>12,.2f}", file=sys.stderr)

    print("\n--- Cost by tag: team ---", file=sys.stderr)
    rows = conn.execute(
        "SELECT tag_value, ROUND(SUM(billed_cost), 2) AS c "
        "FROM agg_cost_by_tag WHERE tag_key = 'team' GROUP BY tag_value ORDER BY c DESC"
    ).fetchall()
    for value, cost in rows:
        print(f"  {value:<26} USD {cost:>12,.2f}", file=sys.stderr)


def main() -> None:
    args = _build_parser().parse_args()
    settings = Settings()
    if args.db_path is not None:
        settings.db_path = args.db_path

    conn = sqlite3.connect(settings.db_path)
    try:
        counts = rebuild_all(conn)
        summary = ", ".join(f"{name}={n}" for name, n in counts.items())
        print(f"[aggregation-service] rebuilt gold tables: {summary}", file=sys.stderr)
        if args.report:
            _print_report(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
