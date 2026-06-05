# Development Log

A running record of work sessions on the FinOps platform: decisions made, what was
built, the reasoning behind it, and next steps. Maintained at the end of each session
so the project's history (and the learning journey) is preserved in the repo itself.

> Format: newest session at the top. Each entry captures **Context → Decisions →
> Actions → Learnings → Next steps**.

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
