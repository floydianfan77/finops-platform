"""Dead-letter writer: captures messages that fail validation/processing.

Instead of crashing or silently dropping bad data, we append it (with the error
and some context) to a newline-delimited JSON file for later inspection/replay.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class DeadLetterWriter:
    def __init__(self, dlq_path: str) -> None:
        self._path = Path(dlq_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self._path.open("a", encoding="utf-8")
        self.count = 0

    def write(self, raw_value: bytes | None, error: str, key: bytes | None = None) -> None:
        entry = {
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "error": error,
            "key": key.decode("utf-8", errors="replace") if key else None,
            "raw_value": raw_value.decode("utf-8", errors="replace") if raw_value else None,
        }
        self._fh.write(json.dumps(entry) + "\n")
        self._fh.flush()
        self.count += 1

    def close(self) -> None:
        self._fh.close()
