/* ── SAB Web Shell — Progressive Enhancement ── */

/* Dark mode */
document.addEventListener('alpine:init', () => {
  Alpine.store('theme', {
    dark: localStorage.getItem('sab-dark') === 'true' ||
          (!localStorage.getItem('sab-dark') && window.matchMedia('(prefers-color-scheme: dark)').matches),

    toggle() {
      this.dark = !this.dark;
      localStorage.setItem('sab-dark', this.dark);
      document.documentElement.classList.toggle('dark', this.dark);
    },

    init() {
      document.documentElement.classList.toggle('dark', this.dark);
    }
  });
});

/* Radar chart initialization */
function initRadarChart(canvasId, dimensions, options) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === 'undefined') return;

  const labels = dimensions.map(d => d.label);
  const scores = dimensions.map(d => d.score !== null && d.score !== undefined ? d.score : 0);
  const colors = dimensions.map(d => {
    if (d.score === null || d.score === undefined) return 'rgba(143, 139, 129, 0.6)';
    if (d.score >= 0.75) return 'rgba(47, 125, 50, 0.6)';
    if (d.score >= 0.45) return 'rgba(178, 136, 0, 0.6)';
    return 'rgba(176, 40, 40, 0.6)';
  });

  const isDark = document.documentElement.classList.contains('dark');
  const gridColor = isDark ? 'rgba(200, 197, 188, 0.15)' : 'rgba(30, 29, 26, 0.08)';
  const tickColor = isDark ? '#c8c5bc' : '#6f6a5f';

  new Chart(canvas, {
    type: 'radar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Gate Profile',
        data: scores,
        backgroundColor: 'rgba(17, 78, 138, 0.12)',
        borderColor: 'rgba(17, 78, 138, 0.7)',
        borderWidth: 2,
        pointBackgroundColor: colors,
        pointBorderColor: colors,
        pointRadius: 4,
        pointHoverRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const dim = dimensions[ctx.dataIndex];
              const score = dim.score !== null ? dim.score.toFixed(3) : 'pending';
              return `${dim.label}: ${score}`;
            }
          }
        }
      },
      scales: {
        r: {
          min: 0,
          max: 1,
          ticks: {
            stepSize: 0.25,
            color: tickColor,
            font: { size: 9 },
            backdropColor: 'transparent',
          },
          grid: { color: gridColor },
          angleLines: { color: gridColor },
          pointLabels: {
            color: tickColor,
            font: {
              family: "'Space Grotesk', sans-serif",
              size: options?.labelSize || 10,
            }
          }
        }
      },
      ...(options?.extra || {})
    }
  });
}

/* Witness chain client-side verification */
async function verifyWitnessChain(entries) {
  if (!entries || entries.length === 0) return { verified: true, brokenAt: null };

  let prevHash = 'genesis';
  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];

    if (entry.prev_hash !== prevHash) {
      return { verified: false, brokenAt: i };
    }

    const material = {
      spark_id: entry.spark_id,
      witness_id: entry.witness_id,
      signature: entry.signature,
      action: entry.action,
      payload: entry.payload,
      timestamp: entry.timestamp,
      prev_hash: entry.prev_hash,
    };

    const canonical = JSON.stringify(material, Object.keys(material).sort(), '');
    const encoded = new TextEncoder().encode(canonical);
    const hashBuf = await crypto.subtle.digest('SHA-256', encoded);
    const hashArr = Array.from(new Uint8Array(hashBuf));
    const hashHex = hashArr.map(b => b.toString(16).padStart(2, '0')).join('');

    if (hashHex !== entry.hash) {
      return { verified: false, brokenAt: i };
    }
    prevHash = entry.hash;
  }
  return { verified: true, brokenAt: null };
}

function setChainStatus(root, className, text) {
  const status = root.querySelector('[data-chain-status]');
  if (!status) return;
  status.classList.remove('chain-verified', 'chain-broken', 'chain-pending');
  if (className) status.classList.add(className);
  status.textContent = text;
}

async function verifyChainFromEndpoint(root) {
  const endpoint = root?.dataset?.chainEndpoint;
  if (!endpoint) return;

  setChainStatus(root, 'chain-pending', 'checking');
  try {
    const response = await fetch(endpoint, {
      headers: { Accept: 'application/json' },
      credentials: 'same-origin',
    });
    if (!response.ok) {
      setChainStatus(root, 'chain-broken', `unavailable ${response.status}`);
      return;
    }
    const data = await response.json();
    const entries = Array.isArray(data.entries) ? data.entries : [];
    if (data.verified === true) {
      setChainStatus(root, 'chain-verified', `verified ${entries.length} entries`);
    } else {
      const brokenAt = data.broken_at ?? data.brokenAt ?? null;
      const suffix = brokenAt === null ? '' : ` at ${brokenAt}`;
      setChainStatus(root, 'chain-broken', `broken${suffix}`);
    }
  } catch (_err) {
    setChainStatus(root, 'chain-broken', 'unavailable');
  }
}

function initChainVerifiers(scope) {
  const rootScope = scope || document;
  rootScope.querySelectorAll('[data-chain-verifier]').forEach((root) => {
    if (root.dataset.chainVerifierReady === 'true') return;
    root.dataset.chainVerifierReady = 'true';
    const button = root.querySelector('[data-chain-trigger]');
    if (button) {
      button.addEventListener('click', () => verifyChainFromEndpoint(root));
    }
    verifyChainFromEndpoint(root);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initChainVerifiers(document);
});

/* HTMX event hooks */
document.addEventListener('htmx:afterSwap', (evt) => {
  /* Re-init any charts in swapped content */
  const canvases = evt.detail.target.querySelectorAll('[data-radar-init]');
  canvases.forEach(c => {
    const dims = JSON.parse(c.dataset.dimensions || '[]');
    initRadarChart(c.id, dims, { labelSize: 8 });
  });
  initChainVerifiers(evt.detail.target);
});
