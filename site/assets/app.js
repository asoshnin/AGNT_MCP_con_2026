let ALL_TALKS = [];
let ACTIVE_TOPIC = null;
let HIGH_RELEVANCE_ONLY = false;
let SLIDES_ONLY = false;
let CURRENT_VIEW_MODE = localStorage.getItem("agntcon_view_mode") || "grid";
let CURRENT_SORT = "relevance";
let CURRENT_INFERENCE_TIER = localStorage.getItem("agntcon_inference_tier") || "cloud";

function initTheme() {
  const themeSelect = document.getElementById('theme-select');
  let savedTheme = localStorage.getItem('agntcon_theme') || 'system';

  if (themeSelect) {
    themeSelect.value = savedTheme;
  }

  function applyTheme(themeValue) {
    let actualTheme = themeValue;
    if (themeValue === 'system') {
      actualTheme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }
    document.documentElement.setAttribute('data-theme', actualTheme);
  }

  // Initial application
  applyTheme(savedTheme);

  // Listen for changes from the select dropdown
  if (themeSelect) {
    themeSelect.addEventListener('change', (e) => {
      localStorage.setItem('agntcon_theme', e.target.value);
      applyTheme(e.target.value);
    });
  }

  // Listen for system theme changes if set to system
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
    if (localStorage.getItem('agntcon_theme') === 'system' || !localStorage.getItem('agntcon_theme')) {
      applyTheme('system');
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  // Prevent browser form history from auto-filling into search box
  const searchInput = document.getElementById("search-input");
  const searchClear = document.getElementById("search-clear");
  if (searchInput) searchInput.value = "";
  if (searchClear) searchClear.style.display = "none";

  await loadCatalog();
  setupEventListeners();
  setupChat();
  setupModalsAndSettings();
  handleInitialHash();
});

function handleInitialHash() {
  const hash = window.location.hash;
  const match = hash.match(/^#\/session\/([A-Za-z0-9_-]+)$/);
  if (match) {
    openEssenceModal(match[1]);
  }
}

window.addEventListener("hashchange", () => {
  const hash = window.location.hash;
  const match = hash.match(/^#\/session\/([A-Za-z0-9_-]+)$/);
  if (match) {
    openEssenceModal(match[1]);
  } else if (!hash || hash === "#/" || hash === "#") {
    const modalBackdrop = document.getElementById("modal-backdrop");
    if (modalBackdrop && modalBackdrop.classList.contains("open")) {
      modalBackdrop.classList.remove("open");
    }
  }
});

async function loadCatalog() {
  try {
    const res = await fetch("/api/search?q=");
    if (res.ok) {
      ALL_TALKS = await res.json();
    } else {
      // Fallback if accessed as pure static file
      const localRes = await fetch("../data/catalog.json");
      if (localRes.ok) ALL_TALKS = await localRes.json();
    }
  } catch (e) {
    console.log("Could not load /api/search, attempting local JSON...", e);
  }
  renderConceptPills();
  applyViewMode(CURRENT_VIEW_MODE);
  renderCards();
}

function renderConceptPills() {
  const container = document.getElementById("concept-pills");
  if (!container) return;

  // Pre-defined canonical taxonomy order
  const taxonomyOrder = [
    { key: "all", label: "All Sessions" },
    { key: "mcp", label: "Model Context Protocol" },
    { key: "security", label: "Security & Red-Teaming" },
    { key: "sandboxing", label: "Sandboxing & eBPF" },
    { key: "evaluation", label: "Agent Evaluation" },
    { key: "orchestration", label: "Multi-Agent Topology" },
    { key: "memory", label: "Memory & RAG" },
    { key: "tool-use", label: "Tool-Use & Execution" },
    { key: "observability", label: "Observability" },
  ];

  // Count occurrences
  const counts = { all: ALL_TALKS.length };
  ALL_TALKS.forEach((t) => {
    (t.concepts || []).forEach((c) => {
      const lc = c.toLowerCase();
      counts[lc] = (counts[lc] || 0) + 1;
    });
  });

  container.innerHTML = taxonomyOrder
    .map((item) => {
      const count = counts[item.key] || 0;
      if (item.key !== "all" && count === 0) return "";
      const isActive = (item.key === "all" && !ACTIVE_TOPIC) || ACTIVE_TOPIC === item.key;
      return `<button class="pill ${isActive ? "active" : ""}" data-topic="${item.key}">${item.label} (${count})</button>`;
    })
    .join("");

  container.querySelectorAll(".pill").forEach((p) => {
    p.addEventListener("click", () => {
      container.querySelectorAll(".pill").forEach((x) => x.classList.remove("active"));
      p.classList.add("active");
      const topic = p.getAttribute("data-topic");
      ACTIVE_TOPIC = topic === "all" ? null : topic;
      renderCards();
    });
  });
}

window.filterByConcept = function(concept) {
  if (!concept) return;
  const target = concept.toLowerCase().trim();
  const container = document.getElementById("concept-pills");
  if (!container) return;
  const pill = container.querySelector(`[data-topic="${target}"]`);
  if (pill) {
    pill.click();
    window.scrollTo({ top: 0, behavior: "smooth" });
  } else {
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
      searchInput.value = target;
      searchInput.dispatchEvent(new Event("input"));
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }
};

window.copyCitation = function(sid, btn) {
  const t = ALL_TALKS.find((x) => x.id === sid);
  if (!t) return;
  const speaker = (t.speakers && t.speakers.length > 0) ? t.speakers[0] : "Speaker";
  const cleanTitle = (t.title || "").replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
  const citation = `${speaker} (2026). "${cleanTitle}". AGNTCon + MCPCon Europe 2026. ${t.sched_url}`;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(citation).then(() => {
      if (btn) {
        const orig = btn.innerHTML;
        btn.innerHTML = "✓ Copied!";
        btn.style.borderColor = "#22c55e";
        btn.style.color = "#22c55e";
        setTimeout(() => {
          btn.innerHTML = orig;
          btn.style.borderColor = "";
          btn.style.color = "";
        }, 2000);
      }
    });
  }
};

function applyViewMode(mode) {
  CURRENT_VIEW_MODE = mode;
  localStorage.setItem("agntcon_view_mode", mode);
  const gridBtn = document.getElementById("view-grid-btn");
  const tableBtn = document.getElementById("view-table-btn");
  const gridEl = document.getElementById("sessions-grid");
  const tableWrapper = document.getElementById("sessions-table-wrapper");

  if (mode === "table") {
    if (tableBtn) tableBtn.classList.add("active");
    if (gridBtn) gridBtn.classList.remove("active");
    if (tableWrapper) tableWrapper.style.display = "block";
    if (gridEl) gridEl.style.display = "none";
  } else {
    if (gridBtn) gridBtn.classList.add("active");
    if (tableBtn) tableBtn.classList.remove("active");
    if (gridEl) gridEl.style.display = "grid";
    if (tableWrapper) tableWrapper.style.display = "none";
  }
}

function setupEventListeners() {
  const searchInput = document.getElementById("search-input");
  const searchClear = document.getElementById("search-clear");
  const sortSelect = document.getElementById("sort-select");
  const viewGridBtn = document.getElementById("view-grid-btn");
  const viewTableBtn = document.getElementById("view-table-btn");

  if (searchInput) {
    searchInput.value = "";
    if (searchClear) searchClear.style.display = "none";
    searchInput.addEventListener("input", (e) => {
      if (searchClear) searchClear.style.display = e.target.value.trim() ? "block" : "none";
      renderCards();
    });
  }

  if (searchClear && searchInput) {
    searchClear.addEventListener("click", () => {
      searchInput.value = "";
      searchClear.style.display = "none";
      searchInput.focus();
      renderCards();
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", (e) => {
      CURRENT_SORT = e.target.value;
      renderCards();
    });
  }

  if (viewGridBtn) {
    viewGridBtn.addEventListener("click", () => {
      applyViewMode("grid");
      renderCards();
    });
  }

  if (viewTableBtn) {
    viewTableBtn.addEventListener("click", () => {
      applyViewMode("table");
      renderCards();
    });
  }

  const relevanceToggle = document.getElementById("relevance-toggle");
  if (relevanceToggle) {
    relevanceToggle.addEventListener("change", (e) => {
      HIGH_RELEVANCE_ONLY = e.target.checked;
      renderCards();
    });
  }

  const slidesOnlyToggle = document.getElementById("slides-only-toggle");
  if (slidesOnlyToggle) {
    slidesOnlyToggle.addEventListener("change", (e) => {
      SLIDES_ONLY = e.target.checked;
      renderCards();
    });
  }

  // Modal close
  const modalClose = document.getElementById("modal-close");
  const modalBackdrop = document.getElementById("modal-backdrop");
  if (modalClose) modalClose.addEventListener("click", closeModal);
  if (modalBackdrop) {
    modalBackdrop.addEventListener("click", (e) => {
      if (e.target === modalBackdrop) closeModal();
    });
  }
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
}

function calculateMatchScore(talk, query) {
  if (!query) return null;
  const q = query.trim().toLowerCase();
  if (!q) return null;

  const tokens = q.split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return null;

  const cleanTitle = (talk.title || "")
    .replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "")
    .toLowerCase();
  const speakers = (talk.speakers || []).join(" ").toLowerCase();
  const concepts = (talk.concepts || []).join(" ").toLowerCase();
  const essence = (talk.one_paragraph || "").toLowerCase();
  const id = (talk.id || "").toLowerCase();

  let rawScore = 0;

  // Exact phrase match bonuses
  if (id === q) rawScore += 60;
  if (cleanTitle.includes(q)) rawScore += 45;
  else if (speakers.includes(q)) rawScore += 35;
  else if (concepts.includes(q)) rawScore += 25;
  else if (essence.includes(q)) rawScore += 15;

  // Per-token matches
  for (const tok of tokens) {
    if (id === tok) rawScore += 30;
    if (cleanTitle.includes(tok)) rawScore += 25;
    if (speakers.includes(tok)) rawScore += 20;
    if (concepts.includes(tok)) rawScore += 15;
    if (essence.includes(tok)) rawScore += 10;
  }

  // Intrinsic topic depth bonus (up to 12 points) to break ties cleanly
  const depthBonus = (talk.relevance_score || 0.5) * 12;
  const composite = Math.min(99, Math.max(25, Math.round(rawScore * 0.85 + depthBonus)));
  return composite;
}

function renderCards() {
  const grid = document.getElementById("sessions-grid");
  const tableBody = document.getElementById("sessions-table-body");
  const searchInput = document.getElementById("search-input");
  const q = searchInput ? searchInput.value.trim().toLowerCase() : "";

  // Dynamic table header
  const thRelevance = document.getElementById("th-relevance-col");
  if (thRelevance) {
    thRelevance.textContent = q ? "Query Match" : "Topic Depth";
  }

  let filtered = ALL_TALKS.filter((t) => {
    if (HIGH_RELEVANCE_ONLY && (t.relevance_score || 0) < 0.7) return false;
    if (SLIDES_ONLY && !(t.has_slides || t.file_name)) return false;
    if (ACTIVE_TOPIC && !(t.concepts || []).map((c) => c.toLowerCase()).includes(ACTIVE_TOPIC)) return false;
    if (!q) {
      t._matchScore = null;
      return true;
    }

    const blob = `${t.id || ""} ${t.title || ""} ${(t.speakers || []).join(" ")} ${(t.concepts || []).join(" ")} ${t.one_paragraph || ""}`.toLowerCase();
    const matches = blob.includes(q);
    if (matches) {
      t._matchScore = calculateMatchScore(t, q);
    } else {
      t._matchScore = null;
    }
    return matches;
  });

  // Sorting
  filtered.sort((a, b) => {
    if (CURRENT_SORT === "title") {
      const ta = (a.title || "").replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
      const tb = (b.title || "").replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
      return ta.localeCompare(tb);
    } else if (CURRENT_SORT === "speaker") {
      const sa = (a.speakers || [])[0] || "";
      const sb = (b.speakers || [])[0] || "";
      return sa.localeCompare(sb);
    } else if (CURRENT_SORT === "id") {
      return (a.id || "").localeCompare(b.id || "");
    } else {
      // Relevance sort: dynamic match if query active, otherwise intrinsic topic depth
      if (q) {
        return (b._matchScore || 0) - (a._matchScore || 0);
      } else {
        return (b.relevance_score || 0) - (a.relevance_score || 0);
      }
    }
  });

  const countEl = document.getElementById("results-count");
  if (countEl) {
    countEl.textContent = `Showing ${filtered.length} of ${ALL_TALKS.length} presentations`;
  }

  if (filtered.length === 0) {
    const emptyMsg = `<div style="text-align: center; padding: 40px; color: var(--text-secondary);">No presentations match your active filters.</div>`;
    if (grid) grid.innerHTML = `<div style="grid-column: 1/-1;">${emptyMsg}</div>`;
    if (tableBody) tableBody.innerHTML = `<tr><td colspan="6">${emptyMsg}</td></tr>`;
    return;
  }

  // Render Grid
  if (grid) {
    grid.innerHTML = filtered
      .map((t) => {
        const cleanTitle = t.title.replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
        const isKeynote = (t.kind && t.kind.toLowerCase().includes("keynote")) || cleanTitle.toLowerCase().includes("keynote");
        const hasSlides = !!(t.has_slides || t.file_name);
        const hasRepo = !!(t.repos && t.repos.length > 0);
        let badgesHtml = "";
        if (isKeynote) badgesHtml += '<span class="badge badge-keynote">🎙️ Keynote</span>';
        if (hasSlides) badgesHtml += '<span class="badge badge-slides">📄 Slides Available</span>';
        if (hasRepo) badgesHtml += '<span class="badge badge-repo">💻 GitHub Repo</span>';

        const scoreBadge = q && t._matchScore != null
          ? `<span class="relevance-score match-active" title="Dynamic search query match score based on title, speaker, tags, and summary">🎯 Match: ${t._matchScore}%</span>`
          : `<span class="relevance-score" title="Intrinsic conference topic depth (Agent Harnesses, MCP, Security, Tool-Use)">⭐ Topic Depth: ${Math.round((t.relevance_score || 0) * 100)}%</span>`;

        let directSlideBtn = "";
        if (hasSlides) {
          const slideHref = t.slide_url || t.sched_url;
          directSlideBtn = `<a class="btn-view-essence" href="${escapeHtml(slideHref)}" target="_blank" rel="noopener" style="text-decoration: none;" title="View official presentation slides">📄 Slides ↗</a>`;
        }

        return `
    <div class="session-card">
      <div class="card-header">
        <div class="card-meta">
          <span class="card-id">[[${t.id}]]</span>
          ${scoreBadge}
        </div>
        <h3 class="card-title session-title">${escapeHtml(cleanTitle)}</h3>
        ${badgesHtml ? `<div class="card-badges">${badgesHtml}</div>` : ""}
        <p class="card-speakers">${escapeHtml((t.speakers || []).join(", ") || "Speaker")}</p>
        <p class="card-essence">${escapeHtml(t.one_paragraph || "View full essence for architectural takeaways.")}</p>
      </div>
      <div>
        <div class="card-tags">
          ${(t.concepts || []).map((c) => `<span class="card-tag" onclick="filterByConcept('${escapeHtml(c)}')">${escapeHtml(c)}</span>`).join("")}
        </div>
        <div class="card-actions">
          <a class="btn-sched" href="${escapeHtml(t.sched_url)}" target="_blank" rel="noopener">Official Sched ↗</a>
          ${directSlideBtn}
          <button class="btn-view-essence" onclick="openEssenceModal('${t.id}')">View Essence</button>
          <button class="btn-cite" onclick="copyCitation('${t.id}', this)" title="Copy academic/blog citation to clipboard">📋 Citation</button>
        </div>
      </div>
    </div>
  `;
      })
      .join("");
  }

  // Render Table
  if (tableBody) {
    tableBody.innerHTML = filtered
      .map((t) => {
        const cleanTitle = t.title.replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
        const isKeynote = (t.kind && t.kind.toLowerCase().includes("keynote")) || cleanTitle.toLowerCase().includes("keynote");
        const hasSlides = !!(t.has_slides || t.file_name);
        const hasRepo = !!(t.repos && t.repos.length > 0);
        let badgesHtml = "";
        if (isKeynote) badgesHtml += '<span class="badge badge-keynote" style="margin-left: 6px;">🎙️ Keynote</span>';
        if (hasSlides) badgesHtml += '<span class="badge badge-slides" style="margin-left: 6px;">📄 Slides</span>';
        if (hasRepo) badgesHtml += '<span class="badge badge-repo" style="margin-left: 6px;">💻 Repo</span>';

        const tableScoreCell = q && t._matchScore != null
          ? `<td style="text-align: center; font-weight: 700; color: var(--accent);" title="Dynamic query match">🎯 ${t._matchScore}%</td>`
          : `<td style="text-align: center; font-weight: 600; color: var(--text-secondary);" title="Intrinsic conference topic depth">⭐ ${Math.round((t.relevance_score || 0) * 100)}%</td>`;

        return `
    <tr>
      <td><a href="#/session/${t.id}" class="card-id" style="text-decoration: none;" onclick="openEssenceModal('${t.id}')">[[${t.id}]]</a></td>
      <td>
        <strong>${escapeHtml(cleanTitle)}</strong>
        ${badgesHtml}
      </td>
      <td style="color: var(--text-secondary);">${escapeHtml((t.speakers || []).join(", ") || "—")}</td>
      ${tableScoreCell}
      <td>
        <div style="display: flex; flex-wrap: wrap; gap: 4px;">
          ${(t.concepts || []).map((c) => `<span class="card-tag" onclick="filterByConcept('${escapeHtml(c)}')">${escapeHtml(c)}</span>`).join("")}
        </div>
      </td>
      <td style="text-align: right;">
        <div style="display: inline-flex; gap: 6px;">
          <a class="btn-sched" href="${escapeHtml(t.sched_url)}" target="_blank" rel="noopener" style="padding: 4px 8px; font-size: 0.78rem;">Sched ↗</a>
          <button class="btn-view-essence" onclick="openEssenceModal('${t.id}')" style="padding: 4px 8px; font-size: 0.78rem;">View</button>
          <button class="btn-cite" onclick="copyCitation('${t.id}', this)" style="padding: 4px 8px; font-size: 0.78rem;" title="Copy academic citation to clipboard">📋 Citation</button>
        </div>
      </td>
    </tr>
  `;
      })
      .join("");
  }
}

async function openEssenceModal(sid) {
  const modalBackdrop = document.getElementById("modal-backdrop");
  const modalBody = document.getElementById("modal-body");
  
  if (location.hash !== `#/session/${sid}`) {
    history.pushState(null, "", `#/session/${sid}`);
  }
  
  modalBody.innerHTML = `
    <div class="modal-header-bar">
      <span class="modal-title">Presentation Essence: [[${escapeHtml(sid)}]]</span>
    </div>
    <div style="padding: 20px 0; color: var(--text-secondary);">Loading distilled Karpathy essence...</div>
  `;
  modalBackdrop.classList.add("open");

  try {
    const res = await fetch(`/api/page?type=source&name=${sid}`);
    if (res.ok) {
      const data = await res.json();
      let rawContent = data.content || "No essence content found.";
      
      // Transform [[wikilinks]]:
      // - If session ID (e.g. 2RBBJ), render interactive session pill
      // - If keyword/concept (e.g. sandboxing), render clean tag without brackets
      let processed = rawContent.replace(/\[\[([A-Za-z0-9_-]+)\]\]/g, (match, p1) => {
        const isSession = ALL_TALKS.some((t) => t.id.toLowerCase() === p1.toLowerCase());
        if (isSession) {
          return `<a href="#/session/${p1}" class="wikilink-pill" data-session-id="${p1}">[[${p1}]]</a>`;
        } else {
          return `<span class="card-tag" style="display: inline-block; margin: 2px 4px; font-size: 0.78rem;" onclick="closeModal(); filterByConcept('${escapeHtml(p1)}')">${escapeHtml(p1)}</span>`;
        }
      });

      let htmlOutput = "";
      if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
        htmlOutput = DOMPurify.sanitize(marked.parse(processed));
      } else {
        htmlOutput = `<div style="white-space: pre-wrap;">${escapeHtml(processed)}</div>`;
      }

      modalBody.innerHTML = `
        <div class="modal-header-bar">
          <span class="modal-title">Presentation Essence: <span style="color: var(--accent);">[[${escapeHtml(sid)}]]</span></span>
        </div>
        <div class="markdown-content">${htmlOutput}</div>
      `;

      // Enhance code blocks with copy snippet buttons
      modalBody.querySelectorAll("pre").forEach((pre) => {
        const wrapper = document.createElement("div");
        wrapper.className = "code-container";
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);

        const copyBtn = document.createElement("button");
        copyBtn.className = "btn-copy-snippet";
        copyBtn.textContent = "📋 Copy";
        copyBtn.addEventListener("click", () => {
          const codeText = pre.querySelector("code") ? pre.querySelector("code").innerText : pre.innerText;
          navigator.clipboard.writeText(codeText).then(() => {
            copyBtn.textContent = "✓ Copied!";
            setTimeout(() => (copyBtn.textContent = "📋 Copy"), 2000);
          });
        });
        wrapper.appendChild(copyBtn);
      });

      // Bind wikilinks click
      modalBody.querySelectorAll(".wikilink-pill").forEach((pill) => {
        pill.addEventListener("click", (e) => {
          e.preventDefault();
          const targetSid = pill.getAttribute("data-session-id");
          if (targetSid) openEssenceModal(targetSid);
        });
      });

    } else {
      modalBody.innerHTML = `
        <div class="modal-header-bar">
          <span class="modal-title">Session: [[${escapeHtml(sid)}]]</span>
        </div>
        <p style="padding: 20px 0; color: var(--text-secondary);">Source essence for <strong>${escapeHtml(sid)}</strong> is currently in ingestion pipeline.</p>
      `;
    }
  } catch (e) {
    modalBody.innerHTML = `
      <div class="modal-header-bar">
        <span class="modal-title">Error</span>
      </div>
      <p style="padding: 20px 0; color: #f87171;">Error loading essence for ${escapeHtml(sid)}: ${escapeHtml(e.message)}</p>
    `;
  }
}

function closeModal() {
  const modalBackdrop = document.getElementById("modal-backdrop");
  if (modalBackdrop) {
    modalBackdrop.classList.remove("open");
    if (location.hash && location.hash.startsWith("#/session/")) {
      history.pushState(null, "", window.location.pathname + window.location.search);
    }
  }
}

function updateChatEngineBadge() {
  const badge = document.getElementById("chat-engine-badge");
  if (!badge) return;
  const tier = localStorage.getItem("agntcon_inference_tier") || "cloud";

  if (tier === "cloud") {
    badge.textContent = "☁️ Cloud Demo (Free)";
    badge.style.background = "rgba(56, 189, 248, 0.15)";
    badge.style.color = "var(--accent)";
  } else {
    const providerSelect = document.getElementById("model-provider-select");
    const p = providerSelect ? providerSelect.value : "custom";
    if (p === "lmstudio") {
      badge.textContent = "💻 LM Studio (Local)";
    } else if (p === "ollama") {
      badge.textContent = "💻 Ollama (Local)";
    } else if (p === "nvidia") {
      badge.textContent = "🔑 NVIDIA NIM (BYOM)";
    } else if (p === "kilocode") {
      badge.textContent = "🔑 Kilocode (BYOM)";
    } else if (p === "openrouter") {
      badge.textContent = "🔑 OpenRouter (BYOM)";
    } else {
      badge.textContent = "🔑 Custom (BYOM)";
    }
    badge.style.background = "rgba(34, 197, 94, 0.15)";
    badge.style.color = "#22c55e";
  }
}

function setupChat() {
  const toggleBtn = document.getElementById("chat-toggle");
  const chatPanel = document.getElementById("chat-panel");
  const chatClose = document.getElementById("chat-close");
  const chatReset = document.getElementById("chat-reset");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatMessages = document.getElementById("chat-messages");

  updateChatEngineBadge();

  if (chatReset) {
    chatReset.addEventListener("click", () => {
      chatMessages.innerHTML = `
        <div class="chat-msg bot">
          Hello! I am your research assistant for <strong>AGNTCon + MCPCon Europe 2026</strong>.<br><br>
          Ask me about any presentation, architecture pattern, security boundary, or tool mentioned at the conference. Every answer links directly to the canonical presentation on Sched.
        </div>
      `;
    });
  }

  toggleBtn.addEventListener("click", () => chatPanel.classList.toggle("open"));
  chatClose.addEventListener("click", () => chatPanel.classList.remove("open"));

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const q = chatInput.value.trim();
    if (!q) return;

    appendMsg(q, "user");
    chatInput.value = "";

    const loadingId = appendMsg("Consulting AGNTCon + MCPCon knowledge base...", "bot");
    const onlySlides = document.getElementById("chat-slides-only") ? document.getElementById("chat-slides-only").checked : false;
    const breadthSelect = document.getElementById("rag-breadth-select");
    const breadth = breadthSelect ? breadthSelect.value : "auto";
    const tier = localStorage.getItem("agntcon_inference_tier") || "cloud";

    // 1. BYOM: Direct Browser-Side Execution (Local or Custom Cloud)
    if (tier === "byom") {
      const baseUrlInput = document.getElementById("model-base-url");
      const modelNameInput = document.getElementById("model-name-input");
      const apiKeyInput = document.getElementById("model-api-key");
      const baseUrl = (baseUrlInput ? baseUrlInput.value.trim() : "http://127.0.0.1:1234/v1").replace(/\/+$/, "");
      const modelName = modelNameInput ? modelNameInput.value.trim() : "huihui-qwythos-9b-claude-mythos-5-1m-abliterated";
      const apiKey = apiKeyInput ? apiKeyInput.value.trim() : "";

      try {
        // Fetch RAG context from local search endpoint
        const searchRes = await fetch(`/api/search?q=${encodeURIComponent(q)}&only_with_slides=${onlySlides ? "1" : "0"}`);
        const searchData = await searchRes.json();
        const topMatches = (Array.isArray(searchData) ? searchData : (searchData.results || [])).slice(0, 6);

        let contextSnippets = [];
        let citations = [];
        topMatches.forEach((m) => {
          citations.push({ id: m.id, title: m.title, sched_url: m.sched_url });
          contextSnippets.push(`### [[${m.id}]]: ${m.title}\nSpeaker(s): ${(m.speakers || []).join(", ")}\nSummary: ${m.one_paragraph}`);
        });

        const systemPrompt = `You are the research assistant for AGNTCon + MCPCon Europe 2026.
Answer clearly and concisely based strictly on the provided conference excerpts.
Always cite the session ID (e.g. [[2RBBJ]]) and speaker by name for every claim.`;

        const userMsg = `Question: ${q}\n\n<conference_excerpts>\n${contextSnippets.join("\n\n---\n\n")}\n</conference_excerpts>`;

        const headers = { "Content-Type": "application/json" };
        if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;

        const llmRes = await fetch(`${baseUrl}/chat/completions`, {
          method: "POST",
          headers: headers,
          body: JSON.stringify({
            model: modelName,
            messages: [
              { role: "system", content: systemPrompt },
              { role: "user", content: userMsg }
            ],
            max_tokens: 1000,
            temperature: 0.2
          })
        });

        const botEl = document.getElementById(loadingId);
        if (llmRes.ok) {
          const llmData = await llmRes.json();
          const answerText = (llmData.choices && llmData.choices[0] && llmData.choices[0].message) ? llmData.choices[0].message.content : "No response content.";
          let html = `<div>${formatBotMarkdown(answerText)}</div>`;
          if (citations.length > 0) {
            html += `<div class="chat-citations" style="margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border); font-size: 0.82rem;">
              <strong style="color: var(--text-primary);">Referenced Presentations:</strong><br>
              ${citations.map((c) => `
                <div style="margin-top: 6px; line-height: 1.4;">
                  <strong>[[${escapeHtml(c.id)}]]</strong> ${escapeHtml(c.title)}<br>
                  <span style="font-size: 0.78rem;">
                    <a href="javascript:void(0)" onclick="openEssenceModal('${escapeHtml(c.id)}')" style="color: var(--accent); font-weight: 600; text-decoration: underline; margin-right: 8px;">📖 View Summary / Essence</a>
                    <a href="${escapeHtml(c.sched_url)}" target="_blank" rel="noopener" style="color: var(--text-secondary); text-decoration: underline;">Official Sched ↗</a>
                  </span>
                </div>
              `).join("")}
            </div>`;
          }
          botEl.innerHTML = html;
        } else {
          botEl.innerHTML = `<div style="color: #f87171;">Local LLM error (HTTP ${llmRes.status}). Verify model name '${escapeHtml(modelName)}' is loaded.</div>`;
        }
      } catch (err) {
        const botEl = document.getElementById(loadingId);
        if (window.location.protocol === "https:" && baseUrl.startsWith("http://")) {
          botEl.innerHTML = `
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 12px; color: var(--text-primary); font-size: 0.85rem; line-height: 1.5;">
              <strong style="color: #ef4444;">🛡️ HTTPS Mixed Content Blocked</strong><br><br>
              You are accessing this site via HTTPS, but trying to reach a local LLM via <code>http://</code>. Browsers block this by default.<br><br>
              <strong>Solutions:</strong><br>
              1. Switch to <strong>Cloud Demo</strong> (Free).<br>
              2. Use a browser extension to Allow Insecure Content for this origin.<br>
              3. Access this site via <code>http://</code> instead of <code>https://</code> if available.
              <div style="margin-top: 12px;">
                <button class="btn-header" onclick="localStorage.setItem('agntcon_inference_tier', 'cloud'); updateChatEngineBadge(); location.reload();" style="font-size: 0.78rem; padding: 4px 10px;">
                  ☁️ Switch to Cloud Demo
                </button>
              </div>
            </div>
          `;
        } else {
          botEl.innerHTML = `
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 12px; color: var(--text-primary); font-size: 0.85rem; line-height: 1.5;">
              <strong style="color: #ef4444;">✕ Inference Provider at ${escapeHtml(baseUrl)} is unreachable.</strong><br><br>
              Ensure your local LLM (LM Studio/Ollama) is running with CORS enabled, or your BYOM API key is valid.
              <div style="margin-top: 8px;">
                <button class="btn-header" onclick="localStorage.setItem('agntcon_inference_tier', 'cloud'); updateChatEngineBadge(); location.reload();" style="font-size: 0.78rem; padding: 4px 10px;">
                  ☁️ Switch to Cloud Demo
                </button>
              </div>
            </div>
          `;
        }
      }
      chatMessages.scrollTop = chatMessages.scrollHeight;
      return;
    }

    // 2. Cloud Demo: Server-Side Proxy Path (Default)
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonSafe({ question: q, only_with_slides: onlySlides, breadth: breadth }),
      });

      const data = await res.json();
      const botEl = document.getElementById(loadingId);

      if (res.ok) {
        let html = `<div>${formatBotMarkdown(data.answer)}</div>`;
        if (data.citations && data.citations.length > 0) {
          html += `<div class="chat-citations" style="margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border); font-size: 0.82rem;">
            <strong style="color: var(--text-primary);">Referenced Presentations:</strong><br>
            ${data.citations.map((c) => `
              <div style="margin-top: 6px; line-height: 1.4;">
                <strong>[[${escapeHtml(c.id)}]]</strong> ${escapeHtml(c.title)}<br>
                <span style="font-size: 0.78rem;">
                  <a href="javascript:void(0)" onclick="openEssenceModal('${escapeHtml(c.id)}')" style="color: var(--accent); font-weight: 600; text-decoration: underline; margin-right: 8px;">📖 View Summary / Essence</a>
                  <a href="${escapeHtml(c.sched_url)}" target="_blank" rel="noopener" style="color: var(--text-secondary); text-decoration: underline;">Official Sched ↗</a>
                </span>
              </div>
            `).join("")}
          </div>`;
        }
        botEl.innerHTML = html;
      } else if (res.status === 503 || (data && data.error === "cascade_unavailable")) {
        botEl.innerHTML = `
          <div style="background: rgba(234, 179, 8, 0.12); border: 1px solid rgba(234, 179, 8, 0.35); border-radius: 8px; padding: 12px; color: var(--text-primary); font-size: 0.85rem; line-height: 1.5;">
            <strong style="color: #eab308; display: block; margin-bottom: 4px;">⚠️ Public Free Cascade Currently at Capacity</strong>
            All public free-tier fallbacks (NVIDIA, Kilocode, OpenRouter) are currently busy or rate-limited.<br><br>
            <strong>To continue immediately:</strong><br>
            • Connect your own free API key or local Ollama: <button class="btn-header" onclick="document.getElementById('btn-open-settings').click()" style="padding: 2px 8px; font-size: 0.78rem; margin: 2px 0;">⚙️ Open Settings</button><br>
            • Or download the offline SQLite bundle to query directly via Cursor or Claude Desktop.
          </div>
        `;
      } else {
        botEl.innerHTML = `<div style="color: #f87171;">${escapeHtml(data.error || "Error retrieving response.")}</div>`;
      }
    } catch (err) {
      const botEl = document.getElementById(loadingId);
      botEl.innerHTML = `<div style="color: #f87171;">Connection error to /api/chat. Is serve.py running?</div>`;
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
}

function appendMsg(text, type) {
  const chatMessages = document.getElementById("chat-messages");
  const id = "msg_" + Math.random().toString(36).substring(2, 9);
  const div = document.createElement("div");
  div.id = id;
  div.className = `chat-msg ${type}`;
  div.textContent = text;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

function formatBotMarkdown(text) {
  if (!text) return "";
  let out = escapeHtml(text);
  // Format markdown links [title](url)
  out = out.replace(/\[(.*?)\]\((https?:\/\/.*?)\)/g, '<a href="$2" target="_blank" rel="noopener" style="color: var(--accent); font-weight: 500;">$1 ↗</a>');
  // Format wikilinks [[2RBBJ]] as clickable links to open essence modal!
  out = out.replace(/\[\[([A-Za-z0-9_-]+)\]\]/g, '<a href="javascript:void(0)" onclick="openEssenceModal(\'$1\')" style="color: var(--accent); font-weight: 700; text-decoration: underline; cursor: pointer;" title="Open presentation summary">[[$1]]</a>');
  // Format bold
  out = out.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  // Replace newlines
  out = out.replace(/\n/g, "<br>");
  return out;
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function jsonSafe(obj) {
  return JSON.stringify(obj);
}

function setupModalsAndSettings() {
  // Legal Modal
  const legalModal = document.getElementById("legal-modal-backdrop");
  const btnOpenLegal = document.getElementById("btn-open-legal");
  const linkOpenLegal = document.getElementById("link-open-legal");
  const legalClose = document.getElementById("legal-modal-close");
  const btnFeedbackFromLegal = document.getElementById("btn-open-feedback-from-legal");

  const openLegal = () => legalModal && legalModal.classList.add("open");
  const closeLegal = () => legalModal && legalModal.classList.remove("open");

  if (btnOpenLegal) btnOpenLegal.addEventListener("click", openLegal);
  if (linkOpenLegal) linkOpenLegal.addEventListener("click", (e) => { e.preventDefault(); openLegal(); });
  if (legalClose) legalClose.addEventListener("click", closeLegal);
  if (legalModal) legalModal.addEventListener("click", (e) => { if (e.target === legalModal) closeLegal(); });

  // Speaker Feedback Modal
  const feedbackModal = document.getElementById("feedback-modal-backdrop");
  const feedbackClose = document.getElementById("feedback-modal-close");
  const feedbackCancel = document.getElementById("feedback-cancel-btn");
  const feedbackForm = document.getElementById("author-feedback-form");
  const feedbackSessionSelect = document.getElementById("feedback-session-id");
  const feedbackStatus = document.getElementById("feedback-status");

  const openFeedback = (prefillSid) => {
    closeLegal();
    if (feedbackSessionSelect && ALL_TALKS.length > 0) {
      feedbackSessionSelect.innerHTML = '<option value="">-- Select Session --</option>' +
        ALL_TALKS.map(t => `<option value="${t.id}" ${prefillSid === t.id ? 'selected' : ''}>[[${t.id}]] ${(t.title || '').replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, '').substring(0, 60)}...</option>`).join('');
    }
    if (feedbackModal) feedbackModal.classList.add("open");
  };
  const closeFeedback = () => feedbackModal && feedbackModal.classList.remove("open");

  if (btnFeedbackFromLegal) btnFeedbackFromLegal.addEventListener("click", () => openFeedback());
  if (feedbackClose) feedbackClose.addEventListener("click", closeFeedback);
  if (feedbackCancel) feedbackCancel.addEventListener("click", closeFeedback);
  if (feedbackModal) feedbackModal.addEventListener("click", (e) => { if (e.target === feedbackModal) closeFeedback(); });

  if (feedbackForm) {
    feedbackForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const hp = document.getElementById("feedback-hp").value;
      const sessionId = document.getElementById("feedback-session-id").value;
      const name = document.getElementById("feedback-name").value.trim();
      const email = document.getElementById("feedback-email").value.trim();
      const profileUrl = document.getElementById("feedback-profile").value.trim();
      const requestType = document.getElementById("feedback-type").value;
      const notes = document.getElementById("feedback-notes").value.trim();

      feedbackStatus.style.display = "block";
      feedbackStatus.style.color = "var(--text-secondary)";
      feedbackStatus.textContent = "Transmitting verification request...";

      try {
        const res = await fetch("/api/author-feedback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            website_hp: hp,
            session_id: sessionId,
            name: name,
            email: email,
            profile_url: profileUrl,
            request_type: requestType,
            notes: notes
          })
        });
        const result = await res.json();
        if (res.ok && result.status === "ok") {
          const fullLink = `${window.location.origin}${result.ticket_url}`;
          feedbackModal.querySelector(".modal-box").innerHTML = `
            <button class="modal-close" onclick="document.getElementById('feedback-modal-backdrop').classList.remove('open'); location.reload();">&times;</button>
            <div style="text-align: center; padding: 24px 12px;">
              <div style="font-size: 2.5rem; margin-bottom: 8px;">📝</div>
              <h2 style="margin: 0 0 6px 0; font-size: 1.3rem;">Speaker Request Registered!</h2>
              <div style="display: inline-block; font-size: 0.95rem; font-weight: 700; color: var(--accent); background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); padding: 4px 14px; border-radius: 6px; margin-bottom: 16px;">
                Reference: #${result.ticket_id}
              </div>
              <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6; max-width: 520px; margin: 0 auto 20px auto;">
                A confirmation email with your private dialogue link has been dispatched to <strong>${escapeHtml(email)}</strong>.<br><br>
                Our engineering team reviews all speaker requests within 48 hours. You can track progress and communicate with the maintainer below:
              </p>
              <div style="display: flex; gap: 8px; justify-content: center; max-width: 520px; margin: 0 auto 24px auto;">
                <input type="text" class="search-input" value="${fullLink}" readonly style="font-size: 0.82rem; padding: 8px 12px;">
                <button type="button" id="btn-copy-feedback-link" class="btn-header" style="background: var(--accent); color: #0b0f19; font-weight: 600; white-space: nowrap;">
                  📋 Copy Link
                </button>
              </div>
              <button type="button" class="btn-header" onclick="document.getElementById('feedback-modal-backdrop').classList.remove('open'); location.reload();" style="padding: 8px 24px;">
                Done
              </button>
            </div>
          `;
          document.getElementById("btn-copy-feedback-link").addEventListener("click", function() {
            navigator.clipboard.writeText(fullLink).then(() => {
              this.textContent = "✓ Copied!";
              setTimeout(() => (this.textContent = "📋 Copy Link"), 2000);
            });
          });
        } else {
          feedbackStatus.style.color = "#f87171";
          feedbackStatus.textContent = "Error: " + (result.error || "Submission failed.");
        }
      } catch (err) {
        feedbackStatus.style.color = "#f87171";
        feedbackStatus.textContent = "Connection error: Failed to reach /api/author-feedback.";
      }
    });
  }

  // Collaboration Inquiry Modal
  const collabModal = document.getElementById("collab-modal-backdrop");
  const btnOpenCollab = document.getElementById("btn-open-collab");
  const collabClose = document.getElementById("collab-modal-close");
  const collabCancel = document.getElementById("collab-cancel-btn");
  const collabForm = document.getElementById("collab-form");
  const collabStatus = document.getElementById("collab-status");

  const openCollab = () => collabModal && collabModal.classList.add("open");
  const closeCollab = () => collabModal && collabModal.classList.remove("open");

  if (btnOpenCollab) btnOpenCollab.addEventListener("click", openCollab);
  if (collabClose) collabClose.addEventListener("click", closeCollab);
  if (collabCancel) collabCancel.addEventListener("click", closeCollab);
  if (collabModal) collabModal.addEventListener("click", (e) => { if (e.target === collabModal) closeCollab(); });

  // Collaboration preset starters
  document.querySelectorAll(".btn-collab-starter").forEach((btn) => {
    btn.addEventListener("click", () => {
      const text = btn.getAttribute("data-starter");
      const descArea = document.getElementById("collab-description");
      if (descArea && text) {
        descArea.value = text;
        descArea.focus();
      }
    });
  });

  if (collabForm) {
    collabForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const hp = document.getElementById("collab-hp").value;
      const name = document.getElementById("collab-name").value.trim();
      const email = document.getElementById("collab-email").value.trim();
      const org = document.getElementById("collab-org").value.trim();
      const profile = document.getElementById("collab-profile").value.trim();
      const type = document.getElementById("collab-type").value;
      const description = document.getElementById("collab-description").value.trim();

      collabStatus.style.display = "block";
      collabStatus.style.color = "var(--text-secondary)";
      collabStatus.textContent = "Transmitting inquiry...";

      try {
        const res = await fetch("/api/collaboration-interest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            website_hp: hp,
            name: name,
            email: email,
            organization: org,
            profile_url: profile,
            inquiry_type: type,
            description: description
          })
        });
        const result = await res.json();
        if (res.ok && result.status === "ok") {
          const fullLink = `${window.location.origin}${result.ticket_url}`;
          collabModal.querySelector(".modal-box").innerHTML = `
            <button class="modal-close" onclick="document.getElementById('collab-modal-backdrop').classList.remove('open'); location.reload();">&times;</button>
            <div style="text-align: center; padding: 24px 12px;">
              <div style="font-size: 2.5rem; margin-bottom: 8px;">🎉</div>
              <h2 style="margin: 0 0 6px 0; font-size: 1.3rem;">Inquiry Successfully Registered!</h2>
              <div style="display: inline-block; font-size: 0.95rem; font-weight: 700; color: var(--accent); background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); padding: 4px 14px; border-radius: 6px; margin-bottom: 16px;">
                Reference: #${result.ticket_id}
              </div>
              <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6; max-width: 520px; margin: 0 auto 20px auto;">
                A confirmation email with your private dialogue link has been dispatched to <strong>${escapeHtml(email)}</strong>.<br><br>
                You can also bookmark or copy your private thread link below to message the maintainer anytime:
              </p>
              <div style="display: flex; gap: 8px; justify-content: center; max-width: 520px; margin: 0 auto 24px auto;">
                <input type="text" class="search-input" value="${fullLink}" readonly style="font-size: 0.82rem; padding: 8px 12px;">
                <button type="button" id="btn-copy-collab-link" class="btn-header" style="background: var(--accent); color: #0b0f19; font-weight: 600; white-space: nowrap;">
                  📋 Copy Link
                </button>
              </div>
              <button type="button" class="btn-header" onclick="document.getElementById('collab-modal-backdrop').classList.remove('open'); location.reload();" style="padding: 8px 24px;">
                Done
              </button>
            </div>
          `;
          document.getElementById("btn-copy-collab-link").addEventListener("click", function() {
            navigator.clipboard.writeText(fullLink).then(() => {
              this.textContent = "✓ Copied!";
              setTimeout(() => (this.textContent = "📋 Copy Link"), 2000);
            });
          });
        } else {
          collabStatus.style.color = "#f87171";
          collabStatus.textContent = "Error: " + (result.error || "Submission failed.");
        }
      } catch (err) {
        collabStatus.style.color = "#f87171";
        collabStatus.textContent = "Connection error: Failed to reach /api/collaboration-interest.";
      }
    });
  }

  // Disclaimer Modal
  const disclaimerModal = document.getElementById("disclaimer-modal-backdrop");
  const btnOpenDisclaimer = document.getElementById("btn-open-disclaimer");
  const disclaimerClose = document.getElementById("disclaimer-modal-close");
  const btnSpeakerFromDisclaimer = document.getElementById("btn-open-speaker-from-disclaimer");
  const btnCollabFromDisclaimer = document.getElementById("btn-open-collab-from-disclaimer");
  const btnLegalFromDisclaimer = document.getElementById("btn-open-legal-from-disclaimer");

  const openDisclaimer = () => disclaimerModal && disclaimerModal.classList.add("open");
  const closeDisclaimer = () => disclaimerModal && disclaimerModal.classList.remove("open");

  if (btnOpenDisclaimer) btnOpenDisclaimer.addEventListener("click", openDisclaimer);
  if (disclaimerClose) disclaimerClose.addEventListener("click", closeDisclaimer);
  if (disclaimerModal) disclaimerModal.addEventListener("click", (e) => { if (e.target === disclaimerModal) closeDisclaimer(); });

  if (btnSpeakerFromDisclaimer) {
    btnSpeakerFromDisclaimer.addEventListener("click", () => {
      closeDisclaimer();
      openFeedback();
    });
  }
  if (btnCollabFromDisclaimer) {
    btnCollabFromDisclaimer.addEventListener("click", () => {
      closeDisclaimer();
      openCollab();
    });
  }
  if (btnLegalFromDisclaimer) {
    btnLegalFromDisclaimer.addEventListener("click", () => {
      closeDisclaimer();
      openLegal();
    });
  }

  // Settings & Model Test Modal
  const settingsModal = document.getElementById("settings-modal-backdrop");
  const btnOpenSettings = document.getElementById("btn-open-settings");
  const settingsClose = document.getElementById("settings-modal-close");
  const providerSelect = document.getElementById("model-provider-select");
  const baseUrlInput = document.getElementById("model-base-url");
  const modelNameInput = document.getElementById("model-name-input");
  const apiKeyInput = document.getElementById("model-api-key");
  const btnTestModel = document.getElementById("btn-test-model");
  const testModelResult = document.getElementById("test-model-result");
  const btnCopyMcp = document.getElementById("btn-copy-mcp-json");

  const checkMixedContent = () => {
    if (window.location.protocol === "https:") {
      const warning = document.getElementById("https-mixed-content-warning");
      if (baseUrlInput && warning) {
        const url = baseUrlInput.value.trim();
        if (url.startsWith("http://")) {
          warning.style.display = "block";
        } else {
          warning.style.display = "none";
        }
      }
    }
  };

  if (baseUrlInput) {
    baseUrlInput.addEventListener("input", checkMixedContent);
  }

  // Inference Tier Tabs
  const tabCloud = document.getElementById("tab-cloud-demo");
  const tabBYOM = document.getElementById("tab-byom");
  const panelCloud = document.getElementById("panel-cloud-demo");
  const panelBYOM = document.getElementById("panel-byom");

  if (tabCloud && tabBYOM && panelCloud && panelBYOM) {
    const activeTier = localStorage.getItem("agntcon_inference_tier") || "cloud";
    if (activeTier === "cloud") {
      tabCloud.classList.add("active");
      tabBYOM.classList.remove("active");
      panelCloud.style.display = "block";
      panelBYOM.style.display = "none";
    } else {
      tabBYOM.classList.add("active");
      tabCloud.classList.remove("active");
      panelBYOM.style.display = "block";
      panelCloud.style.display = "none";
    }

    tabCloud.addEventListener("click", () => {
      localStorage.setItem("agntcon_inference_tier", "cloud");
      tabCloud.classList.add("active");
      tabBYOM.classList.remove("active");
      panelCloud.style.display = "block";
      panelBYOM.style.display = "none";
      updateChatEngineBadge();
    });

    tabBYOM.addEventListener("click", () => {
      localStorage.setItem("agntcon_inference_tier", "byom");
      tabBYOM.classList.add("active");
      tabCloud.classList.remove("active");
      panelBYOM.style.display = "block";
      panelCloud.style.display = "none";
      checkMixedContent();
      updateChatEngineBadge();
    });
  }

  // Cloud Test button
  const btnTestCloud = document.getElementById("btn-test-cloud");
  const testCloudResult = document.getElementById("test-cloud-result");
  if (btnTestCloud) {
    btnTestCloud.addEventListener("click", async () => {
      if (testCloudResult) {
        testCloudResult.style.color = "var(--text-secondary)";
        testCloudResult.textContent = "Pinging AGNTCon Cloud Proxy...";
      }
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: "Ping test", breadth: "focused" })
        });
        if (res.ok) {
          if (testCloudResult) {
            testCloudResult.style.color = "#22c55e";
            testCloudResult.textContent = "✓ Cloud Demo Online";
          }
        } else {
          if (testCloudResult) {
            testCloudResult.style.color = "#f87171";
            testCloudResult.textContent = "✕ Cloud Demo Offline (HTTP " + res.status + ")";
          }
        }
      } catch (e) {
        if (testCloudResult) {
          testCloudResult.style.color = "#f87171";
          testCloudResult.textContent = "✕ Connection Error";
        }
      }
    });
  }

  // Forget Key button
  const btnForgetKey = document.getElementById("btn-forget-key");
  if (btnForgetKey) {
    btnForgetKey.addEventListener("click", () => {
      if (apiKeyInput) apiKeyInput.value = "";
      localStorage.removeItem("agntcon_custom_key");
      btnForgetKey.textContent = "✓ Cleared";
      setTimeout(() => (btnForgetKey.textContent = "Forget Key"), 2000);
    });
  }

  // Restore saved API key from localStorage if present
  if (apiKeyInput) {
    const savedKey = localStorage.getItem("agntcon_custom_key");
    if (savedKey) apiKeyInput.value = savedKey;
    apiKeyInput.addEventListener("change", (e) => {
      localStorage.setItem("agntcon_custom_key", e.target.value.trim());
    });
  }

  // Provider presets
  if (providerSelect) {
    providerSelect.addEventListener("change", (e) => {
      const p = e.target.value;
      if (p === "lmstudio") {
        baseUrlInput.value = "http://127.0.0.1:1234/v1";
        modelNameInput.value = "huihui-qwythos-9b-claude-mythos-5-1m-abliterated";
      } else if (p === "ollama") {
        baseUrlInput.value = "http://localhost:11434/v1";
        modelNameInput.value = "qwen2.5:7b-instruct";
      } else if (p === "nvidia") {
        baseUrlInput.value = "https://integrate.api.nvidia.com/v1";
        modelNameInput.value = "nvidia/llama-3.1-nemotron-70b-instruct";
      } else if (p === "kilocode") {
        baseUrlInput.value = "https://api.kilo.ai/v1";
        modelNameInput.value = "kilo-auto/free";
      } else if (p === "openrouter") {
        baseUrlInput.value = "https://openrouter.ai/api/v1";
        modelNameInput.value = "meta-llama/llama-3.3-70b-instruct:free";
      }
      checkMixedContent();
      updateChatEngineBadge();
    });
  }

  const openSettings = () => settingsModal && settingsModal.classList.add("open");
  const closeSettings = () => settingsModal && settingsModal.classList.remove("open");

  if (btnOpenSettings) btnOpenSettings.addEventListener("click", openSettings);
  if (settingsClose) settingsClose.addEventListener("click", closeSettings);
  if (settingsModal) settingsModal.addEventListener("click", (e) => { if (e.target === settingsModal) closeSettings(); });

  if (btnCopyMcp) {
    btnCopyMcp.addEventListener("click", () => {
      const code = btnCopyMcp.parentElement.querySelector("code").innerText;
      navigator.clipboard.writeText(code).then(() => {
        btnCopyMcp.textContent = "✓ Copied!";
        setTimeout(() => (btnCopyMcp.textContent = "📋 Copy"), 2000);
      });
    });
  }

  if (btnTestModel) {
    btnTestModel.addEventListener("click", async () => {
      const baseUrl = (baseUrlInput ? baseUrlInput.value.trim() : "").replace(/\/+$/, "");
      const model = modelNameInput ? modelNameInput.value.trim() : "";
      const apiKey = apiKeyInput ? apiKeyInput.value.trim() : "";

      if (!baseUrl) {
        testModelResult.style.color = "#f87171";
        testModelResult.textContent = "Error: Base URL cannot be empty.";
        return;
      }

      testModelResult.style.color = "var(--text-secondary)";
      testModelResult.textContent = `Pinging ${baseUrl}/chat/completions with model '${model}'...`;
      const t0 = performance.now();

      try {
        const headers = { "Content-Type": "application/json" };
        if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;

        const probeUrl = `${baseUrl}/chat/completions`;
        const res = await fetch(probeUrl, {
          method: "POST",
          headers: headers,
          body: JSON.stringify({
            model: model,
            messages: [{ role: "user", content: "ping" }],
            max_tokens: 1
          })
        });

        const elapsed = Math.round(performance.now() - t0);
        if (res.ok) {
          const data = await res.json();
          if (data.choices && data.choices.length > 0) {
            testModelResult.style.color = "#22c55e";
            testModelResult.textContent = `✓ Online & Validated LLM inference model! TTFT latency: ${elapsed}ms (HTTP ${res.status})`;
          } else {
            testModelResult.style.color = "#eab308";
            testModelResult.textContent = `⚠️ Endpoint responded (${elapsed}ms), but missing choices[0].message. Verify model type.`;
          }
        } else {
          testModelResult.style.color = "#f87171";
          testModelResult.textContent = `✕ Server responded with HTTP ${res.status} (${elapsed}ms). Check model name or API key.`;
        }
      } catch (err) {
        const elapsed = Math.round(performance.now() - t0);
        testModelResult.style.color = "#f87171";
        testModelResult.textContent = `✕ Connection error (${elapsed}ms): Network/CORS failure. For Ollama, verify OLLAMA_ORIGINS="*" is set.`;
      }
    });
  }
}
