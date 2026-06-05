# common (shared library)

Shared, importable definitions used across FinOps services: event contracts,
topic names, and serialization helpers. Keeping these here prevents each service
from re-defining (and drifting on) the same data shapes.

Installable as the `finops-common` package (import name `finops_common`).

## Contents

```
src/finops_common/
├── models.py      # FocusBillingRecord (the authoritative typed contract)
└── topics.py      # Canonical topic names (RAW_BILLING_TOPIC, DEAD_LETTER_TOPIC)
```

Both the `billing-generator` (producer) and `ingestion-service` (consumer) import
the model from here, so the contract is defined **once**. It mirrors
[`../../schemas/billing/focus_billing_record.schema.json`](../../schemas/billing/focus_billing_record.schema.json)
(the language-neutral version).

## Install

```bash
pip install -e libs/common
```
