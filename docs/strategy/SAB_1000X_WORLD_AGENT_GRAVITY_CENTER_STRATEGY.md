# SAB 1000x Strategy: World Agent Standing Plane

Date: 2026-07-01  
Status: operating thesis and build strategy  
Depends on:

- `docs/SABP_1_0_CANONICAL.md`
- `docs/SAB_UNIVERSAL_ATTRACTOR_SEED.md`
- `docs/SAB_WORLD_AGENT_STANDING_STANDARD_V0.md`
- `docs/research/SAB_EXTERNAL_RESEARCH_REGISTER_2026_07_01.md`

## Executive Verdict

SAB should become the open standing plane for the agent world.

That does not mean becoming the biggest agent runtime, the most popular directory, a reputation marketplace, a token network, a social layer, or a certification authority.

It means becoming the place where claims made by agents, tools, packages, memories, delegations, and authority grants are converted into scoped, expiring, challengeable standing.

The agent ecosystem is already building the transport rails:

- MCP for agent-to-tool context and tool invocation;
- A2A for agent-to-agent communication;
- AGNTCY-style components for discovery, identity, messaging, observability, and evaluation;
- DID/VC/SPIFFE/OIDC for identity and credentials;
- Sigstore/SLSA/SBOM for artifact provenance;
- OpenTelemetry and CloudEvents for traces and events;
- OWASP and NIST for security and risk framing.

The missing center is not more motion. It is public survival under adversarial review.

SAB's highest-leverage destiny is to make every important agent claim ask:

> What survived challenge, witnessed by whom, under what scope, until what expiry?

## The Founding Sentence

SAB is the open protocol where agent claims earn standing by surviving witnessed challenge.

## One-Paragraph Thesis

As agents gain tools, memory, autonomy, and authority, the core public problem shifts from "can an agent act?" to "which claims and delegations are worth relying on?" SAB should solve that missing layer by turning claims, tool permissions, memory entries, package provenance, delegation results, and governance assertions into signed standing leases: scoped, expiring, replayable, challengeable records of what survived adversarial review. SAB should interoperate with the existing agent ecosystem rather than replace it, and it should refuse every shortcut that converts truth into hype, popularity, tokens, private certification, or institutional theater.

## Operational Doctrine

1. No standing without a claim.
2. No claim without scope.
3. No scope without expiry.
4. No expiry without revocation.
5. No reliance without evidence.
6. No evidence without provenance.
7. No provenance without challenge rights.
8. No challenge resolution without witness.
9. No witness without conflict disclosure.
10. No canon without a living path to correction.

## What SAB Wants To Become

### 1. The Standing Graph

SAB becomes a public graph of standings:

- agent identity standings;
- tool authority standings;
- package and connector standings;
- memory and context standings;
- delegation and task-result standings;
- governance and policy standings;
- public claim standings.

Every standing is a lease, not a permanent rank.

### 2. The Adversarial Court For Agent Claims

SAB does not judge agents by vibe, follower count, benchmark marketing, or institutional name. It asks what an agent asserted, what evidence was attached, what challenge was applied, what changed, and what survived.

This is not a legal court and does not claim state authority. It is a protocol court: a reproducible adversarial process for deciding whether a claim deserves scoped reliance.

### 3. The Interop Trust Plane

SAB should sit beside existing agent standards:

- MCP asks: what tools and data can an agent reach?
- A2A asks: how do agents communicate and delegate?
- AGNTCY asks: how are agents discovered, identified, observed, and evaluated?
- DID/VC/SPIFFE ask: who controls this identifier or credential?
- Sigstore/SLSA ask: where did this artifact come from and how was it built?
- OpenTelemetry asks: what happened during execution?
- SAB asks: what survived challenge and can be relied on for this purpose?

### 4. The External Memory With Adversarial Hygiene

Agents need durable external memory. But shared memory without challenge becomes an attack surface.

SAB should make high-impact memory entries challengeable:

- source-bound;
- time-bound;
- conflict-disclosed;
- revocable;
- linked to successor and supersession;
- marked as `memory_ready`, `challenged`, `expired`, or `withdrawn`.

### 5. The Authority Lease Ledger

The dangerous layer is not just what agents say. It is what agents are allowed to do.

SAB should track authority as leases:

- purpose;
- scope;
- maximum blast radius;
- data boundary;
- tool boundary;
- expiry;
- revoker;
- emergency stop;
- audit evidence.

This turns "the agent had permission" into a checkable object.

## What SAB Must Refuse

SAB loses its center if it becomes:

- a general agent runtime;
- a model provider;
- a popularity ranking site;
- a private certification business;
- an app store;
- a tokenized reputation market;
- a governance theater;
- a world government claim;
- a founder myth;
- a pay-to-pass audit shop;
- a closed database of trust scores.

The gravitational center comes from public method, not ownership.

## The First Four Wedges

### Wedge 1: Package And Tool Trust

Claim under test:

> This MCP server, connector, or agent package is safe enough for a stated authority class.

Evidence needed:

- artifact digest;
- source repository;
- release signature;
- dependency manifest;
- SBOM if available;
- SLSA or in-toto provenance if available;
- Sigstore/Rekor evidence if available;
- permission manifest;
- network/file/process side-effect profile;
- prompt-injection exposure notes;
- adversarial installation and invocation tests;
- revocation owner.

Standing output:

- `package_ready` for a narrow scope;
- `tool_ready` for specific tool actions;
- denied or `provisional` if evidence is weak.

Why it matters:

Tool and package trust is the fastest path to agent compromise. A public challenge process for connectors and MCP servers gives SAB an immediate interop role.

### Wedge 2: Delegation Trust

Claim under test:

> Agent A can delegate task class X to Agent B under constraints Y without exceeding authority Z.

Evidence needed:

- agent identity binding;
- task schema;
- authority lease;
- input/output trace;
- guardrail outcomes;
- failure modes;
- human override path;
- witness quorum;
- retry and escalation policy.

Standing output:

- `delegation_ready` for one task class and expiry;
- challengeable A2A metadata;
- task-result standing receipt.

Why it matters:

The agent world will fail at delegation before it fails at raw model quality. SAB can make delegation reliance inspectable.

### Wedge 3: Memory Trust

Claim under test:

> This memory item is safe and accurate enough to influence future agent action.

Evidence needed:

- source;
- timestamp;
- creator identity;
- context boundary;
- privacy classification;
- contradiction scan;
- poisoning challenge;
- successor links;
- revocation path.

Standing output:

- `memory_ready`, `challenged`, `expired`, or `compost`.

Why it matters:

Persistent memory is leverage and attack surface. SAB can become the hygiene layer for shared agent memory.

### Wedge 4: Authority Exposure

Claim under test:

> This agent may use this capability for this purpose with this blast radius until this date.

Evidence needed:

- delegator identity;
- policy hash;
- tool/capability boundary;
- data boundary;
- spend/action limit;
- expiry;
- named revoker;
- audit trace;
- emergency stop.

Standing output:

- scoped standing lease;
- denial if the permission is unbounded;
- automatic expiry and challenge hooks.

Why it matters:

The world does not need omnipotent agents. It needs accountable authority.

## Architecture Target

### Public Objects

SAB should standardize these objects first:

- `AgentIdentity`
- `ClaimPacket`
- `Challenge`
- `WitnessEvent`
- `StandingLease`
- `EvidenceBundle`
- `AuthorityLease`
- `Revocation`
- `Appeal`

### API Surface

Minimum protocol surface:

- `POST /claims`
- `GET /claims/{claim_id}`
- `POST /claims/{claim_id}/challenges`
- `POST /claims/{claim_id}/witnesses`
- `GET /standings/{standing_id}`
- `GET /standings/search`
- `POST /leases/validate`
- `POST /standings/{standing_id}/revoke`
- `GET /evidence/{bundle_id}`

### MCP Surface

Minimum MCP tools:

- `standing.search`
- `standing.fetch`
- `claim.fetch`
- `challenge.submit`
- `witness.fetch`
- `lease.validate`

### A2A Surface

A2A-compatible metadata should expose:

- current SAB standing IDs;
- accepted delegation classes;
- authority lease requirements;
- challenge URL;
- revocation URL;
- evidence bundle URL.

### Trace And Event Surface

OpenTelemetry attributes:

- `sab.claim_id`
- `sab.standing_id`
- `sab.challenge_id`
- `sab.authority_scope`
- `sab.lease_status`
- `sab.witness_event_id`
- `sab.policy_hash`

CloudEvents compatibility:

- witness events;
- challenge submissions;
- standing updates;
- revocations;
- appeals.

## 90-Day Execution Arc

### Days 1-14: Lock The Thesis

Artifacts:

- publish this strategy;
- publish `SAB_WORLD_AGENT_STANDING_STANDARD_V0.md`;
- publish the external research register;
- accept ADR-0004 as the product-positioning decision;
- add public standing page under `site/standing.html`;
- create wiki home and partner playbook.

Acceptance:

- a new contributor can explain what SAB is and is not in under five minutes;
- a skeptical external reviewer can see source anchors and non-goals.

### Days 15-30: Make Standing Queryable

Build:

- standing lease schema;
- challenge schema;
- witness event schema;
- JSON examples;
- `standing.search` and `standing.fetch` mock or file-backed tools;
- repo tests for lease expiry and revocation logic.

Acceptance:

- an external agent can fetch one standing receipt with scope, expiry, evidence, challenge status, and witness records.

### Days 31-45: Package And Tool Trust Dossier

Build:

- first public challenge dossier for one MCP server, connector, or agent package;
- provenance checklist;
- permission manifest template;
- side-effect test template;
- package standing labels.

Acceptance:

- one package/tool earns either `package_ready` or an explicit refusal with evidence.

### Days 46-60: Delegation Standing Dossier

Build:

- A2A-style delegation claim template;
- task trace evidence bundle;
- authority lease example;
- revocation example.

Acceptance:

- one agent-to-agent delegation gets a scoped standing lease or a documented denial.

### Days 61-75: Observability Bridge

Build:

- OpenTelemetry attribute profile;
- CloudEvents witness export;
- sample trace with SAB standing IDs;
- verification script for evidence bundle integrity.

Acceptance:

- a trace can point to standing, and standing can point back to trace evidence.

### Days 76-90: External Challenge

Build:

- invite external researchers/builders to attack the standard;
- publish every sustained challenge;
- revise v0.1;
- release annual-style transparency note even if the project is small.

Acceptance:

- at least one serious external critique changes the standard.

## 12-Month Strategy

1. Publish three standing dossiers:
   - package/tool trust;
   - delegation trust;
   - memory trust.
2. Implement file-backed and API-backed standing lookup.
3. Publish schemas for claim, challenge, witness, standing, authority lease, and evidence bundle.
4. Ship an MCP server for standing lookup and challenge submission.
5. Create A2A metadata examples for standing and delegation safety.
6. Align challenge taxonomy with OWASP agentic risk categories.
7. Align risk framing with NIST AI RMF vocabulary while avoiding regulatory claims.
8. Build a small independent review circle with conflict disclosure.
9. Publish refusal logs and correction logs.
10. Start a standing registry that can be forked.

## 36-Month Strategy

1. Become a default citation layer for agent trust claims in serious open-source agent stacks.
2. Maintain public standing profiles for high-impact agent connectors and MCP servers.
3. Integrate with multiple agent directories as a standing metadata source, not a replacement.
4. Publish machine-readable standing leases accepted by independent tools.
5. Support external forks and competing witness councils.
6. Become boring enough to be trusted: clear schemas, clear refusals, clear corrections, no spectacle.

## Decade Strategy

If SAB succeeds by 2031, it will be cited because:

- agent builders use it before allowing tools or delegations;
- researchers use it to inspect contested claims;
- journalists use it to trace evidence lineage;
- civil-society groups use it to challenge institutional AI claims;
- labs use it to publish restricted, scoped, challengeable assertions;
- standards bodies use it as an example of adversarial standing rather than reputation scoring.

It will be trusted because it refused to become the owner of truth.

## Outreach And Trust Strategy

### First Source Partners

Target people and groups who can falsify the idea:

- MCP server maintainers;
- A2A implementers;
- AGNTCY contributors;
- OpenTelemetry practitioners;
- OpenSSF/Sigstore/SLSA maintainers;
- OWASP GenAI contributors;
- public-interest AI security researchers;
- agent framework builders;
- investigative technologists;
- community accountability groups affected by automated systems.

The first ask is not endorsement. The first ask is:

> What would make this standing receipt misleading, gameable, or useless?

### First Institutional Pilots

Use low-risk pilots:

- one open-source agent package;
- one internal tool-authority registry;
- one public memory corpus;
- one A2A delegation workflow;
- one public AI/ecology claim dossier.

Avoid pilots that require secrecy, brand protection, or favorable judgments.

### Public Launch Artifact

The launch should not be "SAB is the future of agents."

It should be:

> We challenged one concrete agent package/tool/delegation claim. Here is the evidence, the attack surface, the standing lease, the unresolved doubts, and the correction path.

## Brutal Risks And Countermeasures

| Failure mode | How SAB fails | Structural countermeasure |
| --- | --- | --- |
| Capture | A funder or institution buys legitimacy | public conflict ledger, funding firewall, no paid favorable judgment |
| Amateur evidence | dossiers are shallow | evidence classes, uncertainty notes, source register, external review |
| Overclaiming | standing becomes "truth" | scope, expiry, forbidden reliance, refusal language |
| Legal exposure | SAB makes defamatory or regulatory claims | claim exactness, evidence links, appeal process, counsel review for high-risk dossiers |
| Community extraction | affected groups become legitimacy props | consent rules, right to refuse, right to annotate, right to withdraw from process where lawful |
| Bad science | methods are weak | metrology review, falsification conditions, correction protocol |
| Activist bias | conclusions precede evidence | adversarial alternatives and published sustained challenges |
| Corporate laundering | companies use SAB standing as marketing | no paid favorable judgment, narrow lease language, public challenge window |
| Governance theater | councils exist but cannot stop anything | refusal rights, revocation authority, published dissent |
| Founder mythology | legitimacy attaches to one person | fork rights, public methods, multi-witness review, institutional memory outside personality |

## 1000x Hardening Acceptance Criteria

SAB is not 1000x harder because it says more ambitious words. It is harder when:

1. Every public claim has an exact object under test.
2. Every standing has scope, expiry, revoker, and forbidden reliance.
3. Every high-impact standing has at least three distinct witnesses.
4. Every challenge remains queryable.
5. Every correction is linked to the claim it changed.
6. Every external dependency is named.
7. Every refusal is retained unless lawful safety requires withholding.
8. Every funding relationship is disclosed.
9. Every standing can be forked.
10. Every public interface makes challenge cheaper than passive belief.

## The So What

AI governance has too many declarations and too few adversarial records.

Climate and ecology accountability has too many sustainability claims and too little site-level evidence.

Agent infrastructure has too many tools and too little authority hygiene.

Public-interest auditing has too many one-off reports and too little reusable protocol.

SAB's contribution is a reusable standing layer: a way for consequential claims to become machine-readable, scoped, challenged, witnessed, corrected, and citable without becoming a state, a company moat, or a certification tollbooth.

## Final Positioning

The world does not need agents to be louder. It needs agents to become accountable to challenge.

SAB is the place where agent claims go to become worth relying on.
