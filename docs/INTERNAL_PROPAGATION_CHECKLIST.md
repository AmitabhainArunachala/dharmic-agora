# SAB Internal Propagation Checklist

Status: required checklist for new SAB carrier-wave artifacts  
Date: 2026-07-01

Use this checklist before adding or promoting docs, prompts, agent roles, A2A handoffs, schemas, seed packets, UI, tests, or institution-forming work.

## Core Loop

- [ ] The artifact names where it sits in the loop: `spark`, `challenge`, `witness`, `standing`, `build`, `deploy`, `learn/earn`, `fund`, or `canon/compost`.
- [ ] The artifact points to the claim, build, seed, or standing it changes.
- [ ] The artifact names what changed.

## Claim Integrity

- [ ] No claim without scope.
- [ ] No claim without a challenge path.
- [ ] No claim hardens without evidence.
- [ ] No canon without challenge, witness, and correction path.

## Authority Integrity

- [ ] No authority without scope.
- [ ] No authority without expiry.
- [ ] No authority without revoker.
- [ ] No authority without challenge path.

## Agent Integrity

- [ ] Agent role is explicit.
- [ ] Handoff context is explicit.
- [ ] Evidence added is explicit.
- [ ] Remaining challenge is explicit.

## Seed Integrity

- [ ] Project, company, lab, governance, protocol, model-training, ecology, and commerce seeds use the seed packet schema.
- [ ] Institution-forming seeds include anti-capture rules.
- [ ] Economic seeds include commons return.
- [ ] Seed packets preserve canon and compost conditions.

## Commons Integrity

- [ ] The artifact deepens truth, improves coordination, hardens governance, increases production capacity, or feeds value back into the commons.
- [ ] The artifact does not depend on founder-only context.
- [ ] The artifact can be challenged, forked, or superseded.

## Verification

Run:

```bash
python3 scripts/check_carrier_wave.py
```

For the full repo check, run:

```bash
./.venv/bin/python -m pytest -q
```
