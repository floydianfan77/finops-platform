# Roadmap

Incremental build-out of the FinOps platform. Each step is shippable on its own.

## Step 1 — Synthetic billing generator ✅ (current)

Produce realistic, FOCUS-aligned billing records on a schedule.

- [x] Monorepo scaffold (services / libs / schemas / docs / infra)
- [x] FOCUS-aligned billing record schema + typed model
- [x] Generators (accounts, services, regions, billing records)
- [x] Pluggable sinks: `stdout`, `file`
- [x] Sink abstraction ready for `broker`
- [x] CLI + scheduler (batch size + interval)
- [ ] (nice-to-have) cost anomalies / spikes injection

## Step 2 — Message broker ✅

Event backbone running. We run **both** Kafka and Red Panda (same Kafka protocol).

- [x] Decide broker (run both; see `docs/adr/0002-message-broker-choice.md`)
- [x] Add broker(s) to `docker-compose.yml` (profiles: `redpanda`, `kafka`, `app`)
- [x] Implement `broker` sink with `confluent-kafka` (verified against both)
- [x] Define topic naming (`finops.billing.raw`) + partitioning (key = `BillingAccountId`, 3 partitions)
- [ ] Schema registry? (Avro/JSON Schema) — decide (follow-up ADR)

## Step 3 — Ingestion + storage ✅

- [x] Consumer service reading `finops.billing.raw` (`services/ingestion-service`)
- [x] Validate against the shared `finops_common` contract, dead-letter invalid records
- [x] Land validated data in **SQLite** (`billing_records`), idempotent upserts
- [x] Shared contract promoted to `libs/common` (`finops-common`)
- [ ] (later) land to a warehouse/lake for scale

## Step 4 — Transformation ⏳

- [ ] Normalize/enrich to canonical FOCUS
- [ ] Aggregations (by account, service, tag, period)

## Step 5 — API + UI + alerting ⏳

- [ ] Query API
- [ ] Dashboard (cost trends, top services, anomalies)
- [ ] Budgets & alerts
