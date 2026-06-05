"""Storage abstraction for validated billing records.

Same idea as the generator's ``Sink``: the consumer doesn't care *where* records
land (SQLite now, a warehouse later) as long as the destination can ``write`` them.
"""

from __future__ import annotations

import abc

from finops_common.models import FocusBillingRecord


class Store(abc.ABC):
    """Destination for validated billing records."""

    @abc.abstractmethod
    def write(self, record: FocusBillingRecord) -> None:
        """Persist a single validated record (idempotently, keyed by RecordId)."""

    def close(self) -> None:
        """Release resources. No-op by default."""

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
