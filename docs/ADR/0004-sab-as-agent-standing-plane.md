# ADR-0004: SAB As The Agent Standing Plane

**Status:** Proposed  
**Date:** 2026-07-01  
**Decision Type:** Product boundary / external protocol positioning

---

## Context

SAB already has a deep internal shape:

- spark;
- challenge;
- witnessed sublation;
- canon;
- compost;
- signed witness chain;
- correction-first governance;
- public process legibility.

The external agent ecosystem is converging around complementary protocol layers:

- MCP connects agents to tools, data, and workflows.
- A2A connects opaque agentic applications to each other.
- AGNTCY-style components target discovery, identity, messaging, observability, and evaluation.
- DID/VC/SPIFFE/OIDC establish identity and credential rails.
- Sigstore, SLSA, in-toto, and SBOMs establish artifact provenance.
- OpenTelemetry and CloudEvents establish telemetry and event portability.
- OWASP and NIST establish security and risk-management language.

None of these layers, by itself, decides whether a claim, delegation, memory, tool, package, or authority grant has survived challenge and deserves scoped reliance.

That gap is exactly aligned with SAB's native primitives.

## Decision

SAB will position itself as the agent standing plane.

This means SAB standardizes and serves scoped, expiring, challengeable standing for:

- public claims;
- agent identities where authority-bearing;
- tool permissions;
- package and connector provenance claims;
- memory/context entries;
- delegation results;
- governance and policy assertions;
- authority leases.

The core output is a signed, witnessed, replayable standing lease.

## Non-Goals

SAB will not position itself as:

- an agent runtime;
- a model provider;
- a general agent directory;
- an app store;
- a reputation marketplace;
- a token network;
- a private certification authority;
- a social network;
- a world government;
- a standards body claiming unilateral authority.

## Required Consequences

Future work should prioritize:

1. standing lease schema;
2. challenge schema;
3. witness event schema;
4. authority lease schema;
5. evidence bundle format;
6. MCP standing lookup and challenge tools;
7. A2A standing metadata examples;
8. OpenTelemetry and CloudEvents export profile;
9. package/tool trust dossier;
10. delegation trust dossier;
11. memory trust dossier.

## Validation Test

This decision is valid only if an external agent can:

1. discover a SAB standing for a target claim, tool, package, memory, delegation, or agent;
2. inspect scope, expiry, evidence, witnesses, and conflicts;
3. verify signatures and hashes;
4. submit a challenge;
5. observe standing status change when a challenge is sustained;
6. export or fork the evidence bundle;
7. rely only inside the lease scope.

## Reversal Conditions

This ADR should be revisited if:

- a better primary standard already solves adversarial standing;
- SAB cannot expose standing without creating capture or legal risk;
- external users consistently need runtime or directory functionality more than standing;
- the claim/challenge/witness loop fails to produce useful decisions in three consecutive public dossiers.

## Implementation Notes

This ADR does not require a rewrite of the existing runtime surfaces.

It constrains the next layer of work:

- `agora.api_server` remains the protocol/operator surface;
- `agora.app` remains the public basin shell;
- standing objects can start as file-backed schemas and examples;
- API/MCP/A2A integrations should be added once the standing objects are stable.

Short version:

**SAB should not become the agent world. SAB should become the challengeable standing layer the agent world can cite.**
