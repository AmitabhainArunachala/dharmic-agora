# Experiment Chain: From SAB Thesis To Agent Standing Infrastructure

This chain turns the standing-plane thesis into increasingly public, falsifiable work.

## Experiment 0: Static Standing Objects

Question:

> Can SAB express a standing lease clearly enough that an outside reviewer understands what is and is not being claimed?

Build:

- JSON schema for `ClaimPacket`;
- JSON schema for `Challenge`;
- JSON schema for `WitnessEvent`;
- JSON schema for `StandingLease`;
- one fully populated example;
- one intentionally refused example.

Pass condition:

- a reviewer can identify allowed reliance, forbidden reliance, expiry, revoker, evidence, and unresolved challenge without asking the founder.

Kill condition:

- the standing object collapses into a vague score or badge.

## Experiment 1: Package And Tool Trust Dossier

Question:

> Can SAB evaluate one agent package, MCP server, or connector without becoming a certification tollbooth?

Build:

- artifact digest record;
- dependency and permission inventory;
- provenance evidence;
- side-effect profile;
- prompt-injection exposure note;
- adversarial test log;
- standing lease or refusal.

Pass condition:

- the package/tool gets a narrow, useful standing or an evidence-based refusal.

Kill condition:

- maintainers can buy favorable wording, or the review depends on private undocumented judgment.

## Experiment 2: Delegation Standing Dossier

Question:

> Can SAB make agent-to-agent delegation safer without replacing A2A?

Build:

- delegation claim packet;
- task class definition;
- authority lease;
- trace evidence;
- failure-mode review;
- witness record;
- A2A metadata example.

Pass condition:

- another agent can inspect standing before delegating.

Kill condition:

- standing is too vague to change delegation behavior.

## Experiment 3: Memory Standing Dossier

Question:

> Can SAB make durable agent memory safer without blocking all useful persistence?

Build:

- memory source record;
- privacy classification;
- poisoning challenge;
- contradiction scan;
- expiry and supersession path;
- `memory_ready` or `disputed` label.

Pass condition:

- a future agent can decide whether to use, ignore, narrow, or challenge the memory item.

Kill condition:

- the memory label becomes an unchallengeable truth stamp.

## Experiment 4: MCP Standing Server

Question:

> Can agents query standing through a normal tool interface?

Build MCP tools:

- `standing.search`;
- `standing.fetch`;
- `claim.fetch`;
- `challenge.submit`;
- `witness.fetch`;
- `lease.validate`.

Pass condition:

- an external agent can fetch standing, inspect scope, and submit a challenge.

Kill condition:

- the MCP surface only returns summaries and hides evidence.

## Experiment 5: Trace And Event Interop

Question:

> Can execution traces become evidence without becoming surveillance sludge?

Build:

- OpenTelemetry attribute profile;
- CloudEvents witness export;
- evidence hash verification script;
- trace redaction policy.

Pass condition:

- a standing receipt can cite a trace and a trace can cite a standing receipt.

Kill condition:

- traces expose sensitive data or are too incomplete to support challenge.

## Experiment 6: External Challenge Round

Question:

> Can serious outsiders improve the standard by attacking it?

Build:

- public call for adversarial review;
- issue template for challenge;
- sustained-challenge log;
- v0.1 revision;
- transparent "what changed" report.

Pass condition:

- at least one external critique materially changes the standard.

Kill condition:

- SAB treats critique as branding risk instead of protocol input.

## Experiment 7: Cross-Directory Standing

Question:

> Can SAB attach standing to agent directory entries without becoming the directory?

Build:

- sample AGNTCY-style standing metadata;
- A2A agent-card standing metadata;
- DID/VC standing representation;
- revocation demo.

Pass condition:

- directory entries can display or consume SAB standing while the evidence remains forkable.

Kill condition:

- SAB becomes a popularity index or central registry bottleneck.

## Long Arc

The sequence is:

1. express standing;
2. test standing;
3. query standing;
4. attach standing to agent interop;
5. make standing challengeable by outsiders;
6. make standing forkable.

Only after that should SAB talk about field-wide adoption.
