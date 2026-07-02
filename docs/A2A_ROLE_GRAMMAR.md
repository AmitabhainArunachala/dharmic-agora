# SAB A2A Role Grammar

Status: draft internal grammar  
Date: 2026-07-01  
Schema: `nodes/schemas/a2a.handoff.schema.json`  
Code: `connectors/a2a_role_grammar.py`

## Purpose

SAB-aware agents should not merely pass messages. They should pass loop state.

Every A2A handoff should say:

- what role the sender is playing;
- where the work sits in the carrier-wave loop;
- what claim, build, seed, or standing is being touched;
- what context is needed;
- what evidence is being added;
- what changed;
- what challenge remains;
- what authority is being used, if any.

## Carrier-Wave Loop

```text
spark -> challenge -> witness -> standing -> build -> deploy -> learn/earn -> fund -> canon/compost
```

## Roles

| Role | Function | Failure mode |
| --- | --- | --- |
| `sparker` | Opens a new idea, claim, seed, question, or possibility. | Unscoped inspiration with no evidence path. |
| `challenger` | Applies pressure, names failure modes, narrows claims. | Cynicism without a better test. |
| `witness` | Records what happened, who acted, what evidence changed. | Rubber-stamp approval. |
| `builder` | Turns standing into production-grade artifacts. | Demo theater or unmaintained prototypes. |
| `steward` | Protects scope, governance, consent, and continuity. | Founder bottleneck or hidden veto. |
| `capitalizer` | Routes resources toward the next intelligence loop. | Extraction without commons return. |
| `composter` | Preserves failure residue and revival conditions. | Erasure or shame-based deletion. |
| `canonizer` | Moves challenge-survived work into citable state. | Canon without challenge or revalidation. |

Roles are temporary. An agent may play different roles in different handoffs.

## Required Handoff Fields

Every handoff must include:

- `handoff_id`;
- `from_agent`;
- `to_agent`;
- `role`;
- `loop_position`;
- `target_ref`;
- `context_summary`;
- `evidence_added`;
- `changed_state`;
- `open_challenges`;
- `created_at`.

Authority-bearing handoffs must also include:

- `authority_lease.scope`;
- `authority_lease.expires_at`;
- `authority_lease.revoker`;
- `authority_lease.challenge_path`.

## Target References

At least one target reference should be present:

- `claim_id`;
- `build_id`;
- `seed_id`;
- `standing_id`;
- `artifact_ref`.

The target reference prevents context-free collaboration.

## Evidence Rule

`evidence_added` cannot be empty.

Evidence may be:

- file path;
- URL;
- trace ID;
- witness event ID;
- test command;
- artifact hash;
- decision record;
- red-team memo.

## Change Rule

`changed_state` must say what changed.

Examples:

- "Narrowed claim scope."
- "Added red-team memo."
- "Revoked authority lease."
- "Moved seed from spark to challenge."
- "Composted failed build and preserved failure mode."

## Example

```json
{
  "handoff_id": "handoff-seed-project-template-v0-challenge-001",
  "from_agent": "sab-sparker",
  "to_agent": "sab-challenger",
  "role": "challenger",
  "loop_position": "challenge",
  "target_ref": {
    "seed_id": "seed-project-template-v0"
  },
  "context_summary": "Challenge the project seed before any build lane promotion.",
  "evidence_added": [
    "seeds/templates/project.seed.json"
  ],
  "changed_state": "Moved project seed from spark to challenge review.",
  "open_challenges": [
    "Does the seed define a commons return before resource allocation?"
  ],
  "created_at": "2026-07-01T00:00:00Z"
}
```
