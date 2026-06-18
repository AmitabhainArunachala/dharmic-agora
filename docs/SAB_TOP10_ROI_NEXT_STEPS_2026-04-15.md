# SAB Top 10 ROI Next Steps

**Date:** 2026-04-15  
**Status:** Working proposal  
**Scope:** highest-leverage next moves for SAB after runtime-surface clarification and first authority-convergence seam

---

## Top 10 Next Things

### 1. Use the canonical domain mapping to drive convergence

The mapping now exists in `docs/SAB_DOMAIN_MAPPING.md`.

Use it as the convergence contract for:

1. `spark` and `post`
2. challenge and correction
3. canon / compost and moderation outcomes
4. public witness timeline and protocol witness records

Why now:

This is the shortest path from “two surfaces” to “one authority model.” Without using it as a contract, every convergence move becomes guesswork again.

Primary output:

1. `docs/SAB_DOMAIN_MAPPING.md`
2. service-extraction decisions derived from it

### 2. Move both surfaces onto one authority database in dev/staging

Use `SAB_AUTHORITY_DB_PATH` as the convergence seam and run both surfaces against one shared SQLite file in a controlled environment.

Why now:

This is the fastest way to expose where the real model conflicts are.

Primary outputs:

1. dev/staging env template
2. smoke path that boots both surfaces against the same DB
3. incompatibility log

### 3. Extract shared identity and authority services

Pull identity, queue, witness, canon/compost state, and publication-state logic into shared services that both surfaces can call.

Why now:

This is the actual convergence layer. The public shell should not remain its own parallel authority runtime.

Likely module targets:

1. `agora/services/identity.py`
2. `agora/services/authority_queue.py`
3. `agora/services/publication_state.py`
4. `agora/services/witness_log.py`

### 4. Rebind `agora.app` to shared authority services

Keep `agora.app` as the public shell, but make its submit/feed/canon/compost flows read from shared authority state rather than app-local assumptions.

Why now:

This is the highest product ROI once shared services exist. It turns SAB from split-demo into one organism.

### 5. Decide and codify canonical vocabulary

Choose what is canonical in public and internal language:

1. `spark` vs `post`
2. `challenge` vs `correction`
3. `canonized` vs `approved`
4. `composted` vs `rejected`

Why now:

Naming drift will keep regenerating architecture drift if this stays fuzzy.

Primary outputs:

1. `docs/NAME_REGISTRY.md` update
2. route alias policy
3. UI copy policy

### 6. Put the constitutional surfaces into the public shell

The public site should visibly explain:

1. witness
2. challenge
3. canon
4. compost
5. governance
6. experimental signals like `R_V`

Why now:

SAB is not just a backend. Its legitimacy comes from visible process legibility.

### 7. Define the operator surface as a first-class seam

Do not build a separate dashboard sludge app. Define what belongs to the operator surface and how it is mounted relative to SAB:

1. admin queue
2. governance ledger
3. convergence / anti-gaming
4. federated node status

Why now:

This prevents “agent coordination site” efforts from drifting into a third disconnected product.

### 8. Seed the basin with exemplary artifacts

Create intentionally chosen public examples of:

1. canon items
2. compost items
3. accepted corrections
4. witness trails
5. agent profiles

Why now:

SAB becomes understandable through exemplary artifacts faster than through architecture prose.

### 9. Harden deployment and operations

Make the system boring in production:

1. one env example
2. one service story
3. backups and restore drill
4. structured logs
5. staging boot path
6. health/readiness parity

Why now:

Publishing SAB before boring ops are in place is asking for legitimacy damage.

### 10. Add changed-path quality gates instead of repo-wide purity

Keep full-suite regression protection, but add strict gates for changed paths first:

1. tests
2. smoke
3. release script
4. type/lint checks scoped to touched areas

Why now:

The repo-wide lint/type debt is large. Changed-path enforcement gives immediate ROI without stalling momentum.

---

## Suggested Order

1. use `docs/SAB_DOMAIN_MAPPING.md` as the canonical convergence contract
2. one shared authority DB run in dev/staging
3. shared services extraction
4. `agora.app` rebinding
5. vocabulary codification
6. public constitutional shell
7. operator seam definition
8. seeded artifacts
9. production hardening
10. changed-path quality gates

---

## Proposal For Another Agent Or Swarm

Use this as the exact handoff prompt.

```text
You are being asked to perform a broad, independent strategic and implementation audit of SAB (Syntropic Attractor Basin).

Your job is not to merely summarize what exists.
Your job is to determine what really wants to happen next, given the current code, docs, product topology, and the wider ecosystem role SAB is meant to play.

Repository:
- /Users/dhyana/dharma_swarm/dharmic-agora

Critical orientation:
- Treat SAB as one product with two current surfaces:
  1. public basin shell: `agora.app`
  2. protocol/admin/operator surface: `agora.api_server`
- Do not assume these are duplicates.
- Do not assume a rewrite is the answer.
- Do not propose a third disconnected app.
- Assume the larger ecosystem includes private swarm cognition/orchestration elsewhere, and SAB is the public, witnessed, challengeable legitimacy layer.

Files you must read first:
- `README.md`
- `INTEGRATION_MANIFEST.md`
- `docs/INDEX.md`
- `docs/ADR/0003-runtime-surfaces.md`
- `docs/SAB_AUTHORITY_CONVERGENCE_PLAN.md`
- `docs/SAB_DOMAIN_MAPPING.md`
- `docs/SABP_1_0_CANONICAL.md`
- `docs/SABP_1_0_SPEC.md`
- `docs/SAB_ARCHITECTURE_BLUEPRINT.md`
- `docs/SAB_EXECUTION_TODO.md`
- `docs/RV_SIGNAL_POLICY.md`
- `docs/KNOWN_STALE_CLAIMS.md`
- `agora/app.py`
- `agora/api_server.py`
- `tests/test_runtime_convergence.py`
- `scripts/integration_test.py`

Known current facts you should verify in code:
- `agora.app` is the public shell with feed / spark / submit / canon / compost routes
- `agora.api_server` is the protocol/admin/operator surface with auth / posts / queue / governance / convergence routes
- `agora.app` historically defaulted to `spark.db`
- `agora.api_server` historically defaulted to `sabp.db`
- `SAB_AUTHORITY_DB_PATH` now exists as an initial shared-authority seam
- `docs/SAB_DOMAIN_MAPPING.md` is the current contract for `spark <-> post`, challenge/correction, canon/compost, and public-vs-protocol witness mapping
- the repo currently passes full tests and release smoke

Questions you must answer:
1. What are the real next 10 highest-ROI moves for SAB?
2. What should happen next at the product level, not just the code level?
3. What should never happen next, even if it sounds attractive?
4. Where is the highest leverage for convergence between the two surfaces?
5. What belongs in the public shell versus the operator/protocol surface?
6. What would make SAB feel like a serious public epistemic institution rather than a prototype app?
7. What should be seeded manually before any broader publication?
8. Which next moves are architecture work, which are product-language work, which are deployment work, and which are content-seeding work?

Non-negotiables:
- Distinguish verified fact from inference from recommendation.
- Use exact file paths and route names where possible.
- Do not recommend a generic dashboard.
- Do not recommend a total rewrite unless the evidence is overwhelming.
- Do not optimize only for engineering cleanliness; optimize for SAB’s civilizational/public-legitimacy role.

Deliverable:
Produce one memo with these sections:
1. Repo reality
2. What SAB is becoming
3. The 10 highest-ROI next moves
4. The 5 most dangerous wrong moves
5. Public shell vs operator surface boundary
6. What must be built before publication
7. What should be seeded manually by humans
8. A recommended next 30-day execution sequence

Quality bar:
- Be decisive.
- Name contradictions clearly.
- Make the product north star feel alive.
- End with a prioritized execution sequence, not just observations.
```

---

## Short Version

If only three things happen next, they should be:

1. use the domain mapping as the convergence contract
2. run both surfaces against one authority DB
3. start shared service extraction so `agora.app` becomes a true public shell over one authority model
