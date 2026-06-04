"""Drives generation: emit ``batch_size`` records every ``interval_seconds``."""

from __future__ import annotations

import signal
import sys
import time
from types import FrameType

from billing_generator.generators import AccountCatalog, BillingGenerator
from billing_generator.sinks.base import Sink


class GeneratorScheduler:
    def __init__(
        self,
        generator: BillingGenerator,
        sink: Sink,
        *,
        batch_size: int,
        interval_seconds: float,
        max_batches: int | None = None,
    ) -> None:
        self._generator = generator
        self._sink = sink
        self._batch_size = batch_size
        self._interval = interval_seconds
        self._max_batches = max_batches
        self._stop = False

    def _handle_signal(self, _signum: int, _frame: FrameType | None) -> None:
        # Graceful shutdown on Ctrl+C / SIGTERM.
        self._stop = True

    def run(self) -> int:
        signal.signal(signal.SIGINT, self._handle_signal)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._handle_signal)

        total = 0
        batches = 0
        with self._sink:
            while not self._stop:
                records = self._generator.generate_batch(self._batch_size)
                total += self._sink.emit_many(records)
                self._sink.flush()
                batches += 1

                if self._max_batches is not None and batches >= self._max_batches:
                    break
                if self._interval > 0 and not self._stop:
                    time.sleep(self._interval)

        print(
            f"[billing-generator] stopped. emitted {total} records "
            f"across {batches} batch(es).",
            file=sys.stderr,
        )
        return total


def build_scheduler(
    *,
    num_accounts: int,
    seed: int | None,
    sink: Sink,
    batch_size: int,
    interval_seconds: float,
    max_batches: int | None,
) -> GeneratorScheduler:
    catalog = AccountCatalog(num_accounts=num_accounts, seed=seed)
    generator = BillingGenerator(catalog)
    return GeneratorScheduler(
        generator,
        sink,
        batch_size=batch_size,
        interval_seconds=interval_seconds,
        max_batches=max_batches,
    )
