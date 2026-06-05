"""Sink abstraction: where generated billing records are written.

This is the seam that keeps the generator broker-agnostic. Step 1 ships ``stdout``
and ``file`` sinks; step 2 adds a ``broker`` sink (Kafka / Red Panda) implementing
the *same* interface, so no generator code changes.
"""

from __future__ import annotations

import abc
from collections.abc import Iterable

from finops_common.models import FocusBillingRecord


class Sink(abc.ABC):
    """Destination for billing records."""

    @abc.abstractmethod
    def emit(self, record: FocusBillingRecord) -> None:
        """Write a single record."""

    def emit_many(self, records: Iterable[FocusBillingRecord]) -> int:
        """Write many records; returns the count. Override for true batch writes."""
        count = 0
        for record in records:
            self.emit(record)
            count += 1
        return count

    def flush(self) -> None:
        """Flush any buffered records. No-op by default."""

    def close(self) -> None:
        """Release resources. No-op by default."""

    def __enter__(self) -> "Sink":
        return self

    def __exit__(self, *exc: object) -> None:
        self.flush()
        self.close()
