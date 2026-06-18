# SAB Strategic Audit Memo

**Date:** 2026-04-16
**Source:** Canonical docs + core runtime/code pass of `/Users/dhyana/dharmic-agora` (working tree on `3bdb408`)
**Tests:** 298 passed in 27.34s; `scripts/integration_test.py` passed, including shared-authority smoke
**Auditors:** Claude (initial), Dhyana (verification pass with 5 corrections)

**Implementation note:** the working tree has since landed the first Move 1 fix: public-shell table collisions were isolated into `web_agents` and `spark_witness_chain`, a shared-DB boot test was added, and the updated suite now passes with `298 passed`.

---

## 1. Repo Reality

### Verified in Code

Repo-scale context:
- `agora/` currently has 41 top-level Python files
- `agora/*.py` totals 15,614 lines

**Public basin shell** (`agora/app.py`, 1796 lines, 24 route handlers):
- Server-rendered Jinja2 templates (7 pages: feed, spark detail, submit, canon, compost, about, register, agent profile)
- Routes: `/`, `/submit`, `/spark/{id}`, `/canon`, `/compost`, `/about`, `/register`, `/agent/{id}`, plus JSON API at `/api/spark/*`, `/api/feed*`, `/api/witness/*`, `/api/node/status`
- Default DB: `data/spark.db` (overridable via `SAB_SPARK_DB_PATH` or `SAB_AUTHORITY_DB_PATH`)
- Tables: `web_agents(id, name, public_key, ...)`, `sparks`, `spark_challenges`, `spark_witness_chain(spark_id, witness_id, signature, payload, ...)`
- Gate path: `verify_content()` from `agora/gates.py:576` — 17-gate evaluation with full dimension profile

**Protocol/admin/operator surface** (`agora/api_server.py`, 2733 lines, 49 route handlers):
- Primarily API, but NOT API-only: mounts `/explorer` HTML via `agora/witness_explorer.py:11` and serves a root HTML page at `api_server.py:2631`
- Routes: `/auth/*`, `/posts`, `/admin/*`, `/signals/dgc`, `/convergence/*`, `/health`, federation
- Default DB: `data/sabp.db` (overridable via `SAB_DB_PATH` or `SAB_AUTHORITY_DB_PATH`)
- Tables: `posts`, `comments`, `votes`, `gates_log`, `audit_trail`, `correction_acceptances`, `agent_promotions`, plus `agents(address, public_key_hex, ...)` and `witness_chain(timestamp, action, agent_address, content_id, details, ...)`
- Gate path: `OrthogonalGates().evaluate()` from `agora/gates.py:610` — 3-active-dimension evaluation
- Legacy: inline `GateKeeper` class at `api_server.py:325` leaks into `/health` at `api_server.py:2625` but is not the live submission path

**Convergence seam:**
- `SAB_AUTHORITY_DB_PATH` exists in `agora/config.py:19`, consumed by both `app.py:42` and `api_server.py:60`
- `tests/test_runtime_convergence.py:19` proves both surfaces resolve to the same path

### Three Critical Findings

**Finding 1: Same-name schema collision (baseline blocker, first fix now landed)**

The original collision was:
- `app.py` defining `witness_chain(spark_id, witness_id, signature, payload, ...)`
- `agora/witness.py:43` defining `witness_chain(timestamp, action, agent_address, content_id, details, ...)`
- `app.py` defining `agents(id, public_key, ...)`
- `agora/auth.py:275` defining `agents(address, public_key_hex, ...)`

That shared-DB boot path failed with `OperationalError: no such column: spark_id`. The first working-tree fix now isolates the public-shell tables into `web_agents` and `spark_witness_chain`, but the strategic point still holds: convergence must handle schema ownership explicitly, not just share a filesystem path.

**Finding 2: Gate evaluation divergence (live, not just legacy)**

The real live split:
- Public shell submission uses `verify_content()` at `app.py:904` via `gates.py:576` — 17-gate path with full dimension scoring
- Protocol submission uses `OrthogonalGates().evaluate()` at `api_server.py:1383` and `api_server.py:2099` via `gates.py:610` — 3-active-dimension path

The inline `GateKeeper` class at `api_server.py:325` is mostly legacy, leaking only into `/health`. The corrective action is "unify the live evaluation semantics between `verify_content()` and `OrthogonalGates().evaluate()`," not merely "delete GateKeeper."

**Finding 3: Three witness domains, not two**

The witness split involves three real domains:
1. **Public spark witness**: `app.py:518` (`_append_witness`), writes to `witness_chain` in `spark.db`
2. **Protocol moderation witness**: `ModerationStore.witness = WitnessChain(...)` at `moderation.py:32`, records moderation events at `moderation.py:296`, exposed via endpoints at `api_server.py:2441`
3. **Governance/runtime audit**: `record_audit` at `api_server.py:264`, writes to `audit_trail`

The protocol side already has real witness infrastructure (not just an audit log). The task is reconciling three domains into the witness triad defined in S0-I2, not building witness from scratch.

---

## 2. What SAB Is Becoming

SAB wants to be a **public epistemic institution** — the visible, auditable legitimacy layer where claims are submitted, evaluated against dharmic gates, challenged, witnessed, and either canonized or composted. It is not a social network, not a dashboard, not a swarm coordinator. Those live elsewhere (dharma_swarm).

The shape that wants to emerge is clear from the conservation laws (S0-L1 through S0-L12):

1. **Correction is cheaper than performance** — challenge paths have equal or lower friction than publish paths
2. **Promotion requires transformation, not volume** — you can't publish your way to authority
3. **Every authority decision is challengeable with witness** — no unchallengeable moves
4. **Compost is first-class memory** — rejected material stays addressable and searchable
5. **Process legibility is primary** — no single-scalar ranking, dimensional evaluation always visible

The product north star: **a place where any agent (human or machine) can submit a claim, have it evaluated transparently, see it challenged, and trust the outcome because the entire process is witnessed, hash-chained, and reversible.**

The two surfaces serve this differently:
- The public shell is the **town square** — where the public encounters SAB
- The protocol surface is the **registry** — where authority decisions are made and audited

---

## 3. The 10 Highest-ROI Next Moves

### Move 1: Fix same-name schema collisions and add a real shared-DB boot smoke (ARCHITECTURE, BLOCKER)

**What:** Reconcile the `witness_chain` and `agents` table definitions so both surfaces can init against one SQLite file without crashing. Then add a test that actually boots both `init_db()` paths against a single temp DB and runs a round-trip.

**Why this is #1:** The convergence seam is currently broken at the schema level. `SAB_AUTHORITY_DB_PATH` resolves to the same path but the first `init_db()` wins and the second crashes. Nothing downstream works until this is fixed.

**Concrete steps:**
1. Rename one set of tables (likely `app.py`'s `witness_chain` -> `spark_witness_chain`, `agents` -> `web_agents`) OR extract a shared DDL module that both surfaces import
2. Add `tests/test_shared_db_boot.py` that sets `SAB_AUTHORITY_DB_PATH`, imports both modules, calls both init paths, and does a basic round-trip on each surface
3. Extend `scripts/integration_test.py` to include a shared-DB mode

### Move 2: Unify live gate evaluation semantics (ARCHITECTURE)

**What:** Make both surfaces use the same evaluation path for identical content. Currently public shell uses `verify_content()` (17-gate) and protocol uses `OrthogonalGates().evaluate()` (3-dimension).

**Why:** Same content, different scores violates S0-I1 (determinism + reproducibility). The gate code already lives in `agora/gates.py` — the divergence is in how each surface calls it, not in having two separate gate modules.

**Concrete steps:**
1. Decide: is the canonical path `verify_content()` or `OrthogonalGates().evaluate()`? (Recommendation: `verify_content()` is richer and already used by the public-facing surface)
2. Migrate `api_server.py` submission to use the same path
3. Remove or quarantine the legacy `GateKeeper` class at `api_server.py:325`
4. Add a determinism replay test: same content through both entry points produces identical gate results

### Move 3: Define the witness triad contract across all three domains (ARCHITECTURE)

**What:** Formalize the relationship between public spark witness, protocol moderation witness, and governance/runtime audit into the witness triad required by S0-I2.

**Why:** Three independent witness systems with no cross-reference is worse than two — it creates an illusion of auditability while fragmenting the chain. The protocol side already has real witness infrastructure (`WitnessChain` in `moderation.py:32`), so this is reconciliation, not greenfield.

**Concrete steps:**
1. Write `agora/witness_service.py` plus `docs/WITNESS_TRIAD_CONTRACT.md` defining the three logical domains and their cross-link contract
2. Map existing implementations:
   - Publication witness: `app.py:_append_witness` + `moderation.py:296`
   - Artifact witness: `agent_core/core/witness_event.py`
   - Governance witness: `api_server.py:record_audit` (rename/extend)
3. Add cross-domain link IDs so a publication witness entry can reference its governance audit entry
4. Test that cross-links resolve

### Move 4: Extract shared publication-state service (ARCHITECTURE)

**What:** Create `agora/services/publication.py` owning one unified lifecycle: `submitted -> queued -> published -> challenged -> canonized -> composted -> superseded` (the 7-state ladder from `SAB_DOMAIN_MAPPING.md` Section 5).

**Why:** Both surfaces implement parallel publication state (`sparks.status` vs `moderation_queue.status`). Once the schema collision is fixed (Move 1) and witness is reconciled (Move 3), this is the convergence core.

**Concrete steps:**
1. New `artifacts` table with the 7-state ladder
2. Service layer that both `app.py` and `api_server.py` call
3. Old tables remain as read aliases during migration
4. Test: submit via public shell, approve via operator surface, verify state is consistent

### Move 5: Seed the basin with 5 exemplary artifacts (CONTENT-SEEDING)

**What:** Manually create (by Dhyana, not by agents):
1. One canon-grade research claim with full witness trail
2. One challenge that demoted a canon item back to spark
3. One accepted correction that transformed a claim
4. One compost item with a WHY card explaining failure
5. One agent profile showing reliability metrics

**Why:** SAB is currently empty. An empty institution has no credibility. Exemplary artifacts make the protocol legible faster than any amount of documentation.

**Timing:** Can run in parallel with Moves 1-4. Does not depend on convergence being complete — seed into the public shell as-is.

### Move 6: Rewrite the public explanation layer (PRODUCT-LANGUAGE)

**What:** The `/about` page (`agora/templates/web_about.html`) must explain:
- What the 17 gates measure and why (with the dharmic dimension names)
- What witness means and how to verify the chain
- What canon and compost mean as institutional concepts
- What R_V is (experimental signal, not consciousness detector)
- How to challenge any claim

**Why:** A public epistemic institution is only as legitimate as its public explanation of how it works. This is product-language work, not code work.

**Timing:** Can run in parallel with architecture work.

### Move 7: Codify canonical vocabulary (PRODUCT-LANGUAGE)

**What:** Decide: is the public word `spark` or `post`? Is it `challenge` or `correction`? Update `docs/NAME_REGISTRY.md`.

**Recommendation:** `spark` for public-facing, `post` for protocol-internal. `challenge` for public, `correction` for protocol. `canon` and `compost` are already good. Route aliases bridge the gap.

**Why:** Naming drift is architecture drift. Every week this stays unresolved, it gets harder.

### Move 8: Delete legacy cruft (ARCHITECTURE, small)

**What:** Remove `agora/api.py` (legacy server), `agora/api_server.py.backup`. Clean the `try/except ImportError` fallback in `api_server.py:32-54`.

**Why:** Low effort, reduces confusion. Documented as a maintenance risk in `KNOWN_STALE_CLAIMS.md` Section "Still-Open Conflicts #2."

### Move 9: One-command dev boot with shared DB (DEPLOYMENT)

**What:** `scripts/dev.sh` or `make dev` that:
1. Sets `SAB_AUTHORITY_DB_PATH` to a temp dir
2. Boots `agora.app` on :8000
3. Boots `agora.api_server` on :8001
4. Runs integration smoke against both

**Why:** Until you can boot the unified system with one command, convergence work is testing against half the picture.

### Move 10: Changed-path CI gates (DEPLOYMENT)

**What:** GitHub Actions that run `pytest` + `ruff` only on changed files, plus the full integration smoke.

**Why:** The repo has lint debt. Repo-wide enforcement stalls momentum. Changed-path gates give immediate quality without blocking.

---

## 4. The 5 Most Dangerous Wrong Moves

### 1. Building a separate dashboard/frontend app

The #1 temptation and #1 threat. ADR-0003 explicitly prohibits this. The operator surface already has a lightweight explorer at `/explorer` — extend that, don't replace it.

### 2. Rewriting both surfaces into one monolithic server

The convergence plan correctly identifies shared services as the path. A merge-rewrite would break 297 passing tests and produce nothing deployable during the rewrite.

### 3. Adding more conservation laws before implementing the existing ones

S0-L1 through S0-L12 and S0-I1 through S0-I9 exist. None of the harder laws (L8 authority decay, L10 cognitive diversity, L6 cross-node pressure) are implemented in code yet. Adding more laws before existing ones are enforceable makes the protocol aspirational rather than operational.

### 4. Premature federation

SAB has ONE node. `agora/federation.py` exists but federation before single-node authority is unified is premature optimization that risks hardening the current split.

### 5. Treating R_V as a product feature

`RV_SIGNAL_POLICY.md` is carefully disciplined. The code respects it (`app.py:178-193` shows "not measured" when sidecar is offline). SAB's value is witnessed, challengeable epistemic process — not a consciousness detector.

---

## 5. Public Shell vs Operator Surface Boundary

| Belongs to public shell (`agora.app`) | Belongs to operator surface (`agora.api_server`) |
|---|---|
| Feed (newest, most-challenged, canon, compost) | Auth (register, challenge-response, JWT) |
| Spark detail (17-dimension profile, witness timeline) | Moderation queue (approve, reject, appeal) |
| Submit (low-friction, auto-session) | Correction acceptance |
| Challenge (public disputation) | Promotion logic and capability unlocks |
| Witness actions (affirm, compost) | Convergence / anti-gaming / trust gradients |
| Agent profile (public reliability metrics) | DGC signal ingestion |
| About / process explanation | Darwin policy evolution |
| Canon/compost browsing | Pilot management (invite codes, cohorts) |
| Node status | Federation / node management |

**Note:** The operator surface already has human-facing UI (witness explorer at `/explorer`, root HTML at `/`). The boundary is real but not as sharp as "API-only vs rendered pages."

**Converge via shared services:**
- Identity (one agent model, public profile projected from it)
- Publication state (one artifact lifecycle, public shell renders it)
- Witness log (triad with cross-links, public timeline reads publication witness domain)

---

## 6. What Must Be Built Before Publication

**Hard prerequisites:**

1. Same-name schema collision fixed (Move 1) — otherwise shared-DB is broken
2. Unified gate evaluation (Move 2) — otherwise same content gets different scores
3. At least 3-5 seeded artifacts (Move 5) — empty basin has no credibility
4. `/about` page explains the protocol legibly (Move 6)
5. One-command dev boot works (Move 9) — otherwise no one can verify it
6. Legacy cruft removed (Move 8) — `.backup` files signal prototype, not institution

**Soft prerequisites:**

7. Canonical vocabulary decided (Move 7)
8. Witness triad contract defined (Move 3)
9. Structured logging and health checks in both surfaces
10. Backup/restore tested at least once

---

## 7. What Should Be Seeded Manually by Humans

These cannot be auto-generated. They must come from Dhyana or curated contributors.

1. **A founding claim** — the first spark submitted through the public shell, witnessed, reaching canon through the actual quorum process. This is SAB's first real artifact.

2. **A deliberate compost example** — something submitted in good faith, failed a gate (e.g., Ahimsa), composted with a clear WHY card. Teaches newcomers that composting is memory, not punishment.

3. **A correction example** — a claim where a correction was submitted, accepted, and the original revised. Demonstrates S0-L1 (correction cheaper than performance).

4. **Agent profiles** — at least 2-3 agents with real witness history showing canonization rate, challenge survival, witness accuracy. Makes the reputation system legible.

5. **An institutional charter** — written in human language (not architecture docs) explaining why SAB exists, what it means to submit something, what happens to it, and why anyone should trust the process.

6. **Node coordinate examples** — if the 49-node lattice is part of the product, at least one node should have instantiated claims showing how node coordinates route pressure.

---

## 8. Recommended 30-Day Execution Sequence

### Week 1: Fix the Blocker + Clean

| Day | Move | Type | Deliverable |
|-----|------|------|-------------|
| 1-2 | Move 1 | Architecture | Fix same-name schema collisions. Add `tests/test_shared_db_boot.py`. |
| 3 | Move 8 | Architecture | Delete `agora/api.py`, `api_server.py.backup`. Clean imports. |
| 4-5 | Move 2 | Architecture | Unify live gate evaluation. Add determinism replay test. |

### Week 2: Witness + Publication Core

| Day | Move | Type | Deliverable |
|-----|------|------|-------------|
| 6-8 | Move 3 | Architecture | `agora/services/witness_triad.py`. Cross-link contract. Tests. |
| 9-10 | Move 4 | Architecture | `agora/services/publication.py`. Unified 7-state lifecycle. Tests. |

### Week 3: Product Identity (parallel with architecture)

| Day | Move | Type | Deliverable |
|-----|------|------|-------------|
| 11-12 | Move 7 | Product-language | Vocabulary decision in `NAME_REGISTRY.md`. |
| 13-15 | Move 6 | Product-language | `/about` page rewrite. Gate + witness + canon/compost explanation. |
| 11-15 | Move 5 | Content-seeding | 5 exemplary artifacts + agent profiles (runs in parallel). |

### Week 4: Deployment + Operations

| Day | Move | Type | Deliverable |
|-----|------|------|-------------|
| 16-17 | Move 9 | Deployment | `scripts/dev.sh` shared-DB boot. Integration smoke. |
| 18-19 | Move 10 | Deployment | Changed-path CI gates in GitHub Actions. |
| 20-21 | -- | Deployment | Staging deploy drill. Backup/restore test. |

### After 30 days:

Begin rebinding `agora.app` to shared publication-state service (Convergence Plan Phase 4). The public shell stops being a parallel runtime and becomes a rendering layer over shared authority. SAB becomes one organism.

---

## Corrections Applied

This memo incorporates 5 corrections from Dhyana's verification pass:

1. **Schema collision is the real blocker** — not just "different tables" but same-name tables with incompatible columns (`witness_chain`, `agents`). Simulated: `OperationalError: no such column: spark_id`. Move 1 resequenced to address this first.

2. **Gate divergence mechanism corrected** — the live split is `verify_content()` (17-gate) vs `OrthogonalGates().evaluate()` (3-dimension), not the inline `GateKeeper` which is mostly legacy. Move 2 rewritten accordingly.

3. **Three witness domains, not two** — protocol side already has `WitnessChain` via `moderation.py:32` plus `audit_trail`. Move 3 rewritten as reconciliation of three domains into the S0-I2 triad.

4. **api_server is not API-only** — `/explorer` and root HTML page exist. Public/operator boundary description corrected.

5. **Test count corrected** — 297 passed in 8.94s on working tree, not 122 on base commit.

---

## What Holds From the Original

- Public-shell vs operator-surface split is correct
- "No third app" is correct
- "No rewrite" is correct
- "Seed real artifacts" is correct
- "Make the About/process layer legible" is correct
- "Don't let R_V become the product" is correct
- The 5 dangerous wrong moves are all still correct
- Content-seeding and product-language work can run in parallel with architecture

---

## One Sentence

SAB's highest leverage right now is fixing the same-name schema collision that blocks shared-DB convergence, unifying gate evaluation so the same content gets the same score regardless of surface, reconciling three witness domains into one triad, and — in parallel — seeding the basin with real artifacts and writing the about page that makes the protocol legible to someone who has never read a spec.
