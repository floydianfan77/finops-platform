# aggregation-service

Step 4 of the FinOps platform. Reads the **raw** `billing_records` table landed by the
ingestion service and builds pre-aggregated **gold** rollup tables for fast analytics
and dashboards — the *gold* layer of a medallion (bronze → gold) architecture.

```
billing_records (bronze)  ──►  aggregation-service  ──►  agg_cost_by_service
                                                          agg_cost_by_account
                                                          agg_cost_by_provider
                                                          agg_cost_by_tag
```

All rollups are bucketed by **usage day** (`date(charge_period_start)`).

## Quick start

```bash
cd services/aggregation-service
pip install -e ".[dev]"

# Build the gold tables into the ingestion DB and print a summary
aggregation-service --db-path ../ingestion-service/data/finops.db --report
```

## Why pre-aggregate?

Running `GROUP BY` over millions of raw rows on every dashboard load is slow. The gold
tables store the answers once, so reads are tiny and fast. The transformation is
**idempotent** (each table is dropped and recreated via `CREATE TABLE AS SELECT`), so it
can be re-run safely on a schedule.

## Gold tables

| Table | Grain |
|-------|-------|
| `agg_cost_by_service`  | usage_date × service |
| `agg_cost_by_account`  | usage_date × billing account |
| `agg_cost_by_provider` | usage_date × provider |
| `agg_cost_by_tag`      | usage_date × tag key/value (team, environment, cost_center) |

## Example query

```bash
sqlite3 ../ingestion-service/data/finops.db \
  "SELECT tag_value AS team, ROUND(SUM(billed_cost),2) cost FROM agg_cost_by_tag \
   WHERE tag_key='team' GROUP BY team ORDER BY cost DESC;"
```
