# common (shared library)

Shared, importable definitions used across FinOps services: event contracts,
topic names, and serialization helpers. Keeping these here prevents each service
from re-defining (and drifting on) the same data shapes.

## Contents (planned)

```
common/
├── events/        # Typed event/contract models (mirror schemas/)
├── topics.py      # Canonical topic name constants (step 2)
└── serde.py       # (De)serialization helpers (JSON now, Avro later)
```

> In step 1, the authoritative billing contract lives in
> [`../../schemas/billing/focus_billing_record.schema.json`](../../schemas/billing/focus_billing_record.schema.json)
> and is implemented as a typed model inside the `billing-generator` service.
> When a second service needs the same model, promote it into this package.
