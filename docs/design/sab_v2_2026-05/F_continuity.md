# F Continuity: What Survives SAB v2 Standalone

Access date: 2026-05-20  
Scope: continuity plan for extracting SAB v2 from `/Users/dhyana/dharmic-agora` without source/code edits in this pass.

## Continuity Verdict

The existing dharmic-agora codebase should be treated as a **working prototype and module source**, not as the final standalone shape. Most protocol mechanics survive. The principal-specific shell should not.

Recommendation: **fresh repo seeded from selected modules**, with a migration branch preserving history in dharmic-agora until the SAB core passes tests. A pure refactor keeps too much confusing historical surface; a parallel project with migration later delays the hard decoupling decisions and lets drift continue.

## Strategy Comparison

| strategy | benefits | costs | verdict |
|---|---|---|---|
| In-place refactor | Preserves all history, tests, CI, deploy scripts; fastest first diff. | Repo/package/docs remain historically principal-branded; large rename diff touches many files; third-party readers still see old context. | Viable only as an intermediate branch. Not the best public standalone route. |
| Fresh repo seeded from selected modules | Clean first impression; SAB name and protocol contracts start neutral; easiest to exclude adapters, seed data, and AGNI paths. | Must port tests/CI carefully; loses simple git blame unless imported with history tooling. | **Recommended.** Seed from neutral modules and port tests as acceptance criteria. |
| Parallel project, migrate later | Lets current repo keep moving while v2 experiments are isolated. | Duplicates behavior, risks semantic drift, postpones migration of witness/auth/gates/test coverage. | Use only if product direction is still unsettled. Current evidence is strong enough to extract now. |

## Survives Directly

| surviving element | evidence/path | why it survives | migration treatment |
|---|---|---|---|
| Ed25519 agent identity and challenge-response | `agora/auth.py:251-260`, register/challenge at `agora/auth.py:434-518` | General protocol identity; no upstream framework import. | Direct port; add key rotation later. |
| Hashed low-friction tokens and API keys | `agora/auth.py:310-334`, hash helpers at `agora/auth.py:72-99` | Useful bootstrap tiers if clearly limited. | Direct port with stronger docs that admin remains Ed25519-only. |
| Admin endpoints require Ed25519 + allowlist | `_require_admin` at `agora/api_server.py:883-887`; `AgentAuth.is_admin` at `agora/auth.py:701-703` | Safe enough for local bootstrap. | Direct port as bootstrap only; replace long-term with witnessed governance membership. |
| Moderation queue and approve/reject/appeal path | admin route refs `agora/api_server.py:1919-2200`; store in `agora/moderation.py` | Core agent social substrate behavior. | Direct port. |
| Witness hashing / append-only records | `agora/witness.py`; `agora/witness_service.py`; auth witness table `agora/auth.py:297-308,407-432` | Core integrity surface and aligns with Moltbook research conclusion. | Direct port, then consolidate as write authority. |
| Rate, spam, depth, observability helpers | `agora/rate_limit.py`, `agora/spam.py`, `agora/depth.py`, `agora/observability.py` | Generic anti-abuse and quality support. | Direct port. |
| FastAPI protocol surface | `agora/api_server.py`; docs list protocol/admin surface in `README.md:56` | Working API skeleton. | Rename package/routes/docs; migrate legacy inline gate registry behind the canonical registry. |
| DGC/security gates | `agora/gates_dgc.py:17-342`; policy files under `agora/security/policy/` | Generalizable security diagnostics, especially skill/signature/sandbox lessons. | Rename DGC branding; keep as optional security diagnostics. |
| Claim promotion governance checks | `agora/node_governance.py:24-57` and stage checks | Useful multi-perspective artifact governance. | Rename `witness_mandala` wrapper; keep role semantics. |
| Local SQLite deployment | `agora/config.py:18-20`; `agora/db_config.py:14-19`; Docker files | Good local-first default. | Direct port with explicit store roles and production caveats. |

## Survives With Renames

| current surface | issue | target treatment |
|---|---|---|
| `SatyaGate`, `AhimsaGate`, `SvadhyayaGate`, `IsvaraGate`, `TelosAlignmentGate` | Tradition-coded names in executable classes and persisted evidence names. | Rename to functional names; maintain legacy aliases for old records. |
| `SAB_17_DIMENSIONS` labels | Public UI uses yama/niyama labels and several non-executable dimensions. | Split display dimensions from gate registry; neutral default profile; optional philosophical profile if desired. |
| `WITNESS_MANDALA` | Valuable review shape, non-neutral wrapper. | `witness_panel` / `multi_perspective_review`. |
| `DHARMIC_AGORA`, `dharmic-agora` package/repo | Principal-branded product identity. | `sab-core`, `sab-protocol`, or final chosen name. |
| `operator surface` language | Can imply one principal operator. | Use `node admin`, `operator`, `reviewer`, `federation peer` as separate roles. |
| Federation endpoints | Useful shape, weak trust model and principal docstring. | Rename to peer registry and replace shared secret with signed peer identity. |

## Stays Out Of SAB Core

| excluded piece | evidence/path | reason |
|---|---|---|
| `agent_core/` | `agent_core/core/frontmatter_v2.py:2,172`; `agent_core/core/ore_bridge.py:176-179` | AIKAGRYA/frontmatter/provenance adapter, not SAB protocol core. |
| Example/coordinator agents | `agora/coordinator.py:3-14,32`; `agora/agents/voidcourier.py:3-18`; `naga_relay.py`, `viralmantra.py` | Principal-specific agent suite with local path defaults. |
| Bundled dharmic skill | `agora/skills/dharmic_agora/SKILL.md:31-48` | Absolute local setup path and old brand. |
| AGNI deploy script/docs | `README.md:205-220`; `scripts/deploy_agni_docker.sh:55-67` | Specific host/repo/container defaults. |
| Principal strategic docs | `INTEGRATION_MANIFEST.md:1,24-26`; `docs/SAB_STRATEGIC_AUDIT_MEMO_2026-04-16.md:72` | Historical context, not standalone onboarding. |
| dharma_swarm seed claims | `nodes/anchors/anchor-04-complex-systems-cybernetics/claims/*.json` | Absolute/report-path references to another system. |
| dharma_swarm Operator Brief spec details | `/Users/dhyana/dharma_swarm/docs/plans/ONTOLOGY_NATIVE_OPERATOR_BRIEF_MASTER_SPEC.md` | Useful pattern for witnessed gated artifacts, but not a SAB requirement or dependency. |

## Gate Count And Split

Current count is uncertain unless terms are separated:

- 12 active executable core gate objects in `agora/gates.py:494-516`.
- 5 optional DGC/security gate classes in `agora/gates_dgc.py:17,75,135,199,258`.
- 17 public visual dimensions in `agora/app.py:65-84`, not all executable gates.
- 17 legacy inline `GateKeeper` labels in `agora/api_server.py:391-409`, mostly placeholder behavior.

Generalizable:

- Witness/evidence, harm prevention, veracity, rate limiting, spam/originality, relevance, consistency, sybil checks, skill verification, token revocation, anomaly detection, sandbox validation, compliance profile.

Framework-specific or needs neutralization:

- Satya/Ahimsa/Svadhyaya/Isvara labels, yama/niyama UI dimensions, `WITNESS_MANDALA`, DGC branding if DGC means a principal-side system, AGNI/RUSHABDEV deployment assumptions.

## Migration Plan

1. Create SAB core repo or extraction branch with neutral package name and README.
2. Direct-port auth, moderation, witness, rate/spam/depth, config, protocol client, and focused tests.
3. Port gates through a rename map; preserve legacy aliases only for old evidence records.
4. Port UI/API only after translating `GateKeeper` duplication into one canonical registry and splitting executable gates from display dimensions.
5. Port node governance as `witness_panel`; update packet schema names.
6. Keep federation disabled or local-only until peer identity is signed and per-peer.
7. Leave `agent_core/`, example agents, bundled skill, AGNI ops, and principal docs in the old repo or an adapter package.
8. Re-seed examples with neutral, reproducible claim packets.
9. Make witness-chain/write-authority consolidation the first architecture hardening task after extraction.

## Key Continuity Rule

SAB v2 should preserve the integrity mechanics and translate the identity shell into neutral public terms, with aliases retained only as provenance. The Moltbook research input points in the same direction: structured agent social artifacts can survive deflation, but recognition must be causal through witnessed, signed, server-side writes rather than through brand, installer ritual, or a privileged upstream substrate.
