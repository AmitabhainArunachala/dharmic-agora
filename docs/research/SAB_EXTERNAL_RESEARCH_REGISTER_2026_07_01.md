# SAB External Research Register: Agent Trust And Interop

Date: 2026-07-01

Purpose: primary-source register for hardening SAB into the standing/adjudication layer for agent ecosystems.

## Research Verdict

The agent ecosystem is converging around separate layers:

- model-to-tool context and tool invocation;
- agent-to-agent communication;
- agent discovery and schema description;
- workload identity;
- artifact signing and software supply-chain provenance;
- telemetry and traces;
- security risk frameworks.

No inspected primary source claims to solve adversarial standing: the question of whether an agent, tool, package, memory, delegation, or authority grant has survived scoped challenge and should be trusted for a particular purpose until a particular expiry.

That is SAB's opening.

## Source Register

| Source | What it establishes | SAB implication |
| --- | --- | --- |
| Model Context Protocol introduction: https://modelcontextprotocol.io/introduction | MCP is an open standard for connecting AI applications to external systems, data sources, tools, and workflows. | SAB should expose MCP tools for standing lookup, challenge submission, witness retrieval, and claim lease validation. |
| OpenAI MCP guide: https://developers.openai.com/api/docs/guides/tools-connectors-mcp | OpenAI describes MCP as the Model Context Protocol path for connecting models to tools, connectors, and remote MCP servers. | SAB's MCP surface should be read-first and citation-friendly: `search`, `fetch`, `standing.lookup`, `challenge.submit`, `witness.fetch`. |
| A2A Protocol docs: https://a2a-protocol.org/latest/ | A2A is an open standard for communication and collaboration between opaque agentic applications. It explicitly positions MCP as agent-to-tool and A2A as agent-to-agent. | SAB should not compete with A2A. It should provide standing receipts that A2A agents can advertise, request, challenge, and revoke. |
| OpenAI Agents SDK docs: https://openai.github.io/openai-agents-python/ | Modern agent runtimes expose agents, handoffs, tools, guardrails, sessions, sandbox agents, human-in-the-loop, MCP integration, and tracing. | SAB should consume traces and guardrail outcomes as evidence, not rebuild agent loops. |
| AGNTCY docs: https://docs.agntcy.org/ | AGNTCY targets an Internet of Agents with discovery, identity, messaging, observability, and evaluation components. | SAB should be a standing/adjudication profile that can attach to agent directory entries and interop with agent identity/observability rather than becoming a rival directory. |
| W3C DID Core: https://www.w3.org/TR/did-core/ | DIDs are decentralized identifiers that enable verifiable, decentralized digital identity and cryptographic control proof. | SAB agent identities should map to DID-compatible subject identifiers without requiring DID as the only identity rail. |
| W3C Verifiable Credentials Data Model 2.0: https://www.w3.org/TR/vc-data-model-2.0/ | VCs express claims by issuers about subjects, secured against tampering, with issuer-holder-verifier roles. | SAB standings can be represented as verifiable credentials, but the credential is not the standing; the challenge/witness lineage is. |
| OpenTelemetry overview: https://opentelemetry.io/docs/what-is-opentelemetry/ | OpenTelemetry is a vendor-agnostic framework for telemetry data including traces, metrics, and logs; it is not a backend. | SAB should define semantic attributes for claim IDs, standing IDs, challenge IDs, and authority leases in agent traces. |
| SLSA 1.1 about: https://slsa.dev/spec/v1.1/about | SLSA provides supply-chain security guidelines and tamper-resistant evidence from source to binary. | SAB should require SLSA/SBOM-style provenance for package/tool trust claims and avoid substituting social proof for artifact handling evidence. |
| Sigstore docs: https://docs.sigstore.dev/ | Sigstore signs and verifies artifacts, associates them with identity, and records signing events in a transparency log. | SAB should accept Sigstore/Rekor evidence as artifact provenance, then challenge claims about what that provenance means. |
| SPIFFE overview: https://spiffe.io/docs/latest/spiffe-about/overview/ | SPIFFE provides standards for secure workload identity in dynamic heterogeneous environments. | SAB should treat SPIFFE/SVID as runtime workload identity evidence, not as authority by itself. |
| OWASP GenAI Security Project: https://genai.owasp.org/ | OWASP maintains open guidance for GenAI and agentic AI security, including agentic governance and security publications. | SAB should align challenge types with known agentic risks: memory/context poisoning, tool misuse, authority exposure, supply-chain compromise. |
| NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework | NIST AI RMF is voluntary risk management guidance; NIST is developing critical-infrastructure AI risk management profile material. | SAB should use NIST language for risk framing and avoid claiming regulatory authority. |
| CloudEvents: https://cloudevents.io/ | CloudEvents is a CNCF specification for describing event data in a common way. | SAB witness events should be CloudEvents-compatible so evidence can move across systems. |
| RFC 2119: https://www.rfc-editor.org/rfc/rfc2119 | Defines MUST, SHOULD, MAY requirement language for specifications. | SAB normative specs should keep RFC-style requirement discipline. |

## Landscape Map

| Layer | Existing center of gravity | What remains missing | SAB role |
| --- | --- | --- | --- |
| Agent-to-tool | MCP | Tool trust, authority scope, tool-result standing | Standing receipts for tool claims and authority grants |
| Agent-to-agent | A2A, AGNTCY/SLIM | Delegation trust, task-result challenge, witness quality | Challenge-survived delegation and task standing |
| Agent discovery | AGNTCY Agent Directory, agent cards | Ranking-as-trust attack resistance | Directory-adjacent standing graph, not another popularity rank |
| Identity | DID, VC, SPIFFE, OIDC | Authority meaning, scope, expiry, revocation | Claim leases bound to identities and revokers |
| Artifact provenance | Sigstore, SLSA, SBOM | What provenance proves about safety or behavior | Adversarial interpretation of provenance claims |
| Observability | OpenTelemetry, traces/logs/metrics | Which traces count as evidence for standing | Evidence-grade trace semantics and receipt hashing |
| Risk and security | OWASP GenAI, NIST AI RMF | Live claim-level adjudication and correction | Dynamic challenge, witness, correction, and revalidation |

## Non-Negotiable Conclusion

SAB should become:

> The open standing graph for agents: a protocol where claims, delegations, tools, packages, memories, and authority grants earn scoped, expiring, challengeable standing through witnessed adversarial review.

SAB should not become:

- another agent runtime;
- a model provider;
- a social network;
- a ranking site;
- a reputation token;
- an agent marketplace;
- a private certification authority.

## Critical Research Gaps To Close

1. Exact A2A extension point for SAB standing receipts.
2. Exact MCP tool schema for standing/challenge/witness lookup.
3. VC representation for claim leases and standing receipts.
4. OpenTelemetry semantic convention draft for agent claim/witness events.
5. SLSA/Sigstore ingestion policy for package/tool provenance evidence.
6. SPIFFE/OIDC/DID identity binding policy.
7. OWASP-aligned challenge taxonomy for agentic risks.
8. External review from at least one practitioner in each major layer.
