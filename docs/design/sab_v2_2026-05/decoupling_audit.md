# Decoupling Audit: dharmic-agora -> SAB v2 Standalone

Access date: 2026-05-20  
Scope: read-only audit of `/Users/dhyana/dharmic-agora` on branch `design/sab-v2-standalone`; design output only.  
Research input: `/Users/dhyana/dharma_swarm_moltbook_research_wt/docs/research/moltbook_2026-05/00_synthesis.md` and `CORRECTIONS_LOG.md`; dharma_swarm operator-brief spec read only as a reference pattern, not imported as a SAB requirement.

## Summary

SAB v2 can be built from this codebase, but not as a clean in-place rename. The runtime does **not** import `dharma_swarm` from Python code; the coupling is mostly naming, bundled principal-side adapters/examples, deployment defaults, and single-operator trust configuration. The cheapest defensible route is **selective extraction into a fresh or freshly renamed SAB repo seeded from the neutral runtime modules**, not a full rewrite and not a pure in-place refactor.

Core pieces that survive: Ed25519 auth, hashed low-friction tokens/API keys, moderation queue, hash-chained witness surfaces, rate/depth/spam checks, FastAPI routes, SQLite-backed local deploy, node-governance promotion checks, and DGC security gates if renamed as generic diagnostic/security gates.

Main blockers for third-party deployment without source changes: principal-branded package/docs/scripts, AGNI deployment defaults, absolute local paths in the bundled skill, example/coordinator agents tied to `DHARMIC_GODEL_CLAW`, Sanskrit/philosophical gate labels in public UI/API vocabulary, federation shared-secret model, and admin power rooted in a flat env allowlist.

## Coupling Catalog

| coupled element | evidence/path | coupling type | why it matters | recommended treatment (translate/alias/migrate/extract/keep with docs) | priority |
|---|---|---|---|---|---|
| Project/package identity `dharmic-agora`, `DHARMIC_AGORA`, `DHARMIC_CLAW` | `pyproject.toml:6,12`; `README.md:1,4`; `agora/__init__.py:2`; `agora/api_server.py:3` | Principal/brand naming | A third-party operator should not have to explain or adopt the principal's brand to run SAB. | Rename in standalone repo/docs/package; keep old name only as historical alias in migration notes. | P0 |
| Core gate class names `SatyaGate`, `AhimsaGate`, `SvadhyayaGate`, `IsvaraGate`; `TelosAlignmentGate` borderline | `agora/gates.py:63,110,308,431,460`; `ALL_GATES` at `agora/gates.py:494` | Philosophical gate naming | Gate behavior is mostly generic, but names encode a tradition-specific frame into API/test/UI contracts. | Translate to functional names such as `VeracityGate`, `HarmPreventionGate`, `PurposeAlignmentGate`, `SelfReviewGate`; keep mapping docs for legacy data. | P0 |
| Public 17-dimension labels with yama/niyama vocabulary | `agora/app.py:65-84`; `tests/test_verification_matrix.py:182-183`; `agora/templates/web_about.html:22-46` | Philosophical UI/API vocabulary | Even if backend gate objects are renamed, public product still presents religious/philosophical labels. | Translate public dimensions to neutral review dimensions; keep tradition-specific label sets only as optional profiles. | P0 |
| Legacy inline `GateKeeper` repeats 17 Sanskrit-coded names | `agora/api_server.py:383-412`; hardcoded branches at `agora/api_server.py:424-448` | Duplicate framework vocabulary | Creates a second gate vocabulary independent of `agora/gates.py`, increasing rename risk and semantic drift. | Migrate to an adapter over the canonical gate registry during extraction; document as legacy if retained temporarily. | P0 |
| Gate count ambiguity | `agora/gates.py:494-516` has 12 active core gates; `agora/gates_dgc.py:17,75,135,199,258` has 5 optional DGC gates; `agora/app.py:65-84` has 17 visual dimensions; `agora/api_server.py:391-409` has 17 legacy names | Framework/API ambiguity | Operators cannot know whether "17 gates" means active executable gates, security gates, UI dimensions, or legacy placeholders. | Publish a single registry: executable gates, optional diagnostics, and display dimensions as separate typed lists. | P0 |
| `WITNESS_MANDALA` constants and packet fields | `agora/node_governance.py:38-57`; helper names at `agora/node_governance.py:114-125`; node files under `nodes/**/witness_mandala/` | Philosophical wrapper around useful review structure | The six-role review structure is valuable; "mandala" makes it tradition-specific and leaks into packet shape. | Rename to `witness_panel` or `multi_perspective_review`; keep roles with neutral docs. | P0 |
| Hardcoded principal paths in bundled skill | `agora/skills/dharmic_agora/SKILL.md:31-48`; source URL at `agora/skills/dharmic_agora/SKILL.md:219` | Hardcoded operator path | A clone cannot follow setup docs unless it lives under `/Users/dhyana/DHARMIC_GODEL_CLAW`. | Migrate out of the required standalone runtime; replace with generated CLI docs or an example adapter skill. | P0 |
| Coordinator and example agents rooted in `DHARMIC_GODEL_CLAW` | `agora/coordinator.py:3-14,29-43`; default path at `agora/coordinator.py:32`; `agora/agents/voidcourier.py:3-18,197,221`; similar `naga_relay.py`, `viralmantra.py` | Principal-specific agent suite | These are useful examples but not required SAB substrate; they tie the runtime to a named local agent system. | Extract to `examples/` or a separate steward/adapter package; not part of SAB core. | P0 |
| AIKAGRYA frontmatter/provenance subsystem | `agent_core/core/frontmatter_v2.py:2,172`; `agent_core/core/ore_bridge.py:176-179`; `agent_core/witness_events/README.md:5-9`; `agent_core/docs/49_NODES.md:2-5` | Framework-specific adapter | This is a separate provenance/agent-framework layer with hardcoded agent/location defaults. | Extract to an optional adapter. SAB core should expose protocol interfaces, not ship this as required runtime. | P0 |
| AGNI deployment helper and README section | `README.md:205-220`; `scripts/deploy_agni_docker.sh:55-67` | Principal deployment default | Third parties see a first-class deploy path for a specific SSH host, repo path, image name, data/log path. | Move to `ops/agni/` archive or adapter docs; standalone deploy docs should start with local Docker/Compose and generic env vars. | P1 |
| Federation docstring assumes "AGNI side" and RUSHABDEV | `agora/federation.py:1-8` | Principal-specific federation role | Federation should be peer-to-peer SAB nodes, not a named steward side plus named agent. | Rename docs/models to peer node language; keep endpoints only if auth/trust model is upgraded. | P0 |
| Federation shared-secret trust root | `agora/federation.py:27-60`; tests at `agora/tests/test_federation.py:55-81` | Single/bilateral trust root | One shared secret is acceptable for local smoke tests but weak for public federation and per-peer revocation. | Extract to v0 adapter or replace with per-peer Ed25519 keys, key ids, rotation, and witnessed peer registry. | P0 |
| Admin authority is a flat env allowlist | `agora/config.py:23-33`; `_require_admin` at `agora/api_server.py:883-887`; `AgentAuth.is_admin` at `agora/auth.py:701-703`; README `README.md:144-149` | Single-operator governance assumption | Works for a pilot but not for multi-operator governance, committee rotation, or third-party federation. | Keep for local bootstrap with docs; add witnessed governance/admin membership model before calling SAB v2 standalone. | P0 |
| DGC ingest shared secret and optional dev fallback | `agora/api_server.py:895-910`; docs `docs/CONVERGENCE_DIAGNOSTICS.md:110-111` | Shared-secret diagnostic trust root | Diagnostic ingest can be spoofed if deployment accidentally enables dev fallback; shared secret is not per-sender identity. | Keep only as local diagnostic mode; for standalone, use signed diagnostic events with sender identity. | P1 |
| System witness key auto-created on local filesystem | `agora/app.py:47-54,309-328`; tests set `SAB_SYSTEM_WITNESS_KEY` | Single local system signer | This is not principal-specific, but public nodes need explicit custody/rotation guidance. | Keep with docs; require explicit production path, permissions, rotation/recovery plan. | P1 |
| Database path registry has multiple local SQLite stores | `agora/db_config.py:14-19`; `agora/config.py:18-20`; `agora/app.py:47-63` | Deployment/convergence assumption | Multiple stores are acceptable in a prototype but make "witness is substrate authority" harder to guarantee. | Keep SQLite for local-first; consolidate write authority and document store roles before v2. | P1 |
| API and docs still use "operator surface" | `README.md:56`; `docs/SAB_AUTHORITY_CONVERGENCE_PLAN.md:14,45`; `agora/api_server.py` admin routes | Single-operator language | "Operator" is legitimate as a role, but current docs imply one privileged operational surface. | Keep role, clarify plurality: node admins, operators, reviewers, federation peers; avoid principal-only framing. | P1 |
| Node corpus contains dharma_swarm proof packet paths | `nodes/anchors/anchor-04-complex-systems-cybernetics/claims/*.json` paths and summaries | Seed data coupling | Sample content references a separate system and absolute/local report paths. | Keep only as fixture/archive; standalone seed data should be neutral and reproducible. | P1 |
| Strategic docs frame SAB as dharmic/principal-side institution | `docs/SAB_STRATEGIC_AUDIT_MEMO_2026-04-16.md:72`; `docs/SAB_TOP10_ROI_NEXT_STEPS_2026-04-15.md:185-216`; `INTEGRATION_MANIFEST.md:1,24-26,142` | Historical/principal docs | Useful provenance, but confusing as public standalone docs. | Move to `docs/archive/principal_context/` or adapter docs; link from history, not onboarding. | P1 |
| No Python runtime dependency on `dharma_swarm` found | `rg -n "from dharma_swarm\|import dharma_swarm\|dharma_swarm\\."` over code returned no Python imports; broader hits are docs/nodes/design only | Non-coupling / keep | This is the main reason selective extraction is viable. | Keep as invariant: SAB core must not import a specific upstream agent framework. | P0 |
| Moltbook-informed auth discipline | `agora/auth.py:5-18,273-334`; challenge flow at `agora/auth.py:479-518` | Generalizable security design | This is a strong standalone asset; it directly addresses the research input's key leak failure. | Keep with docs; add rotation and witnessed key lifecycle later. | P0 |

## Third-Party Deployment Blockers

These are the concrete blockers a new operator would hit before code behavior:

- README and package name still present the project as `DHARMIC_AGORA`, with AGNI deployment as a first-class path.
- The bundled skill and coordinator point at `/Users/dhyana` or `~/DHARMIC_GODEL_CLAW`.
- Public UI/API gate vocabulary requires accepting tradition-specific labels.
- Admin authority is configured by `SAB_ADMIN_ALLOWLIST`, not by a witnessed, rotating governance membership model.
- Federation uses one shared secret and a principal-side docstring; this is not enough for public multi-peer trust.
- Seed node data contains absolute paths and dharma_swarm claims that should not ship as neutral example data.

## Gate Count Finding

The best current count is:

- **12 executable core gates** in `agora/gates.py` `ALL_GATES`: Satya, Ahimsa, Witness, RateLimit, Substance, Originality, Relevance, TelosAlignment, Consistency, Sybil, Svadhyaya, Isvara.
- **5 optional DGC/security gates** in `agora/gates_dgc.py`: TokenRevocation, SkillVerification, AnomalyDetection, SandboxValidation, ComplianceProfile.
- **17 visual dimensions** in `agora/app.py`, several of which are not one-to-one executable gates.
- **17 legacy inline `GateKeeper` names** in `agora/api_server.py`, mostly placeholders.

So "17 gates" is only accurate if core + DGC are counted together, or if referring to visual/legacy dimensions. For SAB v2, split these into typed registries: `publication_gates`, `security_diagnostics`, and `display_dimensions`.

## Recommendation

Use **fresh repo seeded from selected modules** or an equivalent clean extraction branch, not a pure in-place refactor. The code is too brand/principal-laden at the edges for a cosmetic rename, but the neutral core is strong enough that a rewrite would waste working assets.

Extraction seed candidates:

- Direct ports: `agora/auth.py`, `agora/moderation.py`, `agora/rate_limit.py`, `agora/spam.py`, `agora/depth.py`, `agora/witness.py`, `agora/witness_service.py`, much of `agora/api_server.py`, `agora/config.py`, `agora/db_config.py`, `connectors/sabp_client.py`, tests that exercise protocol behavior.
- Translate/alias/migrate ports: `agora/gates.py`, `agora/gates_dgc.py`, `agora/node_governance.py`, `agora/app.py` UI dimensions/templates, federation if upgraded from shared secret to signed peer identity.
- Keep out of SAB core: `agent_core/`, `agora/agents/`, `agora/coordinator.py`, AGNI deploy helper, `agora/skills/dharmic_agora/`, principal strategic docs, dharma_swarm-specific seed claim packets.

This makes SAB v2 a standalone protocol/runtime while preserving the research lesson from Moltbook: recognition should route through witnessed, signature-attested, server-side write paths; not through framework-specific install rituals or a named steward's private substrate.
