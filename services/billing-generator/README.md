# billing-generator

Synthetic, **FOCUS-aligned** cloud billing data generator. This is **step 1** of the
FinOps platform: a controllable source of realistic cost & usage events.

## Install

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# bash:
# . .venv/bin/activate

pip install -e ".[dev]"
```

## Usage

```bash
# Emit 5 records every 2 seconds to the terminal
billing-generator --sink stdout --interval 2 --batch-size 5

# Append newline-delimited JSON to a file
billing-generator --sink file --file-path ./data/billing.ndjson --batch-size 10

# Generate a fixed number of batches then stop (great for tests/demos)
billing-generator --sink stdout --max-batches 3

# Reproducible data
billing-generator --sink stdout --seed 42
```

All flags also read from environment variables (see `.env.example`). CLI flags win
over env vars.

## How it stays broker-ready

Output goes through a `Sink` interface (`src/billing_generator/sinks/`):

| Sink     | Status | Notes                                              |
|----------|--------|----------------------------------------------------|
| `stdout` | ✅      | Prints JSON lines                                  |
| `file`   | ✅      | Appends NDJSON                                     |
| `broker` | 🔜     | Kafka/Red Panda via `confluent-kafka` (step 2)     |

To enable the broker sink later:

```bash
pip install -e ".[broker]"
billing-generator --sink broker   # uses BROKER_* settings
```

## Data shape

Records follow the FOCUS-aligned contract in
[`../../schemas/billing/focus_billing_record.schema.json`](../../schemas/billing/focus_billing_record.schema.json).

## Project layout

```
src/billing_generator/
├── main.py          # CLI entry point
├── config.py        # Settings (env + CLI)
├── models.py        # FocusBillingRecord (pydantic)
├── generators/      # Fake data generation
│   ├── accounts.py  # Accounts, services, regions catalog
│   └── billing.py   # Billing record factory
├── sinks/           # Output destinations (broker-agnostic)
│   ├── base.py
│   ├── stdout_sink.py
│   ├── file_sink.py
│   └── broker_sink.py
└── scheduler.py     # Batch + interval loop
```
