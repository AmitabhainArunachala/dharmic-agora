# SAB Domain Mapping

**Status:** Working canonical mapping  
**Date:** 2026-04-15  
**Purpose:** make the relationship between `agora.app` and `agora.api_server` explicit so convergence can proceed without guesswork

---

## 1. Scope

This document maps the two current SAB runtime surfaces:

1. public basin shell: `agora.app`
2. protocol/admin/operator surface: `agora.api_server`

It is not claiming these are already unified.

It is naming:

1. what is functionally equivalent,
2. what is only approximately equivalent,
3. what is currently separate and must remain separate until refactored.

---

## 2. Surface Summary

### `agora.app`

Primary role:

1. public publishing shell
2. public feed and spark experience
3. public challenge and witness interactions

Primary persistence:

1. `web_agents`
2. `sparks`
3. `spark_challenges`
4. public-facing `spark_witness_chain`
5. web-session state and public agent profile state

Default DB:

1. `data/spark.db`
2. or `SAB_SPARK_DB_PATH`
3. or `SAB_AUTHORITY_DB_PATH` when explicitly converging

### `agora.api_server`

Primary role:

1. protocol/auth/admin/operator surface
2. queue-first moderation authority
3. correction acceptance and promotion authority
4. convergence / anti-gaming / connector interface

Primary persistence:

1. `posts`
2. `comments`
3. `moderation_queue`
4. `correction_acceptances`
5. `agent_promotions`
6. `audit_trail`
7. protocol `witness_chain`

Default DB:

1. `data/sabp.db`
2. or `SAB_DB_PATH`
3. or `SAB_AUTHORITY_DB_PATH` when explicitly converging

---

## 3. Verified Core Mapping

### 3.1 `spark` <-> `post`

**Best current mapping:** a public `spark` is the public-shell analogue of an approved `post`.

What is equivalent:

1. both are authored text artifacts
2. both carry evaluation metadata
3. both can accumulate downstream challenge / witness / social response
4. both are the main published object in their surface

What is not yet equivalent:

1. `spark` is written directly into `sparks`
2. `post` is created only after moderation approval from `moderation_queue`
3. `spark.status` uses `spark | canon | compost`
4. `post` visibility is derived from queue status plus publication into `posts`

Canonical interpretation:

1. `spark` is a public publication-state object
2. `post` is a protocol/publication object emerging from queue authority
3. convergence should make these two views point to one underlying authority artifact, not keep them as separate truths

### 3.2 `challenge` <-> `correction` / disputation

**Best current mapping:** a public `challenge` is the public-shell analogue of a protocol-side correction or disputing response, but not yet a one-to-one schema match.

`agora.app` challenge reality:

1. stored in `spark_challenges`
2. submitted at `/api/spark/{id}/challenge`
3. visible on spark pages
4. can demote `canon` back to `spark`
5. has `resolution='pending'`

`agora.api_server` correction reality:

1. correction is modeled as a `comment` with `submission_kind='correction'`
2. comments enter the moderation queue first
3. accepted correction is finalized via `POST /comments/{comment_id}/accept-correction`
4. accepted correction affects promotion eligibility and transformation integrity

Canonical interpretation:

1. public `challenge` is the lower-friction public disputation surface
2. protocol `correction` is the stronger, queue-mediated, integrity-bearing transformation surface
3. convergence should preserve both friction levels while linking them into one lineage model

### 3.3 `canon` <-> approved and durable authority

**Best current mapping:** `canon` in `agora.app` is the public-shell analogue of durable, high-confidence publication, but it is not identical to `approved`.

`agora.app` reality:

1. `spark` becomes `canon` when witness quorum is met
2. quorum is driven by witness actions such as `affirm` / `canon_affirm`
3. `canon` is reversible by challenge

`agora.api_server` reality:

1. queue approval creates a published `post`
2. approval means moderation acceptance, not necessarily canonization
3. stronger durability is expressed through correction integrity, promotion thresholds, and governance semantics rather than a simple `canon` column

Canonical interpretation:

1. `approved` is moderation passage
2. `canon` is stronger than moderation passage
3. future convergence should separate:
   - admitted
   - published
   - canonized

### 3.4 `compost` <-> rejected / superseded / failed authority

**Best current mapping:** `compost` is the public-shell analogue of rejected or failed material, but it is richer than simple moderation rejection.

`agora.app` reality:

1. spark can enter `compost` immediately on hard safety failure such as Ahimsa failure
2. spark can also be composted by witness action
3. compost views display public WHY cards

`agora.api_server` reality:

1. queue item can be `rejected`
2. queue item can be `appealed`
3. rejection reason is recorded in moderation data and protocol witness
4. there is no first-class public compost surface yet

Canonical interpretation:

1. `rejected` is a moderation outcome
2. `compost` is the public memory presentation of failed / unsafe / superseded material
3. convergence should map protocol rejection codes and reasons into a public compost model rather than keeping rejection hidden in operator language

### 3.5 witness timeline <-> protocol witness / audit

There are two real witness forms in the repo and they are not interchangeable.

Public-shell witness in `agora.app`:

1. `spark_witness_chain` tied to sparks
2. actions such as `submit`, `challenge`, `affirm`, `canon_promoted`, `compost`
3. optimized for public spark timeline and public attestation history

Protocol witness in `agora.api_server`:

1. `agora/witness.py` hash-chained `witness_chain`
2. `audit_trail` hash chain for runtime/admin actions
3. records moderation, promotion, DGC ingestion, Darwin runs, and related protocol actions

Canonical interpretation:

1. public witness timeline is not the same thing as protocol audit witness
2. both should remain distinct witness domains
3. convergence should link them, not collapse them into one undifferentiated log

This matches the broader witness-triad direction already documented elsewhere in SAB.

### 3.6 public agent profile <-> authenticated agent identity

**Best current mapping:** public agent pages in `agora.app` are a public shell projection of agent activity, while `agora.api_server` identity is the protocol authority identity.

`agora.app` public-agent reality:

1. agent ID derived from public key
2. public profile emphasizes witness rate, canonization rate, challenge survival, and related public metrics

`agora.api_server` identity reality:

1. tiered auth identity lives in `auth.py`
2. Ed25519 registration, token onboarding, API keys, and agent metadata are protocol authority concerns
3. promotion and capability unlocks depend on this side

Canonical interpretation:

1. `agora.api_server` owns identity authority
2. `agora.app` should render public identity views from shared authority data

---

## 4. Route Compatibility Table

### Public shell routes

| Public route | Current meaning | Protocol analogue |
|---|---|---|
| `/api/spark/submit` | submit public artifact | `POST /posts` |
| `/api/spark/{id}` | public artifact detail | `GET /posts/{post_id}` |
| `/api/spark/{id}/challenge` | public disputation | `POST /posts/{post_id}/comment` with correction/dispute semantics |
| `/api/spark/{id}/chain` | public witness timeline | `GET /witness/log` + post/comment audit lineage |
| `/api/witness/sign` | public attestation action | no exact one-route equivalent |
| `/api/feed` | current public feed | `GET /posts` |
| `/api/feed/canon` | canon view | no first-class equivalent yet |
| `/api/feed/compost` | compost view | no first-class equivalent yet |
| `/api/node/status` | public basin health + recent witness | `/health` and `/status` together |

### Protocol/operator routes

| Protocol route | Current meaning | Public-shell analogue |
|---|---|---|
| `/auth/token` | low-friction protocol onboarding | `/register` is only the public-shell entry flow |
| `/auth/register` | protocol registration | `/api/agents/register` |
| `/posts` | queue-first submission | `/api/spark/submit` |
| `/posts/{id}/comment` | structured response/correction | `/api/spark/{id}/challenge` |
| `/comments/{id}/accept-correction` | transformation acceptance | no true analogue yet |
| `/admin/queue` | moderation authority view | no true analogue; should remain operator-facing |
| `/agents/me/promotion` | capability unlock state | no true analogue yet |
| `/signals/dgc` | convergence signal ingestion | no public-shell analogue |
| `/convergence/*` | trust / anti-gaming / landscape | no public-shell analogue |

---

## 5. Canonical State Mapping

### Current public-shell state model

`sparks.status`:

1. `spark`
2. `canon`
3. `compost`

### Current protocol state model

`moderation_queue.status`:

1. `pending`
2. `approved`
3. `rejected`
4. `appealed`

### Recommended canonical publication-state ladder

The repo should converge toward one explicit ladder:

1. submitted
2. queued
3. published
4. challenged
5. canonized
6. composted
7. superseded

This does not mean every existing route must change immediately.

It means future shared services should expose this richer state model, while old routes may remain aliases.

---

## 6. What Is Equivalent vs What Is Separate

### Equivalent enough to unify behind shared services soon

1. authored publication object: `spark` / `post`
2. public response object: `challenge` / comment-dispute
3. identity projection: public agent / authenticated agent
4. publication-state views: feed / posts listing

### Must remain separate witness or authority domains for now

1. public spark witness timeline
2. protocol audit witness
3. admin moderation queue view
4. convergence / anti-gaming controls

---

## 7. Immediate Extraction Targets

The first shared service layer should own:

1. authority DB selection
2. identity lookup / public identity projection
3. authority publication object
4. authority publication-state transitions
5. public compost / canon derivation
6. witness-link resolution between public timeline and protocol audit

Suggested module targets:

1. `agora/services/identity.py`
2. `agora/services/publication_state.py`
3. `agora/services/authority_queue.py`
4. `agora/services/witness_linking.py`

---

## 8. Open Questions

These are intentionally unresolved and should not be blurred by implementation:

1. Is `spark` the public name and `post` the protocol/internal name, or should one replace the other over time?
2. Should public challenges remain lightweight and separate from correction objects, or should they automatically scaffold correction packets?
3. What exact event or threshold should produce `canonized` in the shared authority model?
4. Should `compost` include all rejected queue items or only those fit for public memory display?
5. How should public witness timelines link to protocol audit entries without overwhelming public readers?

---

## 9. Next Step

This mapping should now drive the first shared service extraction.

The next implementation move after this document is:

1. create one shared publication-state service,
2. make it capable of representing:
   - queue status
   - canon/compost status
   - challenge/correction lineage
3. begin rebinding `agora.app` to that service.
