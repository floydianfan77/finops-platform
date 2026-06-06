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

## Step 4 — Transformation ✅

Gold-layer rollups built from the landed `billing_records` table (`services/aggregation-service`).

- [x] Idempotent transformation (CREATE TABLE AS SELECT → re-runnable, never doubles)
- [x] Aggregations bucketed by usage day: by service, by account, by provider
- [x] Cost-by-tag allocation via `json_each` (team / environment / cost_center)
- [x] Tests: correct sums, tag expansion, idempotent rebuild
- [ ] (later) normalize/enrich to canonical FOCUS as data sources grow

## Step 5 — API + UI + alerting ✅

Read API + dashboard + budget alerts over the gold rollups (`services/api-service`).

- [x] Query API (FastAPI): summary, by service/provider/account/tag, daily timeseries
- [x] Dashboard (Chart.js): KPIs, trend, top services, provider split, cost by team
- [x] Budgets & alerts (OK / WARN / OVER) per total and per provider
- [x] Auto-generated OpenAPI docs at `/docs`; tests with FastAPI `TestClient`
- [ ] (later) anomaly detection / scheduled alert delivery (email/Slack)
