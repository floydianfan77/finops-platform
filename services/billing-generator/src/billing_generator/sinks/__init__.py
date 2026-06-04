"""Output sinks + a factory to build one from settings."""

from __future__ import annotations

from billing_generator.config import Settings
from billing_generator.sinks.base import Sink
from billing_generator.sinks.file_sink import FileSink
from billing_generator.sinks.stdout_sink import StdoutSink

__all__ = ["Sink", "StdoutSink", "FileSink", "build_sink"]


def build_sink(settings: Settings) -> Sink:
    """Construct the configured sink. The 'broker' sink is imported lazily so its
    optional dependency is only needed when actually used (step 2)."""
    kind = settings.sink.lower()

    if kind == "stdout":
        return StdoutSink()
    if kind == "file":
        return FileSink(settings.file_path)
    if kind == "broker":
        from billing_generator.sinks.broker_sink import BrokerSink

        return BrokerSink(settings.broker)

    raise ValueError(
        f"Unknown sink '{settings.sink}'. Valid options: stdout, file, broker."
    )
