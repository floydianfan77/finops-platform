"""Sink that prints records as JSON lines to stdout."""

from __future__ import annotations

import sys

from billing_generator.models import FocusBillingRecord
from billing_generator.sinks.base import Sink


class StdoutSink(Sink):
    def emit(self, record: FocusBillingRecord) -> None:
        sys.stdout.write(record.to_json() + "\n")

    def flush(self) -> None:
        sys.stdout.flush()
