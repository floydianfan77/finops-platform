# 2. Message broker choice (Kafka vs Red Panda)

- **Status:** Proposed (decision deferred to step 2)
- **Date:** 2026-06-04

## Context

The platform is event-driven and needs a durable, replayable event backbone between
the billing producer(s) and downstream consumers. The candidates are both
open-source and expose the **Kafka protocol**:

- **Apache Kafka** — the de facto standard; huge ecosystem; KRaft mode removes the
  Zookeeper dependency. Heavier resource footprint.
- **Red Panda** — Kafka-API-compatible, single binary (C++), no JVM, lighter for
  local/dev and small deployments; simpler ops.

## Decision

**Deferred.** We will choose during step 2. To avoid lock-in in the meantime:

- Producers write through a `Sink` abstraction; the broker is one implementation.
- The `broker` sink will use **`confluent-kafka`**, which works against **either**
  Kafka or Red Panda unchanged (same protocol).
- `docker-compose.yml` already contains ready-to-enable blocks for both options.

## Consequences

- The choice becomes a configuration/ops decision, not a code rewrite.
- We can prototype on Red Panda locally and still target Kafka in production
  (or vice versa) with minimal change.
- If a schema registry is introduced, that becomes a follow-up ADR.
