async function loadSeedClaims() {
  const container = document.getElementById("seed-claims");
  if (!container) return;

  try {
    const response = await fetch("./data/seed_claims.json");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    const claims = Array.isArray(payload.claims) ? payload.claims : [];
    if (!claims.length) {
      container.innerHTML = "<p>No seed claims available yet.</p>";
      return;
    }
    container.innerHTML = claims
      .map((claim) => {
        const witnessRefs = Array.isArray(claim.witness_refs) ? claim.witness_refs : [];
        const redTeamRefs = Array.isArray(claim.red_team_refs) ? claim.red_team_refs : [];
        const artifactRefs = Array.isArray(claim.artifact_refs) ? claim.artifact_refs : [];
        return `
          <article class="claim-card">
            <h3>${escapeHtml(claim.title || "")}</h3>
            <div class="claim-meta">
              <span class="pill">${escapeHtml(claim.node_coordinate || "unknown-node")}</span>
              <span class="pill">${escapeHtml(claim.requested_stage || "unscoped")}</span>
              <span class="pill">${escapeHtml(claim.status || "unknown")}</span>
            </div>
            <p><strong>${escapeHtml(claim.node || "unknown-node")}</strong></p>
            <p>${escapeHtml(claim.summary || "")}</p>
            <p>
              <a href="../${escapeAttr(claim.claim_path || "")}">Claim packet</a>
              ${renderRefLinks("Witnesses", witnessRefs)}
              ${renderRefLinks("Red team", redTeamRefs)}
              ${renderRefLinks("Artifacts", artifactRefs)}
            </p>
          </article>
        `;
      })
      .join("");
  } catch (error) {
    container.innerHTML = `<p>Unable to load seed claims: ${escapeHtml(String(error))}</p>`;
  }
}

function renderRefLinks(label, refs) {
  if (!refs.length) return "";
  const links = refs
    .map((ref, index) => renderRefLink(ref, index))
    .join(" ");
  return `<span class="ref-group">${escapeHtml(label)}: ${links}</span>`;
}

function renderRefLink(ref, index) {
  const label = escapeHtml(String(index + 1));
  if (!isRepoRelativePath(ref)) {
    return `<span title="${escapeAttr(ref)}">${label}</span>`;
  }
  return `<a href="../${escapeAttr(ref)}">${label}</a>`;
}

function isRepoRelativePath(ref) {
  const value = String(ref || "");
  return value && !value.startsWith("/") && !value.includes("..") && !/^[a-z]+:/i.test(value);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#96;");
}

void loadSeedClaims();
