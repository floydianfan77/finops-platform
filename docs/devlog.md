# Development Log

A running record of work sessions on the FinOps platform: decisions made, what was
built, the reasoning behind it, and next steps. Maintained at the end of each session
so the project's history (and the learning journey) is preserved in the repo itself.

> Format: newest session at the top. Each entry captures **Context → Decisions →
> Actions → Learnings → Next steps**.

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
