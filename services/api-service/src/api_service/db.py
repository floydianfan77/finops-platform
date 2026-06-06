"""Tiny SQLite access layer (read-only) for the API."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def read_conn(db_path: str) -> Iterator[sqlite3.Connection]:
    """Open the database read-only. Rows behave like dicts (``row["col"]``)."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (name,)
    ).fetchone()
    return row is not None
