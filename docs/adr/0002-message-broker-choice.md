# 2. Message broker choice (Kafka vs Red Panda)

- **Status:** Accepted (step 2 — run both locally)
- **Date:** 2026-06-04 (updated 2026-06-05)

## Context

The platform is event-driven and needs a durable, replayable event backbone between
the billing producer(s) and downstream consumers. The candidates are both
open-source and expose the **Kafka protocol**:

- **Apache Kafka** — the de facto standard; huge ecosystem; KRaft mode removes the
  Zookeeper dependency. Heavier resource footprint.
- **Red Panda** — Kafka-API-compatible, single binary (C++), no JVM, lighter for
  local/dev and small deployments; simpler ops.

## Decision

**Run both, locally, behind Compose profiles.** Rather than pick one, we keep both
available because they share the Kafka protocol and the choice is purely ops/config:

- Producers write through a `Sink` abstraction; the `broker` sink is one implementation.
- The `broker` sink uses **`confluent-kafka`**, verified unchanged against **both**
  Apache Kafka and Red Panda (identical key→partition behavior observed).
- `docker-compose.yml` exposes both via profiles (`redpanda` on `:9092`, `kafka` on
  `:9094`); select a target with `BROKER_BOOTSTRAP_SERVERS`.
- Both use dual named listeners (host vs. docker network) to handle advertised
  addresses correctly for host CLI, in-container tools, and the console.

Production target can be revisited later; nothing in the code depends on it.

## Consequences

- The choice becomes a configuration/ops decision, not a code rewrite.
- We can prototype on Red Panda locally and still target Kafka in production
  (or vice versa) with minimal change.
- If a schema registry is introduced, that becomes a follow-up ADR.
