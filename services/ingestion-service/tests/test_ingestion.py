"""Tests for the ingestion logic: validation, storage, idempotency, dead-lettering."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from finops_common.models import FocusBillingRecord

from ingestion_service.consumer import process_message
from ingestion_service.storage import DeadLetterWriter, SQLiteStore


def _valid_record(record_id: str = "rec-1") -> FocusBillingRecord:
    now = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    return FocusBillingRecord(
        RecordId=record_id,
        ProviderName="AWS",
        BillingAccountId="acct-1",
        BillingPeriodStart=now,
        BillingPeriodEnd=now,
        ChargePeriodStart=now,
        ChargePeriodEnd=now,
        ServiceName="Amazon EC2",
        ServiceCategory="Compute",
        ChargeCategory="Usage",
        RegionId="us-east-1",
        ResourceId="i-123",
        PricingQuantity=10.0,
        PricingUnit="Hours",
        ListUnitPrice=0.5,
        ListCost=5.0,
        EffectiveCost=4.0,
        BilledCost=4.0,
        BillingCurrency="USD",
    )


def _store_and_dlq(tmp_path):
    store = SQLiteStore(str(tmp_path / "finops.db"))
    dlq = DeadLetterWriter(str(tmp_path / "dlq.ndjson"))
    return store, dlq


def test_valid_message_is_stored(tmp_path):
    store, dlq = _store_and_dlq(tmp_path)
    ok = process_message(_valid_record().to_json().encode("utf-8"), b"acct-1", store, dlq)
    assert ok is True
    assert store.count() == 1
    assert dlq.count == 0


def test_malformed_json_is_dead_lettered(tmp_path):
    store, dlq = _store_and_dlq(tmp_path)
    ok = process_message(b"this is not json", b"k", store, dlq)
    assert ok is False
    assert store.count() == 0
    assert dlq.count == 1


def test_validation_error_is_dead_lettered(tmp_path):
    store, dlq = _store_and_dlq(tmp_path)
    # Valid JSON, but missing nearly all required fields.
    payload = json.dumps({"RecordId": "rec-x", "ProviderName": "AWS"}).encode("utf-8")
    ok = process_message(payload, b"k", store, dlq)
    assert ok is False
    assert store.count() == 0
    assert dlq.count == 1


def test_none_value_is_dead_lettered(tmp_path):
    store, dlq = _store_and_dlq(tmp_path)
    ok = process_message(None, None, store, dlq)
    assert ok is False
    assert dlq.count == 1


def test_sqlite_write_is_idempotent(tmp_path):
    store, dlq = _store_and_dlq(tmp_path)
    payload = _valid_record("dup-1").to_json().encode("utf-8")
    process_message(payload, b"k", store, dlq)
    process_message(payload, b"k", store, dlq)  # same RecordId again
    assert store.count() == 1  # not 2 -> idempotent upsert
