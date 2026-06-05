"""Tests for the synthetic billing generators and sinks."""

from __future__ import annotations

import json

from billing_generator.config import Settings
from finops_common.models import FocusBillingRecord

from billing_generator.generators import AccountCatalog, BillingGenerator
from billing_generator.sinks import build_sink
from billing_generator.sinks.file_sink import FileSink


def _make_generator(seed: int = 42) -> BillingGenerator:
    catalog = AccountCatalog(num_accounts=5, seed=seed)
    return BillingGenerator(catalog)


def test_catalog_is_deterministic_with_seed():
    a = AccountCatalog(num_accounts=5, seed=7)
    b = AccountCatalog(num_accounts=5, seed=7)
    assert [acc.account_id for acc in a.accounts] == [acc.account_id for acc in b.accounts]


def test_generate_one_returns_valid_record():
    record = _make_generator().generate_one()
    assert isinstance(record, FocusBillingRecord)
    assert record.RecordId
    assert record.BillingCurrency == "USD"
    assert record.PricingQuantity >= 0
    assert record.ChargePeriodStart < record.ChargePeriodEnd


def test_generate_batch_size():
    records = _make_generator().generate_batch(10)
    assert len(records) == 10
    assert len({r.RecordId for r in records}) == 10  # unique ids


def test_record_serializes_to_json():
    record = _make_generator().generate_one()
    payload = json.loads(record.to_json())
    assert payload["ProviderName"] in {"AWS", "GCP", "Azure", "OCI"}
    assert "BillingAccountId" in payload


def test_charge_category_values_are_valid():
    records = _make_generator(seed=1).generate_batch(50)
    valid = {"Usage", "Purchase", "Tax", "Credit", "Adjustment"}
    assert all(r.ChargeCategory in valid for r in records)


def test_file_sink_writes_ndjson(tmp_path):
    out = tmp_path / "billing.ndjson"
    records = _make_generator().generate_batch(3)

    with FileSink(str(out)) as sink:
        written = sink.emit_many(records)

    assert written == 3
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    assert all(json.loads(line)["RecordId"] for line in lines)


def test_build_sink_factory_stdout():
    settings = Settings(sink="stdout")
    sink = build_sink(settings)
    assert sink.__class__.__name__ == "StdoutSink"


def test_build_sink_rejects_unknown():
    settings = Settings(sink="carrier-pigeon")
    try:
        build_sink(settings)
    except ValueError as exc:
        assert "Unknown sink" in str(exc)
    else:
        raise AssertionError("expected ValueError for unknown sink")
