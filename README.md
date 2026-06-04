# FinOps Platform

An open-source, event-driven **FinOps** platform for ingesting, processing, and analyzing
cloud cost & usage data. This is a learning/portfolio monorepo built incrementally.

## Vision

```
                +------------------------+
   (synthetic)  |   billing-generator    |   <-- YOU ARE HERE (step 1)
   cost data -->|  (fake billing source) |
                +-----------+------------+
                            |
                            v
                +------------------------+
                |   message broker       |   <-- step 2 (Kafka / Red Panda)
                |  (event backbone)      |
                +-----------+------------+
                            |
              +-------------+-------------+
              v             v             v
        ingestion     transformation   alerting
        services       (FOCUS norm.)   (budgets)
              \             |             /
               v            v            v
                +------------------------+
                |   storage + API + UI   |   <-- later steps
                +------------------------+
```

## Repository layout

```
finops-platform/
├── services/                # Independently deployable services
│   └── billing-generator/   # Step 1: synthetic FOCUS billing producer
├── libs/                    # Shared, importable Python packages
│   └── common/              # Shared event/contract definitions
├── schemas/                 # Language-agnostic data contracts (JSON Schema)
│   └── billing/             # FOCUS-aligned billing record schema
├── infra/                   # Infrastructure (docker, broker, k8s) [grows over time]
├── docs/                    # Architecture, roadmap, ADRs
├── docker-compose.yml       # Local dev environment
└── Makefile                 # Common dev commands
```

## Design principles

1. **Event-driven & broker-agnostic.** Services emit/consume events through a thin
   abstraction so we can choose **Kafka or Red Panda** later without rewrites.
2. **Contract-first.** Data shapes live in `schemas/` (FOCUS-aligned) and are shared
   via `libs/common`, not duplicated per service.
3. **Independently deployable services.** Each folder in `services/` is self-contained
   (own `pyproject.toml`, `Dockerfile`, tests).

## Quick start (step 1)

```bash
cd services/billing-generator
python -m venv .venv && . .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Emit fake billing to your terminal
billing-generator --sink stdout --interval 2 --batch-size 5
```

## Roadmap

See [`docs/roadmap.md`](docs/roadmap.md). Short version:

- [x] **Step 1** — Synthetic billing generator (FOCUS-aligned)
- [ ] **Step 2** — Message broker (Kafka / Red Panda) as the event backbone
- [ ] **Step 3** — Ingestion + storage
- [ ] **Step 4** — Transformation / cost normalization
- [ ] **Step 5** — API + dashboard + budget alerting
