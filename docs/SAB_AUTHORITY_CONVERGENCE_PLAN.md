# SAB Authority Convergence Plan

**Status:** Active  
**Date:** 2026-04-15  
**Scope:** converge dual-surface SAB toward one authority model without a rewrite

---

## Goal

Keep the current product split:

1. `agora.app` as public basin shell
2. `agora.api_server` as protocol/admin/operator surface

But remove split truth over time so both surfaces read and write one authority-bearing domain model.

---

## Current Reality

### Public Basin Shell

- entrypoint: `agora.app`
- default database: `data/spark.db`
- public routes:
  - `/`
  - `/submit`
  - `/spark/{id}`
  - `/canon`
  - `/compost`
  - `/api/spark/*`
  - `/api/feed*`
  - `/api/node/status`

### Protocol / Operator Surface

- entrypoint: `agora.api_server`
- default database: `data/sabp.db`
- authority-bearing routes:
  - `/auth/*`
  - `/posts`
  - `/posts/{id}/comment`
  - `/comments/{id}/accept-correction`
  - `/admin/*`
  - `/signals/dgc`
  - `/convergence/*`
  - `/health`

### Present Split

The repo currently has:

1. split naming: `spark` vs `post`
2. split storage defaults: `spark.db` vs `sabp.db`
3. split lifecycle semantics: public publishing loop vs protocol queue/governance loop

---

## Convergence Principles

1. no third runtime
2. no full rewrite
3. public shell remains public-first
4. authority-bearing logic moves toward shared services
5. route compatibility should be preserved where practical

---

## Implementation Phases

### Phase 0: Make The Split Explicit

Status: complete in docs and packaging.

Outcomes:

1. runtime surfaces named clearly
2. release smoke path updated
3. one explicit ADR for current topology

### Phase 1: Shared Authority DB Seam

Status: in progress.

Outcome:

1. both surfaces can be pointed at one SQLite file via `SAB_AUTHORITY_DB_PATH`

Files:

1. `agora/config.py`
2. `agora/app.py`
3. tests proving shared path resolution

Acceptance:

1. setting `SAB_AUTHORITY_DB_PATH=/path/shared.db` causes both entrypoints to use the same file
2. existing tests remain green
3. default behavior remains unchanged when the env var is absent

### Phase 2: Shared Domain Mapping

Outcome:

1. documented mapping between:
   - `spark` and `post`
   - challenge and correction
   - canon / compost and moderation status
   - witness records across both surfaces

Files:

1. `docs/SAB_DOMAIN_MAPPING.md`
2. route-level compatibility table

### Phase 3: Shared Services Extraction

Outcome:

1. shared modules for:
   - identity
   - authority queue
   - witness writes
   - canonical publication state
   - compost state

Likely files:

1. `agora/services/identity.py`
2. `agora/services/authority_queue.py`
3. `agora/services/publication_state.py`
4. `agora/services/witness_log.py`

### Phase 4: Public Shell Rebinding

Outcome:

1. `agora.app` renders public UX against shared authority services instead of its own parallel runtime model

### Phase 5: Route And Schema Cleanup

Outcome:

1. legacy route aliases retained only where necessary
2. canonical vocabulary decided and documented
3. duplicated internals removed

---

## First Code Slice

This repo change starts **Phase 1**:

1. add `SAB_AUTHORITY_DB_PATH` as a shared DB override
2. keep `SAB_SPARK_DB_PATH` as the explicit public-shell override
3. prove the seam with a test

This is intentionally small.

It does not solve domain unification yet.
It creates the first safe convergence lever.

---

## Recommended Next Slice After This One

Create `docs/SAB_DOMAIN_MAPPING.md` with an exact mapping for:
This document now exists and should drive the first shared service extraction.
