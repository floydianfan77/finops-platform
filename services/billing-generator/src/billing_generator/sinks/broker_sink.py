"""Sink that publishes records to a Kafka-compatible broker (Kafka or Red Panda).

STEP 2 placeholder. The structure is complete and intentionally provider-neutral:
``confluent-kafka`` speaks the Kafka protocol, which both Apache Kafka and Red Panda
implement, so the *same* code targets either by changing ``bootstrap_servers``.

To activate:
    pip install -e ".[broker]"
then set BILLING_SINK=broker (and BROKER_* settings).
"""

from __future__ import annotations

from billing_generator.config import BrokerSettings
from billing_generator.models import FocusBillingRecord
from billing_generator.sinks.base import Sink


class BrokerSink(Sink):
    def __init__(self, settings: BrokerSettings) -> None:
        self._settings = settings
        self._producer = None
        self._connect()

    def _connect(self) -> None:
        try:
            from confluent_kafka import Producer
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError(
                "The 'broker' sink requires the optional dependency. "
                'Install it with: pip install -e ".[broker]"'
            ) from exc

        self._producer = Producer(
            {
                "bootstrap.servers": self._settings.bootstrap_servers,
                "client.id": self._settings.client_id,
                "enable.idempotence": True,
            }
        )

    def emit(self, record: FocusBillingRecord) -> None:
        assert self._producer is not None
        # Key by account so a tenant's records land on the same partition (ordering).
        self._producer.produce(
            topic=self._settings.topic,
            key=record.BillingAccountId.encode("utf-8"),
            value=record.to_json().encode("utf-8"),
        )
        # Serve delivery callbacks without blocking.
        self._producer.poll(0)

    def flush(self) -> None:
        if self._producer is not None:
            self._producer.flush()

    def close(self) -> None:
        self.flush()
