# Witness Triad Contract

**Status:** working contract  
**Date:** 2026-04-17

---

## 1. Purpose

SAB keeps witness domains logically separate while allowing one witnessed event to
be resolved across domains.

This implements `S0-I2 Witness Triad Separation` from `docs/SABP_1_0_CANONICAL.md`.

---

## 2. Domains

1. Publication witness
   - public shell spark witness in `spark_witness_chain`
   - protocol moderation witness in `witness_chain`
2. Artifact witness
   - external to this repo, e.g. `agent_core/core/witness_event.py`
3. Governance witness
   - runtime/admin audit in `audit_trail`

Artifact witness remains logically separate. This repo currently cross-links
publication and governance witness.

---

## 3. Shared Cross-Link Contract

All witness-capable stores may carry these fields:

1. `witness_domain`
2. `witness_link_id`
3. `related_link_ids_json`

The canonical metadata payload is nested under `witness_meta` and includes:

1. `link_id`
2. `domain`
3. `action`
4. `actor_id`
5. `subject_type`
6. `subject_id`
7. `origin`
8. `related_link_ids`

Implementation helper:

- `agora/witness_service.py`

---

## 4. Current Wiring

### Public shell

- `agora.app:_append_witness`
- table: `spark_witness_chain`
- default domain: `publication`

### Protocol moderation witness

- `agora.witness:WitnessChain.record`
- `agora.moderation:approve/reject/appeal`
- table: `witness_chain`
- default domain: `publication`

### Governance/runtime audit

- `agora.api_server:record_audit`
- table: `audit_trail`
- default domain: `governance`

Moderation approve/reject/appeal now emit:

1. publication witness row in `witness_chain`
2. governance audit row in `audit_trail`
3. shared `witness_link_id` across both rows

---

## 5. Resolution Surface

API endpoint:

- `GET /witness/triad/{witness_link_id}`

Current response groups rows into:

1. `publication.public_shell`
2. `publication.protocol`
3. `artifact`
4. `governance`

---

## 6. Constraints

1. Domains remain logically separate even if they share one SQLite file.
2. Cross-linking does not imply schema unification.
3. Governance audit is not a substitute for publication witness.
4. Public spark witness is not a substitute for protocol moderation witness.

---

## 7. Next Step

Move 4 should consume this contract when extracting shared publication state, so
artifact lineage, publication state, and governance changes can be resolved
without collapsing into one undifferentiated log.
