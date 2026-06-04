# Architecture

## Overview

The FinOps platform is an **event-driven** system. Producers emit cost/usage events,
a **message broker** carries them, and a set of consumers ingest, transform, store,
and surface the data.

This document grows with the project. Today it covers **step 1** and the contracts
that keep later steps decoupled.

## Components

| Component           | Status   | Responsibility                                        |
|---------------------|----------|-------------------------------------------------------|
| `billing-generator` | ✅ step 1 | Produce synthetic, FOCUS-aligned billing records      |
| message broker      | 🔜 step 2 | Durable event backbone (Kafka **or** Red Panda)       |
| ingestion           | ⏳ later  | Consume events, validate, land raw data               |
| transformation      | ⏳ later  | Normalize to FOCUS, enrich, aggregate                 |
| storage             | ⏳ later  | Warehouse / lake for cost data                        |
| api + ui            | ⏳ later  | Query, dashboards, budgets & alerts                   |

## Key decisions

- **Contract-first.** The billing event shape is defined once in
  [`../schemas/billing/focus_billing_record.schema.json`](../schemas/billing/focus_billing_record.schema.json)
  and mirrored by a typed model in `libs/common`. Every service depends on the
  contract, never on another service's internals.
- **Broker abstraction.** Producers write to a `Sink` interface. `stdout` and `file`
  sinks exist now; a `broker` sink lands in step 2. Swapping Kafka ↔ Red Panda is a
  config change, not a code change (both speak the Kafka protocol).
- **FOCUS alignment.** We model synthetic data on the FinOps Open Cost & Usage
  Specification so downstream logic matches real-world AWS/GCP/Azure exports.

## Event flow (target)

```
billing-generator --> [sink: broker] --> topic: finops.billing.raw
                                              |
                                  ingestion consumer(s)
                                              |
                                  topic: finops.billing.normalized
                                              |
                                   storage + analytics
```

## Why a broker (step 2)

- **Decoupling**: producers and consumers scale and deploy independently.
- **Buffering**: absorbs spikes in billing volume.
- **Replayability**: reprocess history when transformation logic changes.
- **Fan-out**: many consumers (storage, alerting, analytics) read the same stream.

Red Panda and Kafka are both candidates; both expose the Kafka API, so the
`broker` sink (via `confluent-kafka`) works against either.
