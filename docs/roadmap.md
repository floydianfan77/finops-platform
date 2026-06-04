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

## Step 2 — Message broker 🔜

Introduce the event backbone (decision pending: **Kafka** vs **Red Panda**).

- [ ] Decide broker (see `docs/adr/0002-message-broker-choice.md`)
- [ ] Add broker to `docker-compose.yml` (blocks already prepared)
- [ ] Implement `broker` sink with `confluent-kafka`
- [ ] Define topic naming + partitioning strategy
- [ ] Schema registry? (Avro/JSON Schema) — decide

## Step 3 — Ingestion + storage ⏳

- [ ] Consumer service reading `finops.billing.raw`
- [ ] Validate against schema, dead-letter invalid records
- [ ] Land raw + normalized data (warehouse or lake)

## Step 4 — Transformation ⏳

- [ ] Normalize/enrich to canonical FOCUS
- [ ] Aggregations (by account, service, tag, period)

## Step 5 — API + UI + alerting ⏳

- [ ] Query API
- [ ] Dashboard (cost trends, top services, anomalies)
- [ ] Budgets & alerts
