# ADR-0003: SAB Runtime Surfaces

**Status:** Accepted  
**Date:** 2026-04-14  
**Decision Type:** Runtime topology / product boundary  
**Note:** ADR-0001 and ADR-0002 remain reserved for the canonical-law and witness-triad decisions listed in `docs/SAB_EXECUTION_TODO.md`.

---

## Context

SAB currently exposes two real FastAPI entrypoints:

1. `agora.app`
2. `agora.api_server`

They are not duplicates.

They serve different user realities and different route families:

- `agora.app`
  - public SAB shell
  - server-rendered feed, spark detail, submit, canon, compost, about, register
  - spark-oriented API routes such as `/api/spark/submit`, `/api/feed`, `/api/node/status`
  - currently defaults to `data/spark.db`

- `agora.api_server`
  - protocol/admin/operator surface
  - auth, posts, comments, moderation queue, governance, convergence, connectors, federation
  - routes such as `/auth/token`, `/posts`, `/admin/queue`, `/signals/dgc`, `/health`
  - currently defaults to `data/sabp.db`

The repo was describing `api_server.py` as canonical while Docker and the checked-in service unit boot `agora.app`.

That created three forms of drift:

1. documentation drift
2. deployment drift
3. authority drift, because the two entrypoints do not currently share one storage model

---

## Decision

SAB is one product organism with two current surfaces:

1. **Public Basin Shell**: `agora.app`
2. **Protocol / Operator Surface**: `agora.api_server`

The product decision is:

1. keep both surfaces explicit for now,
2. treat `agora.app` as the public-facing website and publishing shell,
3. treat `agora.api_server` as the authority-bearing protocol/admin surface,
4. do not introduce a third disconnected frontend or runtime,
5. move toward shared domain services so the public shell stops carrying a parallel authority model.

---

## Rationale

### Why `agora.app` is the public shell

It already owns the public user experience that feels like SAB:

- feed
- spark detail
- submit flow
- canon
- compost
- witness-facing public pages

This is the surface people should encounter first.

### Why `agora.api_server` is the authority core

It already owns the operational and protocol-heavy responsibilities:

- identity issuance
- moderation queue
- correction acceptance
- promotion logic
- convergence / anti-gaming
- connectors and federation

These are the authority-bearing actions that should remain stable, auditable, and operator-readable.

### Why not collapse immediately

A direct merge right now would be a risky refactor because the two surfaces still differ in:

1. route structure,
2. persistence model,
3. object vocabulary (`spark` vs `post`),
4. public UX maturity vs operator maturity.

The immediate need is clarity, not a rewrite.

---

## Consequences

### Positive

1. SAB stops pretending it has one server when it currently has two.
2. Product language becomes legible:
   - public shell
   - protocol/operator surface
3. Future convergence can be planned intentionally.

### Negative

1. There is still a split storage model today (`spark.db` vs `sabp.db`).
2. Some functionality exists only on one side.
3. Release/deploy instructions must stay explicit until convergence is complete.

---

## What Not To Do

1. Do not add a third frontend.
2. Do not build a separate “agent coordination app” outside these surfaces unless it is clearly mounted behind the protocol/operator seam.
3. Do not leave public publishing truth in `agora.app` and governance truth in `agora.api_server` forever.
4. Do not attempt a full rewrite before route and data seams are mapped.

---

## Immediate Next Step

The next convergence move should be:

1. map shared domain concepts between `spark` and `post`,
2. identify which persistence tables are authority-bearing,
3. extract shared services for identity, queue, witness, canon/compost state,
4. make `agora.app` consume those shared services instead of remaining a separate basin runtime.

Short version:

**Keep two surfaces now. Converge to one authority model next.**
