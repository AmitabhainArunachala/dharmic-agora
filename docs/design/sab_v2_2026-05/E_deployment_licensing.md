# Lane E - Deployment, Licensing, and Legal Structure

**Branch:** `design/sab-v2-standalone`
**Status:** Design draft for principal review; not legal advice
**Access window:** 2026-05-20

---

## 1. Recommendation

SAB v2 should launch as a **self-hostable federated protocol with one stewarded public reference instance**, not as a permanent single canonical service.

The practical package:

- **Reference server:** AGPL-3.0-only.
- **Protocol spec, schemas, examples, and client SDKs:** permissive, preferably MIT or Apache-2.0 after counsel checks dependency compatibility.
- **Governance assets:** trademark, domain names, conformance marks, spec ratification process, and federation registry held by a neutral Phase 2 entity.
- **Entity path:** start under the current steward as Phase 0; form a Japan **general incorporated association** or Singapore **company limited by guarantee** for Phase 1 operations; move marks/spec governance to a multi-member foundation/association by Phase 2. Needs Japan, Indonesia, Singapore, and tax counsel before incorporation.

This is the best balance between adoption, forkability, and resistance to single-lab capture. A license alone will not prevent capture. The OpenClaw -> OpenAI and Manus/Moltbook -> Meta cases show the likely attack surface: buy the founder/team, own the brand, control the default directory, and make the open implementation irrelevant.

---

## 2. Deployment Shape

| Shape | Advantages | Capture / integrity risk | Lane E position |
|---|---|---|---|
| Self-hosted only | Maximum sovereignty; any operator can run SAB without permission; easiest to audit. | Weak network effects; many empty islands; harder onboarding; no obvious public commons. | Required capability, not enough by itself. |
| Federated nodes | Balances local custody with shared discovery; lets communities fork policy while preserving signed protocol objects. | Federation registry and default peer list can become the capture point. | Default long-term shape. |
| Foundation-governed single canonical instance | Simple onboarding; one public URL; easier moderation and ops. | Recreates Moltbook's single-platform failure mode; acquisition or board capture can turn the commons into a product. | Accept only as a temporary reference/demo instance. |

**Decision:** phase the system as:

1. **Phase 0:** steward-operated reference instance plus reproducible self-hosting.
2. **Phase 1:** public federation allowlist, conformance tests, multiple independent nodes.
3. **Phase 2:** neutral entity owns marks/spec; steward node becomes one peer.

The canonical object must be **SABP**, not a hosted service. The public instance should be useful, but no user or agent should need it to prove identity, export history, or federate.

---

## 3. License Choice

### AGPL

AGPL-3.0 is the right default for the **networked reference server** because SAB's main capture risk is hosted-service capture. The FSF describes AGPL as designed for network server software so users interacting over a network can receive the modified source. It is also OSI-approved.

AGPL reduces the "lab runs a private modified hosted fork" problem. It does **not** stop:

- operating the unmodified server as a dominant service;
- capturing users through the default directory, brand, mobile app, or hosted convenience;
- acquiring maintainers or hiring away the team;
- building a clean-room closed competitor that speaks enough of the protocol to drain adoption.

### MIT

MIT is good for SDKs, examples, and integration glue. It is a poor default for the hosted server if the goal is capture resistance. The OpenClaw research artifact identifies OpenClaw as MIT-licensed; AP reports OpenAI hired the OpenClaw creator, and the research treats that as a standards-layer capture warning. MIT helped adoption, but it did not protect governance, brand, or direction.

### Dual license

Dual licensing can work for a company, but it is risky for SAB's purpose. If a single copyright holder can sell proprietary exceptions, then the copyright holder becomes an acquisition target. Dual licensing only fits if:

- copyright is held by a neutral entity;
- proprietary exceptions require board + member approval;
- no single founder can unilaterally relicense;
- contributors use DCO or a non-exclusive CLA, not assignment to a private company.

Default: **do not dual-license the server at launch**.

### Custom license

Avoid a custom "anti-capture" license for core code. It will likely fail OSI open-source criteria if it discriminates against specific actors or fields of endeavor, and it will slow adoption. Put anti-capture controls in governance, trademarks, conformance marks, and federation policy instead.

---

## 4. Capture Cases

| Case | What happened | Lesson for SAB |
|---|---|---|
| OpenClaw -> OpenAI | Research artifacts identify OpenClaw as MIT-licensed and local-first; AP reports OpenAI hired Peter Steinberger to work on personal agents. | Permissive code plus founder centrality lets a lab capture direction without buying copyright. SAB needs shared governance, not only open code. |
| Manus -> Meta | TechCrunch reported Meta acquiring Manus in Dec 2025; Axios later reported Chinese regulators ordered Meta to unwind the deal. | Agent capability startups are acquisition targets, and cross-border entity structure can become a geopolitical constraint. SAB should keep protocol governance outside a venture-backed operating company. |
| Moltbook -> Meta | Lane 4 and AP report Meta acquiring Moltbook and hiring its co-founders; the research frames Meta's interest as agent identity/directory, not just social feed. | The default directory is the asset. Federation registry, marks, and identity namespace must not be controlled by one lab. |

**Implication:** the capture-resistant bundle is:

1. AGPL server.
2. Permissive wire protocol and SDKs.
3. Neutral mark/spec holder.
4. Multi-stakeholder board with no single-lab control.
5. Trademark policy that permits compatible implementations but reserves "official", "certified", and default registry rights.
6. Mandatory export/fork rights in the protocol.

---

## 5. Entity Structure Options

This section is a design screen, not legal advice. The principal operates from Japan/Iriomote and Bali, so tax residency, visa status, foreign-control rules, employment, fundraising, and permanent-establishment risk need counsel before filing.

| Structure | Jurisdiction | Fit | Risk |
|---|---|---|---|
| General incorporated association | Japan | Practical for a Japan-based principal; Japanese law recognizes general incorporated associations/foundations as corporations. Good for member governance and spec/mark custody. | Nonprofit/tax treatment is not automatic; English-language operations and international contributors need setup. |
| Specified nonprofit corporation | Japan | Public-interest signaling; Cabinet Office NPO portal shows active NPO corporation regime. | More administrative fit-checks; may be too narrow for protocol governance and international software stewardship. |
| Yayasan | Indonesia | Natural for Bali-facing local operations; Indonesian law has a foundation statute, amended in 2004. | Foreign-founder/control and activity-scope issues require Indonesian counsel; not ideal as sole global protocol holder. |
| Company limited by guarantee | Singapore | Strong English-language legal environment; common non-share-capital form for nonprofits; members' liability limited to guarantee amount. Good neutral Asia-Pacific base. | Requires local compliance/directors; may feel less grounded in the principal's Japan/Bali life. |
| Swiss association/foundation | Switzerland | Credible international standards-holder pattern. | More remote operationally; banking, board, audit, and counsel overhead. |
| Wyoming DAO LLC | United States | Explicit DAO filing path exists through Wyoming Secretary of State. | Poor fit for initial SAB governance: US regulatory exposure, token/DAO optics, and smart-contract formalism before SAB needs it. |

**Recommended path:** do not start with a DAO. For Phase 1, choose either:

- **Japan general incorporated association** if the operating center will genuinely be Japan/Iriomote; or
- **Singapore CLG** if the priority is an English-language international standards body with Asia-Pacific neutrality.

Use an Indonesian Yayasan only for Bali-local education/events/grants, not as the global protocol owner, unless counsel confirms foreign-control and software-governance fit.

Phase 2 entity charter should require:

- board seats split across operators, implementers, security reviewers, and independent public-interest members;
- no employer/lab may control more than one seat or 20-25% of votes;
- supermajority for license changes, trademark assignment, domain transfer, or federation-root changes;
- public minutes for governance decisions;
- non-revocable right to fork the protocol and export data;
- conflict policy for directors employed by foundation labs.

---

## 6. Trademark and Naming

The OpenClaw naming chain is a cautionary case, but not yet a verified legal-pressure case in the research inputs. Lane 2 verifies the naming sequence **Clawdbot -> Moltbot -> OpenClaw** and says CVE records preserve the aliases. It does **not** verify that the renames were forced by trademark/legal pressure. Do not cite that motive unless a primary source is later found.

Practical naming rules for SAB:

- Clear "SAB" and "SABP" before public launch in Japan, Indonesia, Singapore, US, EU, and WIPO Global Brand Database.
- Avoid claw/molt/agent-religion naming collisions entirely.
- Register the word mark for software, hosted protocol services, developer tools, certification, and community/education if counsel agrees.
- Hold marks in the neutral entity, not by the principal personally and not by an operating company.
- Publish a trademark policy: nominative use allowed; "SAB-compatible" allowed after conformance; "SAB-certified" and official logos require passing tests and governance approval.
- Keep the protocol name separate from implementation names. Example: "SABP" is the protocol; "SAB Reference Server" is one implementation; local operators name their node independently.

The trademark policy is more important than the logo. If a lab can own the default directory or call its closed fork "official SAB", the AGPL license will not matter much.

---

## 7. Open Questions

1. **Entity jurisdiction:** Japan association or Singapore CLG for Phase 1? This should be a counsel-backed decision, not a vibe choice.
2. **Contributor intake:** DCO-only, non-exclusive CLA, or foundation-held copyright? Recommendation: DCO or non-exclusive CLA; avoid private copyright assignment.
3. **Spec license:** MIT/Apache-style for schemas and SDKs is straightforward; the prose spec may need CC-BY-4.0 or similar. Counsel should confirm.
4. **Canonical instance:** who operates the first public node, and when does it lose any special status?
5. **Trademark budget:** which first filing jurisdiction becomes the Madrid base application?

---

## Sources

- Moltbook research synthesis: `/Users/dhyana/dharma_swarm_moltbook_research_wt/docs/research/moltbook_2026-05/00_synthesis.md`
- OpenClaw architecture: `/Users/dhyana/dharma_swarm_moltbook_research_wt/docs/research/moltbook_2026-05/02_openclaw_architecture.md`
- Adjacent landscape / Meta acquisition: `/Users/dhyana/dharma_swarm_moltbook_research_wt/docs/research/moltbook_2026-05/04_landscape.md`
- Deflation and acquisition uncertainty: `/Users/dhyana/dharma_swarm_moltbook_research_wt/docs/research/moltbook_2026-05/05_deflation.md`
- Corrections log: `/Users/dhyana/dharma_swarm_moltbook_research_wt/docs/research/moltbook_2026-05/CORRECTIONS_LOG.md`
- FSF AGPL-3.0 text and rationale: https://www.gnu.org/licenses/agpl-3.0.html.en
- SPDX MIT license identifier: https://spdx.org/licenses/MIT
- OSI Open Source Definition: https://opensource.org/osd
- OSI approved-license list: https://opensource.org/licenses
- Japanese Act on General Incorporated Associations and General Incorporated Foundations: https://www.japaneselawtranslation.go.jp/en/laws/link/3588
- Japan Cabinet Office NPO portal: https://www.npo-homepage.go.jp/
- Indonesia Law No. 16 of 2001 on Yayasan and Law No. 28 of 2004 amendment: https://peraturan.bpk.go.id/Details/44893/uu-no-16-tahun-2001 and https://peraturan.bpk.go.id/Details/40703/uu-no-28-tahun-2004
- Singapore MCCY Charities Unit on companies limited by guarantee: https://ask.gov.sg/mccy-cu/questions/clpq9t4w2000y1xxmnhpkqha7
- Wyoming Secretary of State DAO LLC FAQ: https://sos.wyo.gov/Business/Docs/DAOs_FAQs.pdf
- USPTO likelihood-of-confusion guidance: https://www.uspto.gov/trademarks/search/likelihood-confusion
- WIPO Madrid System: https://www.wipo.int/madrid/
- TechCrunch Manus acquisition report: https://techcrunch.com/2025/12/29/meta-just-bought-manus-an-ai-startup-everyone-has-been-talking-about/
- Axios Manus unwind report: https://www.axios.com/2026/04/27/china-blocks-metas-acquisition-of-manus-ai
- AP Moltbook acquisition / OpenClaw hire report: https://apnews.com/article/meta-moltbook-ai-agents-openclaw-31af42ccbb04001dd17a3fc7067d1de3

---

*End Lane E. Block-on: legal counsel for jurisdiction, tax, trademark clearance, and contributor agreement design.*
