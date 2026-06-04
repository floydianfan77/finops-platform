# 1. Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-06-04

## Context

We want a lightweight, durable record of *why* significant choices were made as the
FinOps platform evolves, so future contributors (and future us) understand the
reasoning behind the structure.

## Decision

We will use **Architecture Decision Records (ADRs)** — one short Markdown file per
significant decision, stored in `docs/adr/`, numbered sequentially.

Each ADR captures: Context, Decision, and Consequences, plus a Status
(Proposed / Accepted / Superseded).

## Consequences

- Decisions are discoverable and versioned alongside the code.
- Superseding a decision means adding a new ADR that references the old one,
  rather than rewriting history.
