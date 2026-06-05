"""Kafka consumer: read raw billing records, validate, land them, dead-letter failures."""

from __future__ import annotations

import signal
import sys
from types import FrameType

from pydantic import ValidationError

from finops_common.models import FocusBillingRecord

from ingestion_service.config import Settings
from ingestion_service.storage.base import Store
from ingestion_service.storage.dead_letter import DeadLetterWriter


def process_message(
    value: bytes | None,
    key: bytes | None,
    store: Store,
    dead_letter: DeadLetterWriter,
) -> bool:
    """Validate one raw message and route it. Returns True if stored, False if dead-lettered.

    This contains all the ingestion logic and is deliberately broker-free so it can be
    unit-tested with plain bytes.
    """
    if value is None:
        dead_letter.write(value, "empty message value", key)
        return False
    try:
        record = FocusBillingRecord.model_validate_json(value)
    except ValidationError as exc:
        dead_letter.write(value, f"validation error: {exc.error_count()} issue(s)", key)
        return False
    except ValueError as exc:  # malformed JSON
        dead_letter.write(value, f"json error: {exc}", key)
        return False

    store.write(record)
    return True


class BillingConsumer:
    def __init__(
        self,
        settings: Settings,
        store: Store,
        dead_letter: DeadLetterWriter,
    ) -> None:
        self._settings = settings
        self._store = store
        self._dead_letter = dead_letter
        self._consumer = None
        self._stop = False

    def _handle_signal(self, _signum: int, _frame: FrameType | None) -> None:
        self._stop = True

    def _connect(self) -> None:
        from confluent_kafka import Consumer

        self._consumer = Consumer(
            {
                "bootstrap.servers": self._settings.bootstrap_servers,
                "group.id": self._settings.group_id,
                "auto.offset.reset": self._settings.auto_offset_reset,
                # We commit offsets ourselves, only after a message is handled.
                "enable.auto.commit": False,
            }
        )
        self._consumer.subscribe([self._settings.topic])

    def run(self) -> dict[str, int]:
        signal.signal(signal.SIGINT, self._handle_signal)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._handle_signal)

        self._connect()
        assert self._consumer is not None

        stored = 0
        dead = 0
        handled = 0
        max_messages = self._settings.max_messages

        try:
            while not self._stop:
                msg = self._consumer.poll(self._settings.poll_timeout)
                if msg is None:
                    continue
                if msg.error():
                    self._dead_letter.write(None, f"broker error: {msg.error()}", None)
                    dead += 1
                else:
                    ok = process_message(
                        msg.value(), msg.key(), self._store, self._dead_letter
                    )
                    stored += int(ok)
                    dead += int(not ok)

                # At-least-once: commit only AFTER handling the message.
                self._consumer.commit(msg, asynchronous=False)
                handled += 1

                if max_messages is not None and handled >= max_messages:
                    break
        finally:
            self._consumer.close()
            self._store.close()
            self._dead_letter.close()

        print(
            f"[ingestion-service] stopped. stored {stored}, dead-lettered {dead} "
            f"(handled {handled}).",
            file=sys.stderr,
        )
        return {"stored": stored, "dead_lettered": dead, "handled": handled}
