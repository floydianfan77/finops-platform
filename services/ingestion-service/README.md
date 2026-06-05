# ingestion-service

Step 3 of the FinOps platform. Consumes FOCUS billing records from the broker,
**validates** each one against the shared `finops_common` contract, and **lands**
valid records into a queryable **SQLite** database. Anything that fails validation is
routed to a **dead-letter** file instead of being dropped or crashing the pipeline.

```
broker (finops.billing.raw) ──► ingestion-service ──► SQLite (billing_records)
                                       │
                                       └─ invalid ─► dead_letter.ndjson
```

## Quick start

```bash
cd services/ingestion-service
pip install -e ".[dev]"          # finops-common must be installed too (libs/common)

# Read everything currently on the topic into ./data/finops.db
ingestion-service --from-beginning --max-messages 100
```

Point it at Kafka instead of Red Panda with `--bootstrap-servers localhost:9094`.

## Key ideas

- **Consumer group** (`--group-id`): tracks committed offsets so restarts resume where
  they left off; multiple instances share the partitions.
- **At-least-once delivery**: offsets are committed *after* a message is handled, and
  the SQLite write is **idempotent** (`INSERT OR REPLACE` on `RecordId`), so a
  re-delivered record overwrites rather than duplicates.
- **Dead-letter queue**: invalid payloads are appended to `dead_letter.ndjson` with the
  error and original bytes for later inspection/replay.

## Querying the data

```bash
sqlite3 ./data/finops.db "SELECT service_name, ROUND(SUM(billed_cost),2) AS cost \
  FROM billing_records GROUP BY service_name ORDER BY cost DESC;"
```
