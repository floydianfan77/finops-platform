# api-service

Step 5 of the FinOps platform. A small **FastAPI** app that serves the **gold** cost
rollups (built by the aggregation service) as a JSON API, evaluates **budgets** and
**alerts**, and renders a **dashboard** (Chart.js) — the "consumption" layer of the
pipeline.

```
agg_cost_by_* (gold)  ──►  api-service  ──►  JSON API  ──►  dashboard (charts)
                                         └►  budget alerts (OK / WARN / OVER)
```

## Quick start

```bash
cd services/api-service
pip install -e ".[dev]"

# Point it at the database the ingestion + aggregation services wrote
api-service --db-path ../ingestion-service/data/finops.db
# open http://127.0.0.1:8000  (dashboard)  and  http://127.0.0.1:8000/docs  (API)
```

> The gold tables must exist first. From the repo root: `make ingest` then
> `make aggregate` (with a broker running and data produced).

## Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/` | HTML dashboard |
| GET | `/health` | service status + whether gold tables exist |
| GET | `/api/summary` | totals (billed, effective, records, days, providers) |
| GET | `/api/costs/by-service?limit=N` | top services by billed cost |
| GET | `/api/costs/by-provider` | cost per cloud provider |
| GET | `/api/costs/by-account?limit=N` | cost per billing account |
| GET | `/api/costs/by-tag?key=team` | cost allocated by a tag (team/environment/…) |
| GET | `/api/costs/timeseries` | daily total billed cost (trend) |
| GET | `/api/budgets` | budget status + active alerts |

Interactive docs (Swagger UI) are auto-generated at `/docs`.

## Budgets & alerts

Budgets are monthly USD limits configured via env (prefix `API_`):

```bash
API_BUDGET_TOTAL=60000
API_BUDGET_BY_PROVIDER={"AWS": 45000, "Azure": 12000, "GCP": 12000}
API_WARN_RATIO=0.8
```

Each scope is graded **OK** (`< 80%`), **WARN** (`80–100%`), or **OVER** (`>= 100%`).
The evaluation lives in `budgets.py` as pure functions, so it's unit-tested without a DB.

## Design notes

- **Read-only** SQLite access (`file:...?mode=ro`) — the API never writes.
- **App factory** (`create_app(settings)`) so tests inject a temp database.
- Friendly **503** with a "run the aggregation service first" message if gold is missing.
