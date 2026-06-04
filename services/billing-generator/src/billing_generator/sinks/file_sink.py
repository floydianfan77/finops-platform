"""Sink that appends records to a newline-delimited JSON (NDJSON) file."""

from __future__ import annotations

from pathlib import Path

from billing_generator.models import FocusBillingRecord
from billing_generator.sinks.base import Sink


class FileSink(Sink):
    def __init__(self, file_path: str) -> None:
        self._path = Path(file_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self._path.open("a", encoding="utf-8")

    def emit(self, record: FocusBillingRecord) -> None:
        self._fh.write(record.to_json() + "\n")

    def flush(self) -> None:
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()
