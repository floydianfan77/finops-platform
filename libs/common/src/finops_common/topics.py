"""Canonical Kafka topic names, shared so producers and consumers never disagree.

Naming convention: ``<domain>.<dataset>.<stage>``.
"""

from __future__ import annotations

# Raw billing records straight from the producer (unprocessed).
RAW_BILLING_TOPIC = "finops.billing.raw"

# Records that failed validation/processing during ingestion (dead-letter).
DEAD_LETTER_TOPIC = "finops.billing.dlq"
