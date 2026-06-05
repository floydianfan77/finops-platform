# FinOps Platform — Project Manual

A complete, study-oriented guide to an **event-driven FinOps platform** built
incrementally in Python. It explains the *why* behind every decision, the
*concepts* you need to understand it, and the *how* to run it yourself.

> **What is this project?** A small but realistic platform that ingests, processes,
> and analyzes cloud **cost & usage** data — the discipline known as **FinOps**
> (Financial Operations). It is built step by step as a learning + portfolio project.

---

## Table of contents

1. [The big picture](#1-the-big-picture)
2. [Architecture at a glance](#2-architecture-at-a-glance)
3. [Technology stack](#3-technology-stack)
4. [Core concepts glossary](#4-core-concepts-glossary)
5. [Repository structure](#5-repository-structure)
6. [Step 1 — Synthetic billing generator](#6-step-1--synthetic-billing-generator)
7. [Step 2 — Message broker (Kafka & Red Panda)](#7-step-2--message-broker-kafka--red-panda)
8. [Step 3 — Ingestion service](#8-step-3--ingestion-service)
9. [Running the whole platform](#9-running-the-whole-platform)
10. [Python & engineering concepts learned](#10-python--engineering-concepts-learned)
11. [Roadmap (what's next)](#11-roadmap-whats-next)
12. [What this project demonstrates](#12-what-this-project-demonstrates)

---

## 1. The big picture

### The real-world problem
Companies run software on the cloud (AWS, Azure, GCP). Every resource — servers,
databases, storage — costs money, and providers return enormous, messy **billing
files**. **FinOps** is the practice of understanding and controlling that spend, by
answering questions like:

- *Why did our bill jump 40% last week?*
- *Which team or service is the most expensive?*
- *Are we about to blow our budget?*

This platform builds the machinery to answer those questions.

### Why "event-driven"?
There are two ways to move data through a system:

| Style | How it works | Problem |
|-------|--------------|---------|
| **Request/response (batch)** | Components call each other directly | Tight coupling; one failure cascades; hard to scale |
| **Event-driven** | Components communicate through a **message broker** (a conveyor belt) | Decoupled, resilient, scalable |

**The conveyor-belt metaphor:** a *producer* drops items (events) on a belt and walks
away. *Consumers* pick items off the belt at their own pace. Producers and consumers
never talk directly — they only know about "the belt." This **decoupling** is the
entire point:

- Add new consumers without touching the producer.
- One consumer crashing doesn't stop the producer.
- Fast producers and slow consumers coexist (the belt **buffers**).
- The belt **remembers** events (durability), so consumers can replay history.

The crucial twist: a Kafka-style belt is a **replayable log**, not a one-time mailbox.
Reading an event does **not** delete it — many independent consumers can read the same
events, and new services can re-read history from the beginning.

---

## 2. Architecture at a glance

```
                +------------------------+
   (synthetic)  |   billing-generator    |   Step 1  (producer)
   cost data -->|  (fake billing source) |
                +-----------+------------+
                            | emits FOCUS billing records (JSON)
                            v
                +------------------------+
                |   message broker       |   Step 2  (event backbone)
                |  Kafka  +  Red Panda   |   topic: finops.billing.raw (3 partitions)
                +-----------+------------+
                            | streams events
                            v
                +------------------------+
                |   ingestion-service    |   Step 3  (consumer)
                |  validate + persist    |
                +-----+------------+-----+
                      |            |
                valid |            | invalid
                      v            v
              +-------------+  +------------------+
              |   SQLite    |  | dead_letter.ndjson|
              | billing_    |  | (quarantined bad  |
              | records     |  |  records)         |
              +------+------+  +------------------+
                     |
                     v
            SQL analytics (cost by service / provider / team / period)
            Step 4 (aggregation) and Step 5 (API + dashboard) build on this.
```

### Data flow in one sentence
The **generator** invents realistic cloud charges and publishes them to a **broker**;
the **ingestion service** consumes them, **validates** each against a shared contract,
and **lands** valid records in **SQLite** (sending bad ones to a **dead-letter** file),
where they can be analyzed with SQL.

---

## 3. Technology stack

| Concern | Choice | Why |
|---------|--------|-----|
| Language | **Python 3.10+** | Readable, batteries-included |
| Data modeling / validation | **pydantic v2** | Typed models with automatic validation + JSON |
| Settings | **pydantic-settings** | 12-factor config from env vars |
| Fake data | **Faker** | Realistic company names, etc. |
| Data format | **FOCUS** spec | Industry-standard cloud cost & usage shape |
| Broker | **Apache Kafka** + **Red Panda** | Same protocol; both run side by side |
| Kafka client | **confluent-kafka** | Works unchanged against Kafka or Red Panda |
| Storage | **SQLite** | Real SQL, zero setup |
| Containers | **Docker / Docker Compose** | Reproducible local environment |
| Testing | **pytest** | Fast, convention-based |
| Lint/format | **ruff** | Fast, all-in-one |

---

## 4. Core concepts glossary

### Software design concepts

- **Class vs. object (instance)** — a class is a *blueprint*; an object is a *thing built
  from it*. `FocusBillingRecord` is a class; each generated charge is an object.
- **Method** — a function that belongs to a class (an action an object can perform).
- **Sink** — a data-flow metaphor: the *destination* where data drains to (screen,
  file, broker). Opposite of a *source*.
- **Contract / interface** — a promise about *what methods* something must have, without
  saying how they work (like a wall socket: any matching plug gets power).
- **Abstract base class (`abc.ABC`) / abstract method (`@abstractmethod`)** — how Python
  writes a contract: a template that *cannot* be instantiated and that forces subclasses
  to implement specific methods.
- **Factory** — a function whose job is to build and return the right object, so callers
  don't need construction details (e.g. `build_sink("file")` returns a `FileSink`).
- **Strategy pattern** — a family of interchangeable behaviors behind one contract,
  chosen at runtime (the sinks).
- **Polymorphism** — different objects responding to the same call in their own way
  (`sink.emit(record)` behaves differently per sink, with no `if`-checks).
- **Inheritance / subclass / override** — building a class on top of another, reusing its
  behavior and replacing parts as needed.
- **Dependency injection** — passing a component its collaborators (the scheduler is
  *given* a generator and a sink, instead of creating them itself).

### Event-streaming concepts

- **Producer** — publishes events to the broker (the billing generator).
- **Consumer** — reads events to do work (the ingestion service).
- **Broker** — the server(s) that store and serve the event log (Kafka / Red Panda).
- **Topic** — a named stream/belt (`finops.billing.raw`).
- **Partition** — a topic is split into ordered sub-logs for parallelism. Order is
  guaranteed *within* a partition, not across partitions.
- **Key → partition** — a record's key decides its partition (we key by
  `BillingAccountId`, so one account's records stay ordered together).
- **Offset** — a record's position number within its partition (never changes).
- **Consumer group** — a team of consumers sharing partitions; different groups read the
  same events independently.
- **Retention** — how long events stay on the log (enables replay).
- **Replication** — copies of partitions across brokers (durability).
- **Advertised listeners** — the address a broker tells clients to reach it at; needs to
  be correct for the caller's network (host vs. inside Docker).
- **At-least-once delivery** — a record may be delivered more than once; combine with
  **idempotent** writes so duplicates don't double-count.
- **Dead-letter queue (DLQ)** — where invalid/unprocessable messages go, so they're
  neither dropped nor allowed to crash the pipeline.

---

## 5. Repository structure

A **monorepo** (many projects in one git repository):

```
FinOPS Project/
├── services/                     # Independently deployable programs
│   ├── billing-generator/        # Step 1: synthetic FOCUS billing producer
│   │   ├── src/billing_generator/
│   │   │   ├── config.py          # settings (env vars)
│   │   │   ├── generators/        # accounts catalog + billing factory
│   │   │   ├── sinks/             # stdout | file | broker (+ factory)
│   │   │   ├── scheduler.py       # the timer loop
│   │   │   └── main.py            # CLI
│   │   └── tests/
│   └── ingestion-service/        # Step 3: consumer -> validate -> SQLite
│       ├── src/ingestion_service/
│       │   ├── config.py
│       │   ├── storage/           # base | sqlite_store | dead_letter
│       │   ├── consumer.py        # validation + consume loop
│       │   └── main.py            # CLI
│       └── tests/
├── libs/
│   └── common/                   # finops_common: SHARED contract
│       └── src/finops_common/
│           ├── models.py          # FocusBillingRecord (authoritative)
│           └── topics.py          # canonical topic names
├── schemas/billing/              # JSON Schema (language-neutral contract)
├── infra/                        # infrastructure notes (grows over time)
├── docs/                         # architecture, roadmap, ADRs, this manual
├── docker-compose.yml            # brokers + services (profiles)
└── Makefile                      # common dev commands
```

**Key conventions**
- `services/` = things you *run*; `libs/` = things you *import*; `schemas/` = contracts.
- **src layout** (`src/<package>/`) forces installing the package, so tests run against
  the installed version (like a real user).
- Folder names use hyphens (`billing-generator`); Python package names use underscores
  (`billing_generator`), because `-` is invalid in Python identifiers.
- **Contract-first**: the billing record is defined **once** in `libs/common` and
  imported by every service, so the shape never drifts.

---

## 6. Step 1 — Synthetic billing generator

**Goal:** because we have no real cloud account, we *fake* a realistic, continuous source
of cloud-cost data, shaped like a genuine bill.

### 6.1 The data model (`finops_common/models.py`)
A **pydantic model** defines one billing record as a typed "form." It gives us free
**validation** (wrong types are rejected) and **serialization** (to/from JSON).

```python
class FocusBillingRecord(BaseModel):
    RecordId: str                       # required
    ProviderName: str
    PublisherName: str | None = None    # optional (may be empty)
    BillingAccountId: str
    BillingPeriodStart: datetime        # the invoice cycle (e.g. the month)
    BillingPeriodEnd: datetime
    ChargePeriodStart: datetime         # when THIS usage happened (e.g. one hour)
    ChargePeriodEnd: datetime
    ServiceName: str                    # "Amazon EC2"
    ServiceCategory: str                # "Compute"
    ChargeCategory: str                 # Usage | Purchase | Tax | Credit
    RegionId: str
    ResourceId: str
    PricingQuantity: float = Field(ge=0) # guardrail: must be >= 0
    PricingUnit: str
    ListUnitPrice: float = Field(ge=0)
    ListCost: float                     # sticker price (quantity * unit price)
    EffectiveCost: float                # real cost after discounts
    BilledCost: float                   # what was invoiced
    BillingCurrency: str
    Tags: dict[str, str] = Field(default_factory=dict)  # team/env/cost_center
```

**FOCUS concepts modeled here**
- **Two time windows:** `BillingPeriod` (the monthly invoice) vs `ChargePeriod` (when a
  specific charge happened). One monthly bill contains thousands of tiny charge periods.
- **Three costs:** `ListCost` (sticker), `EffectiveCost` (after discounts),
  `BilledCost` (invoiced). FinOps analysis lives in the gaps between them.
- **Tags:** key/value labels for cost allocation (which team/environment).

> `Field(default_factory=dict)` (not `= {}`) gives each record its **own** empty dict,
> avoiding the classic shared-mutable-default bug.

### 6.2 The generators
- **`accounts.py` — the catalog.** Builds a **stable** cast of accounts, priced services,
  and regions **once** (seeded for reproducibility). Mirrors reality: your account list is
  stable month to month. Uses `@dataclass`, `random.Random(seed)`, and `Faker`.
- **`billing.py` — the factory.** On demand, picks from the catalog and assembles a
  `FocusBillingRecord` with fresh values: random quantity, computed `ListCost`, a discount
  for `EffectiveCost`, a `uuid4` id, and a 1-hour charge window ending "now". Charge
  categories follow a realistic distribution (≈88% Usage, plus Purchase/Tax/Credit); a
  `Credit` is **negative**, a `Tax` has no quantity.

### 6.3 The sinks (Strategy pattern)
`Sink` is the **contract** (`abc.ABC` with abstract `emit`). Implementations:

| Sink | Destination |
|------|-------------|
| `StdoutSink` | prints JSON lines to the screen |
| `FileSink` | appends to an NDJSON file (auto-creates folder, flush/close) |
| `BrokerSink` | publishes to Kafka/Red Panda (keyed by account, idempotent) |

`build_sink(settings)` is the **factory** that returns the chosen one. The generator only
ever calls `sink.emit(record)` — **polymorphism** means it never needs to know which sink
it has. Adding a new destination = one new class, zero changes elsewhere.

### 6.4 The scheduler (`scheduler.py`)
The orchestrator: every `interval_seconds`, generate `batch_size` records and emit them,
until stopped. Features:
- **Graceful shutdown** via OS **signals** (`SIGINT`/Ctrl+C, `SIGTERM`): a handler flips a
  `self._stop` flag; the loop finishes cleanly and flushes — no lost data.
- **Context manager** (`with self._sink:`) guarantees flush + close on exit (even on
  error).
- `--max-batches` stops after N; otherwise runs until interrupted.

### 6.5 The CLI (`main.py`)
Uses **argparse** to define flags (`--sink`, `--batch-size`, `--interval`, `--seed`,
`--max-batches`, `--file-path`). Settings precedence:

```
built-in defaults  <  environment variables (BILLING_*)  <  CLI flags
```

`if __name__ == "__main__": main()` lets the file be imported by tests without running.
The terminal command `billing-generator` exists because of `[project.scripts]` in
`pyproject.toml`.

### 6.6 Tests
8 pytest tests cover determinism, valid records, batch size & unique IDs, JSON
round-trips, valid charge categories, the file sink (using the `tmp_path` fixture), and
the factory (including that bad input **raises** correctly).

### 6.7 Example output (one record, formatted)
```json
{
  "RecordId": "3c52d0bd-...",
  "ProviderName": "GCP",
  "BillingAccountId": "acct-8479902459",
  "BillingPeriodStart": "2026-06-01T00:00:00Z",
  "BillingPeriodEnd":   "2026-07-01T00:00:00Z",
  "ChargePeriodStart":  "2026-06-05T18:14:28Z",
  "ChargePeriodEnd":    "2026-06-05T19:14:28Z",
  "ServiceName": "Google BigQuery",
  "ServiceCategory": "Analytics",
  "ChargeCategory": "Usage",
  "PricingQuantity": 603.77, "PricingUnit": "TB-Scanned",
  "ListCost": 924.66, "EffectiveCost": 824.70, "BilledCost": 824.70,
  "BillingCurrency": "USD",
  "Tags": {"environment": "prod", "team": "growth", "cost_center": "cc-180"}
}
```

---

## 7. Step 2 — Message broker (Kafka & Red Panda)

**Goal:** introduce the event backbone between producer and consumers.

### 7.1 Kafka in plain terms
Kafka is a **distributed, append-only log**: a notebook you can only add to the end of,
copied across machines for safety. Vocabulary (see glossary): **broker, topic, partition,
offset, consumer group, retention, replication**.

### 7.2 Kafka vs Red Panda
Both speak the **same Kafka protocol**, so your code is identical; only the engine and
operations differ.

| Aspect | Apache Kafka | Red Panda |
|--------|--------------|-----------|
| Built in | Java/Scala (JVM) | C++ (single binary) |
| Footprint (local) | Heavier | Lighter, faster start |
| Ecosystem | The industry standard | Smaller, drop-in compatible |
| Console | Add separately | Ships an easy web console |
| Your code (`confluent-kafka`) | **Same** | **Same** |

**Decision (ADR-0002):** run **both** locally behind Compose profiles; choosing between
them is a *config* change (`bootstrap.servers`), not a code change.

### 7.3 Topic & partitioning
- Topic: `finops.billing.raw`, **3 partitions**.
- Records keyed by `BillingAccountId` → a given account always lands on the **same**
  partition → its records stay **in order**. Different accounts spread across partitions
  for parallelism. (Verified live: Kafka and Red Panda assigned identical key→partition.)

### 7.4 The advertised-listener lesson
A broker tells clients "reach me at this address." When clients live in different network
contexts (your host vs. inside Docker), you need **separate named listeners**:

- **Red Panda:** `EXTERNAL` advertised as `localhost:9092` (host), `INTERNAL` as
  `redpanda:9093` (other containers, e.g. the console).
- **Kafka:** `HOST` advertised as `localhost:9094`, `DOCKER` as `kafka:9092`.

This is one of the most common real-world Kafka stumbling blocks.

### 7.5 Ports
| Service | Host port |
|---------|-----------|
| Red Panda (Kafka API) | `9092` |
| Apache Kafka (Kafka API) | `9094` |
| Red Panda Console (web UI) | `8080` |

---

## 8. Step 3 — Ingestion service

**Goal:** consume raw events, validate them, and land them where they can be analyzed.

### 8.1 What it does
```
finops.billing.raw  ──►  ingestion-service  ──►  SQLite (billing_records)
                              │
                              └── invalid ──►  dead_letter.ndjson
```

### 8.2 The consumer loop (`consumer.py`)
- Creates a `confluent_kafka.Consumer` with a **`group.id`**,
  `auto.offset.reset=earliest`, and **`enable.auto.commit=False`** (we commit manually).
- `subscribe()` to the topic, then loop: `poll()` → handle → **commit after handling**.
- The per-message logic is a **broker-free** function, `process_message`, so it can be
  unit-tested with plain bytes.

### 8.3 Validation at the boundary
```python
record = FocusBillingRecord.model_validate_json(value)  # bytes -> trusted object
```
If the bytes aren't valid JSON, or the shape is wrong (missing required fields, bad
types), pydantic raises — and the message is **dead-lettered** instead of crashing the
service.

### 8.4 At-least-once + idempotency
- Offsets are committed **only after** a message is handled → no message is lost if the
  service dies mid-processing (it may be re-delivered).
- The SQLite write uses `INSERT OR REPLACE` keyed on `RecordId` → a re-delivered record
  **overwrites** rather than duplicating. Together: **no loss, no double-counting.**

### 8.5 Storage (`storage/`)
- `Store` (abstract, mirrors the `Sink` idea) → `SQLiteStore` (creates the
  `billing_records` table, idempotent upsert) and `DeadLetterWriter` (appends bad payloads
  + error + original bytes to NDJSON).

### 8.6 The dead-letter demo (proven)
Injecting 2 bad messages among 88 produced: **stored 86, dead-lettered 2, 0 crashes**.
The DLQ file captured each bad payload with its error (e.g. "16 issues" for a record
missing all required fields) and the original bytes for replay.

### 8.7 Example analytics (SQL over landed data)
```
TOTAL records: 86 | TOTAL billed: USD 68,460.41

Top services:   Amazon CloudFront $14,840  | Amazon S3 $11,830 | AWS Lambda $9,039
By provider:    AWS $47,058 | GCP $12,372 | Azure $9,029
By category:    Usage (75) $65,007 | Tax (4) $2,819 | Purchase (4) $1,755 | Credit (3) -$1,121
```
Note credits are **negative** — the Step-1 logic survives all the way to analytics.

---

## 9. Running the whole platform

> Prerequisites: Python 3.10+, Docker Desktop running. Commands shown for Windows
> PowerShell; adjust paths/venv activation for macOS/Linux.

### 9.1 Install (editable)
```powershell
# from the repo root
pip install -e libs/common
cd services/billing-generator ; pip install -e ".[dev,broker]" ; cd ../..
cd services/ingestion-service ; pip install -e ".[dev]" ; cd ../..
```
(Or, where `make` is available: `make install`.)

### 9.2 Start a broker
```powershell
# Red Panda (has a web console at http://localhost:8080)
docker compose --profile redpanda up -d

# Apache Kafka (host port 9094)
docker compose --profile kafka up -d

# Both at once
docker compose --profile redpanda --profile kafka up -d
```

### 9.3 Create the topic (3 partitions)
```powershell
# Red Panda
docker exec finops-redpanda rpk topic create finops.billing.raw --partitions 3 --replicas 1

# Kafka (note: use the in-Docker listener kafka:9092)
docker exec finops-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 `
  --create --topic finops.billing.raw --partitions 3 --replication-factor 1
```

### 9.4 Produce billing records
```powershell
cd services/billing-generator

# To the screen (deterministic with a seed)
billing-generator --sink stdout --batch-size 3 --seed 42 --max-batches 1

# Stream to Red Panda (default broker localhost:9092)
billing-generator --sink broker --batch-size 4 --interval 2 --max-batches 20

# Stream to Kafka instead
$env:BROKER_BOOTSTRAP_SERVERS="localhost:9094"; billing-generator --sink broker --max-batches 5
```

### 9.5 Consume into SQLite
```powershell
cd services/ingestion-service
ingestion-service --from-beginning --max-messages 100        # Red Panda
# or:  ingestion-service --bootstrap-servers localhost:9094 --from-beginning
```

### 9.6 Query the results
```powershell
python -c "import sqlite3; c=sqlite3.connect('./data/finops.db'); print(c.execute('SELECT service_name, ROUND(SUM(billed_cost),2) FROM billing_records GROUP BY service_name ORDER BY 2 DESC').fetchall())"
```

### 9.7 Inspect visually
Open the Red Panda console at **http://localhost:8080** → Topics →
`finops.billing.raw` to browse messages, keys, partitions, and offsets.

### 9.8 Run tests
```powershell
cd services/billing-generator ; python -m pytest -q ; cd ../..
cd services/ingestion-service ; python -m pytest -q ; cd ../..
```

### 9.9 Shut down
```powershell
docker compose --profile redpanda --profile kafka down      # stop (keep data)
docker compose --profile redpanda --profile kafka down -v   # stop + wipe broker data
```

---

## 10. Python & engineering concepts learned

A checklist of what this project teaches, by area.

**Python language**
- Type hints (`str`, `float`, `datetime`, `dict[str, str]`, `X | None`)
- Classes, `__init__`, `__post_init__`, methods, `self`
- `@dataclass` vs pydantic `BaseModel`
- List/set/dict comprehensions; tuple unpacking
- f-strings; `dict.get(key, default)`; `setattr`
- `lambda`; keyword-only arguments (`*`)
- Context managers (`with`, `__enter__`/`__exit__`)
- `try/except/else`; raising and testing exceptions
- `if __name__ == "__main__"`
- `random.Random(seed)` reproducibility; `uuid`; `datetime`/`timedelta`/`timezone`

**Design & architecture**
- Sink/Strategy pattern; factories; polymorphism; inheritance
- Abstract base classes / contracts
- Dependency injection
- Contract-first shared library (no model drift)
- Monorepo + src layout + packaging (`pyproject.toml`, `[project.scripts]`)
- 12-factor configuration (env vars + CLI precedence)

**Data & streaming**
- The FOCUS billing spec (periods, three costs, tags)
- JSON Schema as a language-neutral contract
- Kafka/Red Panda: producers, consumers, topics, partitions, offsets, keys,
  consumer groups, retention, replication
- Advertised listeners (host vs. Docker networking)
- At-least-once delivery + idempotent writes
- Dead-letter queue pattern
- SQLite persistence and SQL aggregation

**Tooling & ops**
- pytest (fixtures, assertions, failure-path tests)
- Docker & Docker Compose (profiles, volumes, build contexts)
- Git with Conventional Commits
- ADRs (Architecture Decision Records) and a development log

---

## 11. Roadmap (what's next)

| Step | Status | Summary |
|------|--------|---------|
| 1 — Billing generator | ✅ | Synthetic FOCUS records, pluggable sinks |
| 2 — Message broker | ✅ | Kafka **and** Red Panda; topic + partitioning |
| 3 — Ingestion + storage | ✅ | Consume → validate → SQLite (+ dead-letter) |
| 4 — Transformation | ⏳ | Pre-aggregated rollups (cost by service/account/tag/period) — the *gold* layer of a medallion architecture |
| 5 — API + UI + alerting | ⏳ | Query API, dashboard (trends, top services, anomalies), budgets & alerts |

---

## 12. What this project demonstrates

For a portfolio, this project shows the ability to:

- **Design an event-driven system** with proper decoupling (producer/broker/consumer).
- **Apply software design patterns** (Strategy, Factory, contracts) for extensible code.
- **Work with Kafka-compatible brokers**, including real operational gotchas
  (advertised listeners, partitioning, consumer groups).
- **Build resilient data pipelines** with validation, idempotency, and dead-lettering.
- **Model real-world data** to an industry standard (FOCUS) with a language-neutral
  contract (JSON Schema) shared across services.
- **Engineer for quality**: tests, configuration, Docker, a monorepo, ADRs, and a
  written development log.
- **Learn iteratively and document the journey** — each step is shippable and explained.

---

*This manual reflects the project through Step 3. See `docs/devlog.md` for the
session-by-session history and `docs/roadmap.md` for the live roadmap.*
