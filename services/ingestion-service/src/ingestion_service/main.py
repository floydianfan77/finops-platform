"""CLI entry point for the ingestion service.

Examples:
    ingestion-service --from-beginning --max-messages 50
    ingestion-service --bootstrap-servers localhost:9094 --group-id finops-ingestion
"""

from __future__ import annotations

import argparse

from ingestion_service import __version__
from ingestion_service.config import Settings
from ingestion_service.consumer import BillingConsumer
from ingestion_service.storage import DeadLetterWriter, SQLiteStore


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ingestion-service",
        description="Consume FOCUS billing records, validate, and land them in SQLite.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--bootstrap-servers", dest="bootstrap_servers",
                        help="Broker address (default env INGEST_BOOTSTRAP_SERVERS or localhost:9092).")
    parser.add_argument("--topic", help="Topic to consume.")
    parser.add_argument("--group-id", dest="group_id", help="Consumer group id.")
    parser.add_argument("--db-path", dest="db_path", help="SQLite database file path.")
    parser.add_argument("--dlq-path", dest="dlq_path", help="Dead-letter NDJSON file path.")
    parser.add_argument("--max-messages", dest="max_messages", type=int,
                        help="Stop after N messages (default: run until interrupted).")
    parser.add_argument("--from-beginning", action="store_true",
                        help="Read the topic from the earliest offset for this group.")
    return parser


def _merge_settings(args: argparse.Namespace) -> Settings:
    settings = Settings()
    overrides = {
        "bootstrap_servers": args.bootstrap_servers,
        "topic": args.topic,
        "group_id": args.group_id,
        "db_path": args.db_path,
        "dlq_path": args.dlq_path,
        "max_messages": args.max_messages,
    }
    for key, value in overrides.items():
        if value is not None:
            setattr(settings, key, value)
    if args.from_beginning:
        settings.auto_offset_reset = "earliest"
    return settings


def main() -> None:
    args = _build_parser().parse_args()
    settings = _merge_settings(args)

    store = SQLiteStore(settings.db_path)
    dead_letter = DeadLetterWriter(settings.dlq_path)
    consumer = BillingConsumer(settings, store, dead_letter)
    consumer.run()


if __name__ == "__main__":
    main()
