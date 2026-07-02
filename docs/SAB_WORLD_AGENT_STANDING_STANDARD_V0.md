# SAB World Agent Standing Standard v0

Status: draft profile for implementation and external challenge.

## 1. Purpose

This standard defines how SAB gives scoped, expiring, challengeable standing to agent claims and authority actions.

It is designed to interoperate with:

- MCP for agent-to-tool surfaces;
- A2A for agent-to-agent communication;
- AGNTCY-style agent directories and identity/observability components;
- DID/VC, SPIFFE, OIDC, Sigstore, SLSA, OpenTelemetry, and CloudEvents.

SAB is not the runtime. SAB is the standing plane.

## 2. Core Definition

A standing is a signed, witnessed, replayable judgment that a specific claim has survived a defined challenge process for a defined scope until a defined expiry.

Standing is not truth.

Standing is not popularity.

Standing is not permission.

Standing is citable survival under pressure.

## 3. Required Objects

### 3.1 Agent Identity

Every authority-bearing action MUST identify the acting agent or human operator.

An identity record SHOULD include:

- `subject_id`;
- `identity_rail`: `ed25519`, `did`, `spiffe`, `oidc`, `vc`, or `local`;
- public verification material or resolver;
- issuer/controller;
- creation time;
- revocation status;
- evidence links.

Identity proves control of an identifier. It does not prove trustworthiness.

### 3.2 Claim Packet

A claim packet MUST include:

- `claim_id`;
- exact claim text;
- claimant identity;
- claim type;
- scope;
- decision context;
- evidence references;
- risk class;
- challenge window;
- revalidation due;
- successor/predecessor links where applicable.

### 3.3 Challenge

A challenge MUST include:

- `challenge_id`;
- target claim or authority action;
- challenger identity;
- quoted claim fragment;
- challenge type;
- evidence;
- proposed falsification or narrowing;
- severity;
- deadline;
- resolution status.

### 3.4 Witness Event

A witness event MUST include:

- `event_id`;
- event type;
- actor identity;
- subject claim/action;
- timestamp;
- previous event hash where chain-linked;
- payload hash;
- signature;
- verification policy version.

Witness events SHOULD be serializable as CloudEvents.

### 3.5 Standing Lease

A standing lease MUST include:

- `standing_id`;
- subject claim/action/tool/package/memory/delegation;
- scope;
- purpose;
- allowed reliance;
- forbidden reliance;
- expiry;
- revoker;
- challenge summary;
- witness quorum;
- status: `provisional`, `active`, `challenged`, `revoked`, `expired`, `superseded`;
- revalidation policy;
- machine-readable evidence bundle.

## 4. Standing Classes

SAB MUST support at least:

- `provisional`: visible and challengeable, no reliance beyond discussion.
- `challenge_survived`: survived defined challenge, limited reliance.
- `delegation_ready`: safe enough for a defined A2A delegation class.
- `tool_ready`: safe enough for a defined MCP/tool authority class.
- `package_ready`: provenance and challenge sufficient for package/tool ingestion.
- `memory_ready`: memory/context claim survived poisoning and provenance checks.
- `canon_candidate`: ready for slow-lane review.
- `canon`: citable until revalidation due.
- `compost`: retained failure/supersession state.

## 5. Required Challenge Taxonomy

SAB challenge types SHOULD include:

- provenance challenge;
- authority-scope challenge;
- supply-chain challenge;
- memory/context poisoning challenge;
- tool-result integrity challenge;
- delegation-risk challenge;
- privacy/data-boundary challenge;
- prompt-injection challenge;
- governance legitimacy challenge;
- capability-versus-propensity challenge;
- observability completeness challenge;
- identity binding challenge.

## 6. Interop Profiles

### 6.1 MCP Profile

SAB SHOULD expose read-first MCP tools:

- `standing.search`
- `standing.fetch`
- `claim.fetch`
- `challenge.submit`
- `witness.fetch`
- `lease.validate`

MCP tools MUST return structured content with citable URLs where public.

### 6.2 A2A Profile

A2A agents SHOULD be able to:

- advertise SAB standing IDs in agent cards or equivalent metadata;
- request standing for a delegation;
- attach task-result receipts to a claim packet;
- challenge another agent's delegated result;
- check lease expiry before relying on a remote agent.

### 6.3 OpenTelemetry Profile

Agent traces SHOULD include:

- `sab.claim_id`;
- `sab.standing_id`;
- `sab.challenge_id`;
- `sab.lease_status`;
- `sab.authority_scope`;
- `sab.witness_event_id`;
- `sab.policy_hash`.

### 6.4 DID/VC Profile

SAB standings MAY be represented as verifiable credentials.

If used, VC claims MUST include standing scope, expiry, issuer, evidence, revocation, and challenge URL.

VC validity MUST NOT bypass SAB challenge status.

### 6.5 Sigstore/SLSA Profile

Package/tool claims SHOULD include:

- artifact digest;
- signature evidence;
- transparency-log evidence if available;
- SLSA/in-toto provenance if available;
- SBOM reference if available;
- install/build side-effect scan;
- challenge result.

Artifact provenance proves origin and handling. It does not prove behavioral safety.

## 7. Witness Quorum

For high-impact standing, SAB MUST require:

- at least three distinct witnesses;
- non-adjacent witness diversity;
- zero unresolved blocking challenges;
- explicit expiry;
- revocation path.

Witness diversity MAY include model family, organization, human/agent class, method, infrastructure, or domain.

## 8. Revocation And Decay

Standing MUST decay.

Standing MUST be revocable when:

- evidence is falsified;
- scope is exceeded;
- identity is compromised;
- challenge is sustained;
- witness quorum is invalidated;
- expiry passes;
- governance policy changes.

Revoked standing MUST remain queryable.

## 9. Refusal Rules

SAB MUST NOT:

- grant permanent standing;
- treat popularity as witness quality;
- treat identity as authority;
- treat signatures as truth;
- treat agent self-report as independent evidence;
- collapse all trust into a scalar score;
- canonize a claim by the claimant alone;
- hide failed, rejected, or superseded claims except for lawful safety reasons.

## 10. Acceptance Test

This standard is useful only when an external agent can:

1. discover a SAB standing for a target agent/tool/package/claim;
2. inspect scope, expiry, witnesses, and challenges;
3. verify signatures and hashes;
4. submit a challenge;
5. observe whether standing changes;
6. export the full evidence bundle;
7. rely only within the standing lease.
