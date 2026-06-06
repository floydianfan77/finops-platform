# Development Log

A running record of work sessions on the FinOps platform: decisions made, what was
built, the reasoning behind it, and next steps. Maintained at the end of each session
so the project's history (and the learning journey) is preserved in the repo itself.

> Format: newest session at the top. Each entry captures **Context → Decisions →
> Actions → Learnings → Next steps**.

---

## Session 5 — 2026-06-05 — Step 5 (API + dashboard + budget alerts)

### Context
Gold rollups exist but nothing exposes them. Step 5 adds the consumption layer: a small
HTTP API to query costs, a dashboard to visualize them, and budgets that turn raw spend
into actionable **alerts** — the part a FinOps stakeholder actually looks at.

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Web framework | **FastAPI** | Async, typed, auto OpenAPI docs at `/docs` |
| DB access | **Read-only** SQLite (`mode=ro`) | API must never mutate landed/gold data |
| App construction | **App factory** `create_app(settings)` | Inject a temp DB in tests cleanly |
| Dashboard | Static HTML + **Chart.js** (CDN) | Zero build step; charts call the JSON API |
| Budgets | Pure functions in `budgets.py` | Unit-testable without a DB; clear OK/WARN/OVER rule |
| Missing gold | Friendly **503** | Tells the user to run aggregation first |

### Actions
- Built `api-service`:
  - `queries.py` — read funcs over gold tables (summary, by service/provider/account/tag, timeseries); `GoldNotReady` guard.
  - `budgets.py` — `status_for()` + `evaluate()` (OK `<80%`, WARN `80–100%`, OVER `>=100%`).
  - `app.py` — FastAPI factory; `/health`, `/api/summary`, `/api/costs/*`, `/api/budgets`, `/` dashboard.
  - `static/index.html` — KPI cards, budget table, trend line, top-services bar, provider doughnut, cost-by-team bar.
  - `config.py` (`API_` settings incl. budgets), `main.py` (uvicorn CLI), `README.md`, `Dockerfile`.
- Wrote tests (9) with `TestClient` over a seeded temp DB + pure budget tests — all passing.
- Ran live against the real DB: total billed **$68,460** flagged **OVER** the $60k budget;
  AWS and GCP OVER, Azure OK. Verified `/health`, `/api/summary`, `/api/costs/by-provider`, `/api/budgets`.
- Wiring: Makefile (`api` target, install/test), `.env.example` (`API_*`), compose `api-service` (port 8000), roadmap/README/manual.

### Learnings (concepts to study)
- **REST API design** + auto-generated OpenAPI/Swagger.
- **App factory + dependency injection** for testable web apps.
- **Read-only DB connections** as a safety boundary.
- **Budget/alerting model**: ratios → states → actionable alerts.
- **Frontend-from-API**: a static page consuming JSON endpoints.

### Next steps
- [ ] (later) anomaly detection; scheduled alert delivery (email/Slack); auth on the API.
- [ ] (later) move storage to a warehouse as volume grows.

---

## Session 4 — 2026-06-05 — Step 4 (transformation / gold aggregations)

### Context
Raw records are landing in SQLite (`billing_records`, the *bronze* layer). Dashboards and
APIs shouldn't `GROUP BY` over raw rows on every read. Step 4 adds a transformation that
pre-computes cost rollups (the *gold* layer) so downstream reads are tiny and fast.

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Where gold lives | Same SQLite DB, `agg_*` tables | Simple now; medallion (bronze→gold) shape stays valid for a warehouse later |
| Rebuild strategy | `CREATE TABLE AS SELECT` (drop + recreate) | Idempotent: re-running never doubles numbers; safe on a schedule |
| Time grain | Usage day, `date(charge_period_start)` | Natural bucket for cost trends |
| Tag allocation | SQLite `json_each` over `tags` | Expands JSON tags into rows → cost by team/environment/cost_center |
| New service vs add-on | New `services/aggregation-service` | Keeps each stage independently runnable/deployable |

### Actions
- Built `aggregation-service`:
  - `transform.py` — four gold rollups (`agg_cost_by_service`, `_account`, `_provider`, `_tag`),
    each `DROP`+`CREATE TABLE AS SELECT`; `rebuild_all()` returns row counts.
  - `config.py` — `AGG_`-prefixed settings (`db_path`).
  - `main.py` — CLI (`--db-path`, `--report`) printing top services + cost-by-team.
  - `README.md`, `Dockerfile`, `pyproject.toml`.
- Wrote tests (4) — correct sums, tag expansion, idempotent rebuild — all passing.
- Ran over the real landed data (86 records): built `agg_cost_by_service=10`,
  `_account=12`, `_provider=3`, `_tag=93`. Verified top services (CloudFront, S3, Lambda)
  and cost-by-team (ml, data, payments…).
- Updated Makefile (`aggregate` target, install/test wiring), `.env.example`, roadmap, README, manual.

### Learnings (concepts to study)
- **Medallion architecture**: bronze (raw) → gold (aggregated) layering.
- **Idempotent transforms**: rebuild-from-scratch is simpler & safer than incremental upserts here.
- **`json_each`**: relational expansion of JSON columns for tag-based cost allocation.
- **Pre-aggregation**: trade write-time compute for cheap read-time queries.

### Next steps
- [ ] Step 5: query API + dashboard (cost trends, top services) + budgets/alerts.
- [ ] (later) move gold to a warehouse/lake as volume grows.

---

## Session 3 — 2026-06-05 — Step 3 (ingestion service + shared contract)

### Context
With the broker backbone running, built the consumer side: a service that reads
`finops.billing.raw`, validates each record, and lands it in queryable storage.
Also promoted the billing model into a shared library (contract-first).

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Shared contract | Promote `FocusBillingRecord` + topics to `libs/common` (`finops-common`) | One authoritative contract; both services import it |
| Landing storage | **SQLite** | Real SQL queries, zero setup; great for a portfolio demo |
| Bad records | **Dead-letter** NDJSON file | Never drop/crash on invalid data; capture for replay |
| Delivery | At-least-once: commit offsets *after* handling | Combined with idempotent upsert = no dupes/loss |
| Idempotency | `INSERT OR REPLACE` on `RecordId` | Re-delivery overwrites instead of duplicating |

### Actions
- Created `libs/common` (`finops_common`): `models.py` (FocusBillingRecord), `topics.py`.
- Refactored `billing-generator` to import the model from `finops_common`; deleted its
  local copy; **8/8 tests still pass** (refactor safety net).
- Built `services/ingestion-service`: `config.py`, `storage/` (`base`, `sqlite_store`,
  `dead_letter`), `consumer.py` (broker-free `process_message` + `BillingConsumer`
  loop with manual commits + graceful shutdown), `main.py` CLI. **5 tests pass.**
- End-to-end run: consumed 86 records Red Panda → SQLite (0 dead-lettered) and queried
  cost by service/provider/charge-category with SQL.
- Updated both Dockerfiles to build from repo root (shared lib) and added
  `ingestion-service` to `docker-compose.yml` (`app` profile).

### Learnings (concepts studied)
- **Consumer groups & offset commits**; `enable.auto.commit=False` + commit-after-handle.
- **At-least-once delivery + idempotent writes** as the dup-safe combination.
- **Validation at the boundary** (`model_validate_json`) turning bytes into trusted models.
- **Dead-letter queue** pattern for resilient pipelines.
- **Shared library / contract-first** to stop model drift across services.

### Next steps
- [ ] Step 4: transformation/aggregation (rollups by account/service/tag/period).
- [ ] Consider a real consumer-group demo (lag, multiple instances).
- [ ] Optionally a small query/report CLI or dashboard.

---

## Session 2 — 2026-06-05 — Step 2 (message broker: Kafka + Red Panda)

### Context
Resumed in teaching mode (step-by-step walkthrough of step 1), then advanced into
step 2: standing up the event backbone. Goal was to make the `broker` sink real and
prove the broker-agnostic design end to end.

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Broker(s) | **Both Kafka and Red Panda**, side by side | Same Kafka protocol; great for learning + comparison |
| Run model | Compose **profiles** (`redpanda`, `kafka`, `app`) | Start only what you need |
| Ports | Red Panda `9092`, Kafka `9094` | Both can run simultaneously without collision |
| Topic | `finops.billing.raw`, **3 partitions**, RF 1 | Demonstrate keying/partitioning/ordering locally |
| Listeners | Dual (EXTERNAL/HOST + INTERNAL/DOCKER) on both brokers | Fix advertised-listener issue for host vs. in-Docker clients |

### Actions
- Installed optional `broker` extra (`confluent-kafka`).
- Reworked `docker-compose.yml`: both brokers behind profiles, distinct ports, named
  volume for Red Panda, Red Panda console on `:8080`.
- Created the topic with 3 partitions on each broker.
- Ran `billing-generator --sink broker` against Red Panda (`:9092`) and Kafka (`:9094`)
  with the **same code** — identical key→partition results on both.
- Verified by consuming records back (`rpk` / `kafka-console-consumer`) and via the
  Red Panda console UI.
- Debugged the **advertised-listener** problem on both brokers; fixed with dual
  named listeners (host vs. docker network).

### Learnings (concepts studied)
- **Broker / topic / partition / offset / consumer group / retention / replication.**
- **Keying** (`BillingAccountId`) → same partition → ordering guarantee (seen live).
- **Advertised listeners**: a broker must advertise an address valid for the *caller's*
  network; multi-network access needs separate named listeners.
- **Protocol compatibility**: Red Panda matched Kafka down to the default partitioner.
- **Durability**: messages persisted across container restart via a named volume.

### Next steps
- [ ] Optionally finish step-1 lessons (scheduler, CLI, tests).
- [ ] Step 3: build a consumer/ingestion service reading `finops.billing.raw`.
- [ ] Consider schema registry decision (follow-up ADR).

---

## Session 1 — 2026-06-04 — Project kickoff & Step 1 (billing generator)

### Context
Started a FinOps SaaS portfolio project. Goal: an event-driven platform, built
incrementally, studying each feature to fully understand it. First deliverable: a
"fake" billing generator that systematically produces synthetic billing data as
input for the future system. A message broker (Kafka or Red Panda) is planned next.

### Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Project location | `Portfolio/FinOPS Project` | Standalone repo, separate from other work |
| Language / stack | Python 3.10+ (`pydantic`, `Faker`) | Matches existing skills |
| Data format | **FOCUS** (FinOps Open Cost & Usage Spec) | Realistic, cross-cloud billing shape |
| Output design | `Sink` abstraction (stdout/file now, broker later) | Broker becomes a drop-in, no rewrite |
| Message broker | **Apache Kafka** (deferred to step 2) | Industry standard, best for learning/portfolio; same protocol as Red Panda so no lock-in |
| Versioning | git, branch `main` | Modern default |

### Actions
- Scaffolded monorepo: `services/`, `libs/`, `schemas/`, `infra/`, `docs/`.
- Built `billing-generator` service:
  - `models.py` — `FocusBillingRecord` (pydantic).
  - `generators/accounts.py` — deterministic catalog of accounts/services/regions.
  - `generators/billing.py` — billing record factory (usage/purchase/tax/credit).
  - `sinks/` — `base`, `stdout`, `file`, `broker` (stub for step 2) + factory.
  - `scheduler.py` — batch + interval loop with graceful shutdown.
  - `main.py` — CLI (`--sink`, `--batch-size`, `--interval`, `--seed`, `--max-batches`).
- Added FOCUS JSON Schema contract, docs (architecture, roadmap, ADRs), Makefile,
  docker-compose (Kafka/Red Panda blocks ready but commented), Dockerfile.
- Wrote tests (8) — all passing. Verified the generator runs and emits valid JSON.
- `git init -b main` + first commit `27c4267` (31 files).

### Learnings (concepts to study)
- **Sink/Strategy pattern**: decoupling *what* we produce from *where* it goes.
- **FOCUS spec**: standardized cloud cost fields (BilledCost vs EffectiveCost vs ListCost).
- **Kafka vs Red Panda**: both speak the Kafka protocol; choice is ops/ecosystem, not code.
- **Monorepo layout**: independently deployable services sharing contracts via `schemas/`.

### Next steps
- [ ] (Recommended) Walk through step-1 code module by module.
- [ ] Push repo to GitHub (portfolio visibility).
- [ ] Step 2: Kafka backbone — implement `broker` sink, enable compose block, define topics.

---

<!--
Template for the next entry (copy above the previous session):

## Session N — YYYY-MM-DD — <title>

### Context
### Decisions
### Actions
### Learnings
### Next steps
-->
