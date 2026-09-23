let ALL_TALKS = [];
let ACTIVE_TOPIC = null;
let HIGH_RELEVANCE_ONLY = false;
let SLIDES_ONLY = false;
let MISSING_SLIDES_ONLY = false;
let CURRENT_VIEW_MODE = localStorage.getItem("agntcon_view_mode") || "grid";
let CURRENT_SORT = "relevance";
let CURRENT_INFERENCE_TIER = localStorage.getItem("agntcon_inference_tier") || "cloud";

let IS_RECOMMENDED_MODE = false;
let IS_TRACK_FILTER_ACTIVE = false;

function updateMissingSlidesCount() {
  const missing = ALL_TALKS.filter((t) => !t.has_slides).length;
  const el = document.getElementById("missing-slides-count");
  if (el) el.textContent = missing;
}

// ── Zero-PII Non-Blocking Engagement Telemetry Beacon ──────────────
function sendTelemetry(eventType, metadata = {}) {
  try {
    const isAdmin = !!localStorage.getItem("agntcon_admin_token");
    const isIgnored = localStorage.getItem("agntcon_ignore_telemetry") === "true";
    const dnt = (typeof navigator !== "undefined" && navigator.doNotTrack === "1") ||
                (typeof window !== "undefined" && window.doNotTrack === "1");

    if (isAdmin || isIgnored || dnt) {
      return;
    }

    const payload = JSON.stringify({ event_type: eventType, metadata: metadata });
    if (typeof navigator !== "undefined" && navigator.sendBeacon) {
      const blob = new Blob([payload], { type: "application/json" });
      navigator.sendBeacon("/api/telemetry", blob);
    } else if (typeof fetch !== "undefined") {
      fetch("/api/telemetry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
        keepalive: true
      }).catch(() => {});
    }
  } catch (e) {
    // Non-blocking telemetry: zero user friction
  }
}

let _searchTelemetryTimer = null;
function debouncedSearchTelemetry(query, resultCount) {
  clearTimeout(_searchTelemetryTimer);
  if (!query || query.trim().length === 0) return;
  _searchTelemetryTimer = setTimeout(() => {
    sendTelemetry("search", { query: query.trim(), result_count: resultCount });
  }, 500);
}

function getUserProfile() {
  const raw = localStorage.getItem("agntcon_user_profile");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

const TAXONOMY_MAP = {
  "mcp protocol & tools": ["mcp", "tools", "protocol", "connectivity"],
  "agent sandboxing & containment": ["sandboxing", "security", "containment", "isolation", "red-teaming"],
  "ebpf & kernel monitoring": ["ebpf", "kernel", "observability", "monitoring"],
  "rag & context architecture": ["rag", "memory", "context", "compaction"],
  "llm evaluation & benchmarking": ["evaluation", "benchmarks", "metrics", "red-teaming"],
  "multi-agent orchestration": ["orchestration", "agents", "multi-agent", "consensus"]
};

function calculateProfileFit(talk, profile) {
  if (!profile) return 0;

  // 1. Focus Areas Match (normalized canonical concepts)
  const profileFocus = (profile.focus_areas || []).map(f => f.toLowerCase().trim());
  const talkConcepts = (talk.concepts || []).map(c => c.toLowerCase().trim());
  
  let matchedFocusCount = 0;
  profileFocus.forEach(f => {
    const canonicalSlugs = TAXONOMY_MAP[f] || [f];
    if (canonicalSlugs.some(slug => talkConcepts.includes(slug))) {
      matchedFocusCount++;
    }
  });
  const s_tags = profileFocus.length > 0 ? (matchedFocusCount / profileFocus.length) * 100 : 0;

  // 2. Custom Notes Keyword Match (0 - 100)
  const notesStr = (profile.custom_notes || "").toLowerCase();
  const titleStr = (talk.title || "").toLowerCase();
  const essenceStr = (talk.one_paragraph || "").toLowerCase();
  const combinedText = `${titleStr} ${essenceStr} ${talkConcepts.join(" ")}`;

  const stopWords = new Set(["the", "and", "for", "with", "that", "this", "from", "about", "what", "how", "are", "you", "your", "only", "also", "want", "more"]);
  const noteTokens = notesStr
    .split(/[^a-z0-9_-]+/)
    .filter(t => t.length > 2 && !stopWords.has(t));

  let s_notes = 0;
  if (noteTokens.length > 0) {
    const matchedTokens = noteTokens.filter(t => combinedText.includes(t));
    if (matchedTokens.length >= 3) s_notes = 100;
    else if (matchedTokens.length === 2) s_notes = 85;
    else if (matchedTokens.length === 1) s_notes = 65;
  }

  // 3. Primary Objective Match (0 - 100)
  const objStr = (profile.objective || "").toLowerCase();
  let s_obj = 60;
  if (objStr.includes("code") || objStr.includes("implement") || objStr.includes("hands-on")) {
    if (talk.has_slides || talk.file_name) s_obj += 20;
    if (talkConcepts.some(c => ["tool-use", "mcp"].includes(c))) s_obj += 20;
  } else if (objStr.includes("security") || objStr.includes("trap") || objStr.includes("harden")) {
    if (talkConcepts.some(c => ["security", "sandboxing", "evaluation"].includes(c))) s_obj += 25;
    if (combinedText.includes("vulnerability") || combinedText.includes("attack") || combinedText.includes("poison") || combinedText.includes("exploit")) s_obj += 15;
  } else if (objStr.includes("standard") || objStr.includes("protocol") || objStr.includes("trend")) {
    if (talkConcepts.some(c => ["mcp", "orchestration"].includes(c))) s_obj += 20;
    if (combinedText.includes("standard") || combinedText.includes("protocol") || combinedText.includes("spec") || combinedText.includes("rfc")) s_obj += 20;
  }
  s_obj = Math.min(100, s_obj);

  // 4. Role Match (targeted non-generic keywords)
  const roleStr = (profile.role || "").toLowerCase();
  let s_role = 60;
  if (roleStr.includes("security") || roleStr.includes("red team")) {
    if (talkConcepts.some(c => ["security", "sandboxing", "red-teaming"].includes(c))) {
      s_role = 100;
    } else if (combinedText.includes("attack") || combinedText.includes("vulnerability") || combinedText.includes("jailbreak") || combinedText.includes("exploit")) {
      s_role = 85;
    } else {
      s_role = 35;
    }
  } else if (roleStr.includes("architect") || roleStr.includes("platform") || roleStr.includes("infrastructure")) {
    if (combinedText.includes("kubernetes") || combinedText.includes("infrastructure") || combinedText.includes("scale") || combinedText.includes("production") || combinedText.includes("control plane") || talkConcepts.includes("ebpf")) {
      s_role = 95;
    } else {
      s_role = 50;
    }
  } else if (roleStr.includes("engineer") || roleStr.includes("developer") || roleStr.includes("dev")) {
    if (combinedText.includes("sdk") || combinedText.includes("code") || combinedText.includes("implementation") || combinedText.includes("tool") || combinedText.includes("framework") || talkConcepts.includes("tool-use")) {
      s_role = 95;
    } else {
      s_role = 50;
    }
  } else if (roleStr.includes("executive") || roleStr.includes("founder") || roleStr.includes("product")) {
    if (combinedText.includes("strategy") || combinedText.includes("enterprise") || combinedText.includes("governance") || combinedText.includes("ecosystem") || talk.kind === "keynote") {
      s_role = 95;
    } else {
      s_role = 40;
    }
  }

  // 5. Topic Depth baseline
  const s_depth = (talk.relevance_score || 0.8) * 100;

  // Composite Discriminative Formula (Base 0)
  let score = 0;
  if (noteTokens.length > 0) {
    score = (0.35 * s_tags) + (0.30 * s_notes) + (0.15 * s_role) + (0.10 * s_obj) + (0.10 * s_depth);
  } else if (profileFocus.length > 0) {
    score = (0.50 * s_tags) + (0.20 * s_role) + (0.15 * s_obj) + (0.15 * s_depth);
  } else {
    score = (0.40 * s_role) + (0.30 * s_obj) + (0.30 * s_depth);
  }

  // Tie-breaker subtle offset (0 - 3 pts) based on relevance
  score += (talk.relevance_score || 0.8) * 3;

  return Math.min(100, Math.max(0, Math.round(score)));
}

function getTrackThreshold() {
  return Number(localStorage.getItem("agntcon_track_threshold") || 75);
}

function curateTrackFromProfile(profile, minThreshold = null) {
  if (!profile) return [];
  const threshold = minThreshold !== null ? minThreshold : getTrackThreshold();
  const scored = ALL_TALKS.map(t => ({
    id: t.id,
    fit: calculateProfileFit(t, profile)
  })).sort((a, b) => b.fit - a.fit);

  // Take all talks meeting or exceeding the user's chosen threshold
  let matches = scored.filter(s => s.fit >= threshold).map(s => s.id);
  // Graceful fallback: if threshold is so high that 0 or fewer than 3 match, take top 3
  if (matches.length < 3 && scored.length > 0) {
    matches = scored.slice(0, Math.min(3, scored.length)).map(s => s.id);
  }
  sendTelemetry("track_curate", { threshold: threshold, talk_count: matches.length });
  return matches;
}

function getTrack() {
  try {
    return JSON.parse(localStorage.getItem("agntcon_my_track") || "[]");
  } catch (e) {
    return [];
  }
}

function toggleTrack(id) {
  let track = getTrack();
  if (track.includes(id)) {
    track = track.filter(x => x !== id);
  } else {
    track.push(id);
  }
  localStorage.setItem("agntcon_my_track", JSON.stringify(track));
  updateTrackCount();
  renderCards(); // Refresh icons on cards
  
  // If track studio modal is open, re-render it immediately
  const exportModal = document.getElementById("export-modal-backdrop");
  if (exportModal && exportModal.classList.contains("open") && typeof window.renderTrackStudio === "function") {
    window.renderTrackStudio();
  }

  // Also refresh modal toggle if open
  const modalToggle = document.querySelector("#modal-body .btn-track-toggle");
  if (modalToggle) {
    const isBookmarked = track.includes(id);
    modalToggle.innerHTML = isBookmarked ? "★ In Track" : "☆ Add to Track";
    modalToggle.classList.toggle("active", isBookmarked);
  }
}
window.toggleTrack = toggleTrack;

function updateTrackCount() {
  const track = getTrack();
  const countEl = document.getElementById("track-count");
  const filterCountEl = document.getElementById("track-filter-count");
  if (countEl) countEl.textContent = track.length;
  if (filterCountEl) filterCountEl.textContent = track.length;
}

function initTheme() {
  const themeToggle = document.getElementById('theme-toggle');
  let currentTheme = localStorage.getItem('agntcon_theme') || 'light';
  if (currentTheme !== 'light' && currentTheme !== 'dark') {
    currentTheme = 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('agntcon_theme', theme);
    if (themeToggle) {
      themeToggle.textContent = theme === 'light' ? '☀️' : '🌙';
      themeToggle.title = `Switch to ${theme === 'light' ? 'Dark' : 'Light'} theme`;
    }
  }

  applyTheme(currentTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const active = document.documentElement.getAttribute('data-theme') || 'light';
      const nextTheme = active === 'light' ? 'dark' : 'light';
      applyTheme(nextTheme);
    });
  }
}

function initApp() {
  if (typeof window !== "undefined" && window.location) {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("internal") === "1" || urlParams.get("debug") === "admin") {
      localStorage.setItem("agntcon_ignore_telemetry", "true");
      console.log("[Analytics] Browser marked as internal tester. Telemetry disabled.");
    }
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  initApp();
  initTheme();
  sendTelemetry("page_view");
  // Prevent browser form history from auto-filling into search box
  const searchInput = document.getElementById("search-input");
  const searchClear = document.getElementById("search-clear");
  if (searchInput) searchInput.value = "";
  if (searchClear) searchClear.style.display = "none";

  // Prevent stale test data from pre-populating "My Track" if no profile exists
  if (!getUserProfile() && localStorage.getItem("agntcon_track_profile_sync")) {
    localStorage.removeItem("agntcon_my_track");
    localStorage.removeItem("agntcon_track_profile_sync");
  }

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
  updateMissingSlidesCount();
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

    // Aggressive autofill guard: clean up accidental browser credential manager insertions
    const sanitizeSearch = () => {
      if (searchInput.value.startsWith("http://") || searchInput.value.startsWith("https://") || searchInput.value.includes("1234")) {
        searchInput.value = "";
        if (searchClear) searchClear.style.display = "none";
        renderCards();
      }
    };
    window.addEventListener("pageshow", sanitizeSearch);
    window.addEventListener("load", sanitizeSearch);
    searchInput.addEventListener("focus", sanitizeSearch);
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

  // Profile Modal
  const profileModal = document.getElementById("profile-modal-backdrop");
  const btnOpenProfile = document.getElementById("btn-open-profile");
  const profileClose = document.getElementById("profile-modal-close");
  const profileForm = document.getElementById("profile-form");
  const btnClearProfile = document.getElementById("btn-clear-profile");

  const updateProfileUI = () => {
    const profile = getUserProfile();
    const tabRec = document.getElementById("tab-filter-recommended");
    const recommendedCount = document.getElementById("recommended-count");
    if (profile) {
      if (tabRec) tabRec.style.display = "inline-flex";
      if (recommendedCount) {
        const matches = ALL_TALKS.filter(t => calculateProfileFit(t, profile) >= 60).length;
        recommendedCount.textContent = matches;
      }
    } else {
      if (tabRec) {
        tabRec.style.display = "none";
        IS_RECOMMENDED_MODE = false;
        tabRec.classList.remove("active");
      }
    }
    updateChatProfileIndicator();
  };

  const notesTextarea = document.getElementById("profile-custom-notes");
  const notesCountSpan = document.getElementById("profile-notes-count");
  if (notesTextarea && notesCountSpan) {
    notesTextarea.addEventListener("input", () => {
      notesCountSpan.textContent = notesTextarea.value.length;
    });
  }

  if (btnOpenProfile) {
    btnOpenProfile.addEventListener("click", () => {
      const profile = getUserProfile();
      if (profile) {
        if (document.getElementById("profile-role")) document.getElementById("profile-role").value = profile.role || "AI Engineer / Agent Dev";
        if (document.getElementById("profile-objective")) document.getElementById("profile-objective").value = profile.objective || "Hands-on Code & Implementations";
        if (notesTextarea) {
          notesTextarea.value = profile.custom_notes || "";
          if (notesCountSpan) notesCountSpan.textContent = notesTextarea.value.length;
        }
        const userFocus = (profile.focus_areas || []);
        document.querySelectorAll("#profile-focus-checkboxes input[type='checkbox']").forEach(b => {
          b.checked = userFocus.includes(b.value);
        });
      }
      if (profileModal) profileModal.classList.add("open");
    });
  }

  if (profileClose) profileClose.addEventListener("click", () => profileModal.classList.remove("open"));

  if (profileForm) {
    profileForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const role = document.getElementById("profile-role") ? document.getElementById("profile-role").value : "";
      const objective = document.getElementById("profile-objective") ? document.getElementById("profile-objective").value : "";
      const notes = notesTextarea ? notesTextarea.value.trim() : "";
      const focusBoxes = document.querySelectorAll("#profile-focus-checkboxes input[type='checkbox']:checked");
      const focus = Array.from(focusBoxes).map(b => b.value);

      const newProfile = { 
        role, 
        focus_areas: focus, 
        objective, 
        custom_notes: notes,
        updated_at: Date.now()
      };
      localStorage.setItem("agntcon_user_profile", JSON.stringify(newProfile));
      profileModal.classList.remove("open");
      updateProfileUI();
      renderCards();

      // If track studio modal is open, re-render it with new realign recommendations immediately
      const exportModal = document.getElementById("export-modal-backdrop");
      if (exportModal && exportModal.classList.contains("open") && typeof window.renderTrackStudio === "function") {
        window.renderTrackStudio();
      }
    });
  }

  if (btnClearProfile) {
    btnClearProfile.addEventListener("click", () => {
      localStorage.removeItem("agntcon_user_profile");
      if (document.getElementById("profile-role")) document.getElementById("profile-role").value = "AI Engineer / Agent Dev";
      if (notesTextarea) notesTextarea.value = "";
      if (notesCountSpan) notesCountSpan.textContent = "0";
      document.querySelectorAll("#profile-focus-checkboxes input[type='checkbox']").forEach(b => b.checked = false);
      profileModal.classList.remove("open");
      updateProfileUI();
      renderCards();
    });
  }

  // Unified Filter Tabs (My Track, Recommended, Slides, Missing Slides, Topic Depth)
  const updateFilterTabs = () => {
    const tabTrack = document.getElementById("tab-filter-track");
    const tabRec = document.getElementById("tab-filter-recommended");
    const tabSlides = document.getElementById("tab-filter-slides");
    const tabMissing = document.getElementById("tab-filter-missing-slides");
    const tabDepth = document.getElementById("tab-filter-depth");

    if (tabTrack) tabTrack.classList.toggle("active", IS_TRACK_FILTER_ACTIVE);
    if (tabRec) tabRec.classList.toggle("active", IS_RECOMMENDED_MODE);
    if (tabSlides) tabSlides.classList.toggle("active", SLIDES_ONLY);
    if (tabMissing) tabMissing.classList.toggle("active", MISSING_SLIDES_ONLY);
    if (tabDepth) tabDepth.classList.toggle("active", HIGH_RELEVANCE_ONLY);
  };

  const tabTrack = document.getElementById("tab-filter-track");
  if (tabTrack) {
    tabTrack.addEventListener("click", () => {
      IS_TRACK_FILTER_ACTIVE = !IS_TRACK_FILTER_ACTIVE;
      updateFilterTabs();
      renderCards();
    });
  }

  const tabRec = document.getElementById("tab-filter-recommended");
  if (tabRec) {
    tabRec.addEventListener("click", () => {
      IS_RECOMMENDED_MODE = !IS_RECOMMENDED_MODE;
      updateFilterTabs();
      renderCards();
    });
  }

  const tabSlides = document.getElementById("tab-filter-slides");
  if (tabSlides) {
    tabSlides.addEventListener("click", () => {
      SLIDES_ONLY = !SLIDES_ONLY;
      if (SLIDES_ONLY) {
        MISSING_SLIDES_ONLY = false;
      }
      updateFilterTabs();
      renderCards();
    });
  }

  const tabMissing = document.getElementById("tab-filter-missing-slides");
  if (tabMissing) {
    tabMissing.addEventListener("click", () => {
      MISSING_SLIDES_ONLY = !MISSING_SLIDES_ONLY;
      if (MISSING_SLIDES_ONLY) {
        SLIDES_ONLY = false;
      }
      updateFilterTabs();
      renderCards();
    });
  }

  const tabDepth = document.getElementById("tab-filter-depth");
  if (tabDepth) {
    tabDepth.addEventListener("click", () => {
      HIGH_RELEVANCE_ONLY = !HIGH_RELEVANCE_ONLY;
      updateFilterTabs();
      renderCards();
    });
  }

  // Interactive Track Studio
  const btnExportTrack = document.getElementById("btn-export-track");
  const exportModal = document.getElementById("export-modal-backdrop");
  const exportClose = document.getElementById("export-modal-close");
  const btnClearTrack = document.getElementById("btn-clear-track");
  const btnTrackItinerarySlides = document.getElementById("btn-track-itinerary-slides");
  const btnCurateTrackProfile = document.getElementById("btn-curate-track-profile");
  const trackSearchPicker = document.getElementById("track-search-picker");
  let ACTIVE_TRACK_PICKER_FILTER = "all";
  let TRACK_ITINERARY_SLIDES_ONLY = false;

  function renderTrackStudio() {
    const profile = getUserProfile();
    const trackIds = getTrack();
    const currentListEl = document.getElementById("export-track-list");
    const candidatesListEl = document.getElementById("track-candidates-list");
    const paneCountEl = document.getElementById("track-pane-count");

    let trackTalks = ALL_TALKS.filter(t => trackIds.includes(t.id));
    if (TRACK_ITINERARY_SLIDES_ONLY) {
      trackTalks = trackTalks.filter(t => t.has_slides || t.file_name);
    }
    if (paneCountEl) paneCountEl.textContent = trackTalks.length;

    // 1. Render Current Itinerary (Left Pane)
    if (currentListEl) {
      if (!profile) {
        // Stage 1: No Profile Yet
        currentListEl.innerHTML = `
          <div style="text-align: center; padding: 24px 12px; background: var(--bg-card); border-radius: 8px; border: 1px dashed var(--border);">
            <div style="font-size: 1.6rem; margin-bottom: 8px;">👤</div>
            <strong style="color: var(--text-primary); font-size: 0.92rem; display: block; margin-bottom: 6px;">
              Set Up Your Profile to Unlock AI Curation
            </strong>
            <p style="color: var(--text-secondary); margin-bottom: 14px; font-size: 0.82rem; line-height: 1.45;">
              Declare your technical role, focus areas, and goals so the AI can automatically curate and rank a personalized conference itinerary for you.
            </p>
            <button type="button" id="btn-setup-profile-from-track" class="btn-header" style="background: var(--accent); color: #0b0f19; font-weight: 600; padding: 7px 16px; font-size: 0.82rem;">
              👤 Set Up My Profile First
            </button>
          </div>
        `;
        const btnSetupProfile = document.getElementById("btn-setup-profile-from-track");
        if (btnSetupProfile) {
          btnSetupProfile.addEventListener("click", () => {
            if (exportModal) exportModal.classList.remove("open");
            const btnOpenProf = document.getElementById("btn-open-profile");
            if (btnOpenProf) btnOpenProf.click();
          });
        }
        // Update Cut-Off Threshold selector and matches label
        const thresholdSelect = document.getElementById("track-threshold-select");
        const thresholdMatches = document.getElementById("track-threshold-matches");
        if (thresholdSelect) {
          thresholdSelect.value = String(getTrackThreshold());
          if (profile && thresholdMatches) {
            const qualifyCount = ALL_TALKS.filter(t => calculateProfileFit(t, profile) >= getTrackThreshold()).length;
            thresholdMatches.textContent = `${qualifyCount} sessions qualify (≥${getTrackThreshold()}%)`;
          } else if (thresholdMatches) {
            thresholdMatches.textContent = "";
          }
        }
      } else if (trackTalks.length === 0) {
        // Stage 2: Profile Exists, but Track is Empty
        currentListEl.innerHTML = `
          <div style="text-align: center; padding: 22px 12px; background: var(--bg-card); border-radius: 8px; border: 1px solid var(--border);">
            <div style="display: inline-flex; align-items: center; gap: 6px; font-size: 0.76rem; font-weight: 600; color: var(--accent); background: var(--badge-bg); padding: 3px 10px; border-radius: 12px; margin-bottom: 8px;">
              🎯 Profile Active: ${escapeHtml(profile.role || "Specialist")}
            </div>
            <strong style="color: var(--text-primary); font-size: 0.9rem; display: block; margin-bottom: 6px;">
              Your Track Is Ready to Curate
            </strong>
            <p style="color: var(--text-secondary); margin-bottom: 14px; font-size: 0.8rem; line-height: 1.4;">
              Focus: ${(profile.focus_areas || []).map(escapeHtml).join(", ") || "General"}
            </p>
            <button type="button" id="btn-auto-curate-track" class="btn-header" style="background: var(--accent); color: #0b0f19; font-weight: 600; padding: 7px 16px; font-size: 0.82rem;">
              ✨ Curate My Track with AI (≥${getTrackThreshold()}% Fit)
            </button>
          </div>
        `;
        const btnAuto = document.getElementById("btn-auto-curate-track");
        if (btnAuto) {
          btnAuto.addEventListener("click", () => {
            const curated = curateTrackFromProfile(profile, getTrackThreshold());
            localStorage.setItem("agntcon_my_track", JSON.stringify(curated));
            localStorage.setItem("agntcon_track_profile_sync", String(profile.updated_at || Date.now()));
            updateTrackCount();
            renderCards();
            renderTrackStudio();
          });
        }
      } else {
        // Stage 3: Track is Populated
        let realignBanner = "";
        const lastSync = Number(localStorage.getItem("agntcon_track_profile_sync") || 0);
        const profileUpdated = Number(profile.updated_at || 0);
        if (profileUpdated > lastSync) {
          realignBanner = `
            <div style="background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 6px; padding: 8px 10px; margin-bottom: 8px; font-size: 0.78rem; display: flex; justify-content: space-between; align-items: center; gap: 6px;">
              <span>💡 Profile updated: recommendations have changed.</span>
              <button type="button" id="btn-realign-track" class="btn-cite" style="padding: 2px 6px; font-size: 0.72rem; color: var(--accent); font-weight: 600; white-space: nowrap;">
                🔄 Re-align Track
              </button>
            </div>
          `;
        }

        // Update Cut-Off Threshold selector and matches label for populated track
        const thresholdSelect = document.getElementById("track-threshold-select");
        const thresholdMatches = document.getElementById("track-threshold-matches");
        if (thresholdSelect) {
          thresholdSelect.value = String(getTrackThreshold());
          if (profile && thresholdMatches) {
            const qualifyCount = ALL_TALKS.filter(t => calculateProfileFit(t, profile) >= getTrackThreshold()).length;
            thresholdMatches.textContent = `${qualifyCount} sessions qualify (≥${getTrackThreshold()}%)`;
          } else if (thresholdMatches) {
            thresholdMatches.textContent = "";
          }
        }

        currentListEl.innerHTML = realignBanner + trackTalks.map(t => {
          const fitScore = calculateProfileFit(t, profile);
          return `
          <div class="track-item">
            <div style="min-width: 0;">
              <a href="#/session/${t.id}" onclick="openEssenceModal('${t.id}')" style="color: var(--accent); font-weight: 700; text-decoration: underline; font-size: 0.85rem; margin-right: 4px;">[${t.id}]</a>
              <strong style="font-size: 0.84rem; color: var(--text-primary);">${escapeHtml(t.title.replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, ""))}</strong><br>
              <span style="font-size: 0.76rem; color: var(--text-secondary);">${escapeHtml((t.speakers || []).join(", "))}</span>
              ${(t.has_slides || t.file_name) ? '<span style="font-size: 0.72rem; color: #22c55e; margin-left: 6px;">📄 Slides</span>' : ''}
              <span style="font-size: 0.72rem; color: var(--accent); font-weight: 600; margin-left: 6px;">Fit: ${fitScore}%</span>
            </div>
            <div style="display: flex; gap: 4px; align-items: center; flex-shrink: 0;">
              <button type="button" class="btn-cite" onclick="openEssenceModal('${t.id}')" style="padding: 3px 6px; font-size: 0.72rem;">Essence</button>
              <button type="button" class="btn-cite" onclick="toggleTrack('${t.id}');" style="padding: 3px 6px; font-size: 0.72rem; color: #ef4444;" title="Remove from track">✕</button>
            </div>
          </div>
        `;
        }).join("");

        const btnRealign = document.getElementById("btn-realign-track");
        if (btnRealign) {
          btnRealign.addEventListener("click", () => {
            const curated = curateTrackFromProfile(profile, getTrackThreshold());
            localStorage.setItem("agntcon_my_track", JSON.stringify(curated));
            localStorage.setItem("agntcon_track_profile_sync", String(profile.updated_at || Date.now()));
            updateTrackCount();
            renderCards();
            renderTrackStudio();
          });
        }
      }
    }

    // 2. Render Candidates Picker (Right Pane)
    if (candidatesListEl) {
      const searchVal = (trackSearchPicker ? trackSearchPicker.value : "").trim().toLowerCase();
      let candidates = ALL_TALKS.filter(t => !trackIds.includes(t.id));

      if (searchVal) {
        candidates = candidates.filter(t => {
          const blob = `${t.id} ${t.title} ${(t.speakers || []).join(" ")} ${(t.concepts || []).join(" ")}`.toLowerCase();
          return blob.includes(searchVal);
        });
      }

      if (ACTIVE_TRACK_PICKER_FILTER === "profile") {
        candidates = candidates.filter(t => calculateProfileFit(t, profile) >= 40);
        candidates.sort((a, b) => calculateProfileFit(b, profile) - calculateProfileFit(a, profile));
      } else if (ACTIVE_TRACK_PICKER_FILTER === "slides") {
        candidates = candidates.filter(t => t.has_slides || t.file_name);
      } else if (ACTIVE_TRACK_PICKER_FILTER === "mcp") {
        candidates = candidates.filter(t => (t.concepts || []).includes("mcp"));
      } else if (ACTIVE_TRACK_PICKER_FILTER === "security") {
        candidates = candidates.filter(t => (t.concepts || []).some(c => ["security", "sandboxing", "red-teaming"].includes(c)));
      } else if (ACTIVE_TRACK_PICKER_FILTER === "ebpf") {
        candidates = candidates.filter(t => (t.concepts || []).includes("ebpf"));
      } else if (ACTIVE_TRACK_PICKER_FILTER === "rag") {
        candidates = candidates.filter(t => (t.concepts || []).some(c => ["rag", "memory"].includes(c)));
      }

      if (candidates.length === 0) {
        candidatesListEl.innerHTML = `<div style="text-align: center; padding: 20px 10px; color: var(--text-secondary); font-size: 0.82rem;">No additional matching sessions found.</div>`;
      } else {
        candidatesListEl.innerHTML = candidates.map(t => {
          const fitScore = profile ? calculateProfileFit(t, profile) : Math.round((t.relevance_score || 0.8) * 100);
          return `
            <div class="track-item">
              <div style="min-width: 0;">
                <span style="font-size: 0.82rem; font-weight: 700; color: var(--accent);">[${t.id}]</span>
                <span style="font-size: 0.82rem; color: var(--text-primary); margin-left: 4px;">${escapeHtml(t.title.replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, ""))}</span><br>
                <span style="font-size: 0.74rem; color: var(--text-secondary);">${escapeHtml((t.speakers || []).join(", "))}</span>
                ${(t.has_slides || t.file_name) ? '<span style="font-size: 0.72rem; color: #22c55e; margin-left: 4px;">📄</span>' : ''}
                <span style="font-size: 0.72rem; color: var(--accent); margin-left: 6px;">Fit: ${fitScore}%</span>
              </div>
              <button type="button" class="track-add-btn" onclick="toggleTrack('${t.id}');">+ Add</button>
            </div>
          `;
        }).join("");
      }
    }
  }
  window.renderTrackStudio = renderTrackStudio;

  if (btnExportTrack) {
    btnExportTrack.addEventListener("click", () => {
      renderTrackStudio();
      if (exportModal) exportModal.classList.add("open");
    });
  }

  if (trackSearchPicker) {
    trackSearchPicker.addEventListener("input", () => renderTrackStudio());
  }

  if (btnTrackItinerarySlides) {
    btnTrackItinerarySlides.addEventListener("click", () => {
      TRACK_ITINERARY_SLIDES_ONLY = !TRACK_ITINERARY_SLIDES_ONLY;
      btnTrackItinerarySlides.classList.toggle("active", TRACK_ITINERARY_SLIDES_ONLY);
      renderTrackStudio();
    });
  }

  document.querySelectorAll(".track-filter-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".track-filter-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      ACTIVE_TRACK_PICKER_FILTER = chip.getAttribute("data-track-filter") || "all";
      renderTrackStudio();
    });
  });

  const thresholdSelectEl = document.getElementById("track-threshold-select");
  if (thresholdSelectEl) {
    thresholdSelectEl.addEventListener("change", (e) => {
      const newThreshold = Number(e.target.value);
      localStorage.setItem("agntcon_track_threshold", String(newThreshold));
      const profile = getUserProfile();
      if (profile) {
        const curated = curateTrackFromProfile(profile, newThreshold);
        localStorage.setItem("agntcon_my_track", JSON.stringify(curated));
        localStorage.setItem("agntcon_track_profile_sync", String(profile.updated_at || Date.now()));
        updateTrackCount();
        renderCards();
        renderTrackStudio();
      }
    });
  }

  if (btnCurateTrackProfile) {
    btnCurateTrackProfile.addEventListener("click", () => {
      const profile = getUserProfile();
      if (!profile) {
        if (exportModal) exportModal.classList.remove("open");
        const btnOpenProf = document.getElementById("btn-open-profile");
        if (btnOpenProf) btnOpenProf.click();
        return;
      }
      const curated = curateTrackFromProfile(profile, getTrackThreshold());
      localStorage.setItem("agntcon_my_track", JSON.stringify(curated));
      localStorage.setItem("agntcon_track_profile_sync", String(profile.updated_at || Date.now()));
      updateTrackCount();
      renderCards();
      renderTrackStudio();
    });
  }

  if (btnClearTrack) {
    btnClearTrack.addEventListener("click", () => {
      localStorage.removeItem("agntcon_my_track");
      updateTrackCount();
      renderCards();
      renderTrackStudio();
    });
  }

  if (exportClose) exportClose.addEventListener("click", () => exportModal.classList.remove("open"));

  // Obsidian Export
  const btnDownloadObsidian = document.getElementById("btn-download-obsidian-zip");
  if (btnDownloadObsidian) {
    btnDownloadObsidian.addEventListener("click", async () => {
      if (typeof JSZip === 'undefined') {
        alert("JSZip library not loaded. Ensure it is included in your index.html.");
        return;
      }
      const trackIds = getTrack();
      const trackTalks = ALL_TALKS.filter(t => trackIds.includes(t.id));

      if (trackTalks.length === 0) {
        alert("Your track is empty. Add sessions to your track before exporting.");
        return;
      }

      sendTelemetry("track_export_obsidian", { talk_count: trackTalks.length });
      btnDownloadObsidian.textContent = "⏳ Bundling Vault...";

      const zip = new JSZip();

      // 00_Conference_Itinerary.md
      let itineraryMd = "# AGNTCon + MCPCon Europe 2026: My Itinerary\n\n";
      itineraryMd += "| ID | Title | Speaker | Sched Link |\n|---|---|---|---|\n";
      trackTalks.forEach(t => {
        const cleanTitle = t.title.replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
        itineraryMd += `| [[${t.id}]] | ${cleanTitle} | ${(t.speakers || []).join(", ")} | [Official Sched](${t.sched_url}) |\n`;
      });
      zip.file("00_Conference_Itinerary.md", itineraryMd);

      // Sessions/ folder with FULL, UNABRIDGED ESSENCE
      const sessionsFolder = zip.folder("Sessions");
      for (const t of trackTalks) {
        const cleanTitle = t.title.replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
        const safeTitle = cleanTitle.replace(/[/\\?%*:|"<>]/g, '-');
        
        let fullMarkdown = "";
        try {
          const res = await fetch(`/api/page?type=source&name=${t.id}`);
          if (res.ok) {
            const data = await res.json();
            fullMarkdown = data.content || "";
          }
        } catch (e) {
          console.warn("Could not fetch full essence for " + t.id, e);
        }

        if (!fullMarkdown) {
          const frontmatter = {
            id: t.id,
            title: cleanTitle,
            speakers: t.speakers || [],
            concepts: t.concepts || [],
            sched_url: t.sched_url,
            exported: new Date().toISOString()
          };
          fullMarkdown = `---\n${JSON.stringify(frontmatter, null, 2)}\n---\n\n# ${cleanTitle}\n\n**Speakers:** ${(t.speakers || []).join(", ")}\n\n## Summary\n${t.one_paragraph || ""}\n\n## Links\n- [Official Sched](${t.sched_url})\n`;
        }
        
        sessionsFolder.file(`${t.id} - ${safeTitle}.md`, fullMarkdown);
      }

      // Concepts/
      const conceptsFolder = zip.folder("Concepts");
      const allConcepts = new Set();
      trackTalks.forEach(t => (t.concepts || []).forEach(c => allConcepts.add(c)));
      allConcepts.forEach(c => {
        const related = trackTalks.filter(t => (t.concepts || []).includes(c));
        let conceptMd = `# Concept: ${c}\n\n## Related Sessions\n`;
        related.forEach(r => {
          conceptMd += `- [[${r.id}]] - ${r.title.replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim()}\n`;
        });
        conceptsFolder.file(`${c.replace(/[/\\?%*:|"<>]/g, '-')}.md`, conceptMd);
      });

      const blob = await zip.generateAsync({ type: "blob" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "agntcon2026_obsidian_vault.zip";
      a.click();
      window.URL.revokeObjectURL(url);
      btnDownloadObsidian.textContent = "💾 Download Obsidian Vault (.zip)";
    });
  }

  // PDF Export
  const btnExportPdf = document.getElementById("btn-export-pdf-dossier");
  if (btnExportPdf) {
    btnExportPdf.addEventListener("click", async () => {
      const trackIds = getTrack();
      const trackTalks = ALL_TALKS.filter(t => trackIds.includes(t.id));
      const profile = getUserProfile();
      const printable = document.getElementById("printable-dossier");
      
      if (!printable) {
        alert("Printable container not found in DOM.");
        return;
      }
      
      if (trackTalks.length === 0) {
        alert("Your track is empty. Add sessions to your track before exporting.");
        return;
      }

      sendTelemetry("track_export_pdf", { talk_count: trackTalks.length });
      btnExportPdf.textContent = "⏳ Generating Dossier...";

      // Fetch full unabridged essence for each session in parallel
      const detailedSessions = await Promise.all(trackTalks.map(async (t) => {
        let fullContent = "";
        try {
          const res = await fetch(`/api/page?type=source&name=${t.id}`);
          if (res.ok) {
            const data = await res.json();
            fullContent = data.content || "";
          }
        } catch (e) {}
        return { talk: t, fullContent: fullContent };
      }));

      btnExportPdf.textContent = "📄 Save / Print Single PDF Dossier";

      let html = `
        <div class="print-cover">
          <h1>AGNTCon + MCPCon Europe 2026</h1>
          <div class="print-subtitle">Comprehensive Research Briefing & Curated Itinerary</div>
          <p style="font-size: 10pt; color: #666; margin-top: 4px;"><strong>Generated:</strong> ${new Date().toLocaleDateString()}</p>
          ${profile ? `
            <div style="margin-top: 14px; padding: 12px; border: 1px solid #ddd; background: #f9f9f9; font-size: 10pt;">
              <strong>Attendee Profile:</strong> ${escapeHtml(profile.role || "Specialist")}<br>
              <strong>Focus Areas:</strong> ${escapeHtml((profile.focus_areas || []).join(", ") || "All")}<br>
              ${profile.custom_notes ? `<strong>Goals:</strong> ${escapeHtml(profile.custom_notes)}` : ""}
            </div>
          ` : ""}
        </div>
        
        <h3 style="margin-top: 20px; font-size: 14pt;">Curated Itinerary Index</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 9.5pt;">
          <thead>
            <tr style="border-bottom: 2px solid #000;">
              <th style="text-align: left; padding: 6px;">ID</th>
              <th style="text-align: left; padding: 6px;">Presentation Title</th>
              <th style="text-align: left; padding: 6px;">Speaker(s)</th>
              <th style="text-align: left; padding: 6px;">Official Sched</th>
            </tr>
          </thead>
          <tbody>
            ${trackTalks.map(t => `
              <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 6px; font-weight: bold;">${t.id}</td>
                <td style="padding: 6px;">${escapeHtml(t.title.replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, ""))}</td>
                <td style="padding: 6px;">${escapeHtml((t.speakers || []).join(", "))}</td>
                <td style="padding: 6px;"><a href="${escapeHtml(t.sched_url)}">Sched Link ↗</a></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
        
        <div class="print-sessions-detail">
          ${detailedSessions.map(({ talk: t, fullContent }) => {
            const cleanTitle = t.title.replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
            const firstSentence = (t.one_paragraph || "").split(/[.!?]\s/)[0].trim() + ".";
            
            // Format full markdown content, stripping YAML frontmatter for clean print layout
            let formattedEssenceHtml = "";
            if (fullContent) {
              const strippedMd = fullContent.replace(/^---[\s\S]*?---\n*/, "");
              if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
                formattedEssenceHtml = DOMPurify.sanitize(marked.parse(strippedMd));
              } else {
                formattedEssenceHtml = `<div style="white-space: pre-wrap;">${escapeHtml(strippedMd)}</div>`;
              }
            } else {
              formattedEssenceHtml = `<p>${escapeHtml(t.one_paragraph || "")}</p>`;
            }

            return `
              <div class="print-session-card">
                <div style="display: flex; justify-content: space-between; font-size: 10pt; color: #555;">
                  <span style="font-weight: bold; color: #000;">[${t.id}]</span>
                  <span><a href="${escapeHtml(t.sched_url)}">${escapeHtml(t.sched_url)}</a></span>
                </div>
                <h2 style="margin: 8px 0 6px 0; font-size: 16pt;">${escapeHtml(cleanTitle)}</h2>
                <p style="font-size: 10pt; color: #333; margin-bottom: 8px;"><strong>Speaker(s):</strong> ${escapeHtml((t.speakers || []).join(", "))}</p>
                <div class="print-takeaway">
                  <strong>💡 Key Takeaway:</strong> ${escapeHtml(firstSentence)}
                </div>
                <div class="markdown-content" style="font-size: 9.5pt; line-height: 1.5; color: #111;">
                  ${formattedEssenceHtml}
                </div>
              </div>
            `;
          }).join("")}
        </div>
      `;
      
      printable.innerHTML = html;
      window.print();
    });
  }

  // Initial UI refresh
  updateProfileUI();
  updateTrackCount();

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
  updateMissingSlidesCount();
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
    if (MISSING_SLIDES_ONLY && t.has_slides) return false;
    if (ACTIVE_TOPIC && !(t.concepts || []).map((c) => c.toLowerCase()).includes(ACTIVE_TOPIC)) return false;
    if (IS_TRACK_FILTER_ACTIVE && !getTrack().includes(t.id)) return false;

    const profile = getUserProfile();
    t._profileFit = profile ? calculateProfileFit(t, profile) : 0;

    if (IS_RECOMMENDED_MODE) {
      if (t._profileFit < 50) return false;
    }

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

  if (q) {
    debouncedSearchTelemetry(q, filtered.length);
  }

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
      // Relevance sort: dynamic match if query active, otherwise recommended fit, otherwise intrinsic topic depth
      if (q) {
        return (b._matchScore || 0) - (a._matchScore || 0);
      } else if (IS_RECOMMENDED_MODE) {
        return (b._profileFit || 0) - (a._profileFit || 0);
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
        const isCommunitySlide = (t.slide_source === "community") || t.id === "2RBA6";
        const hasRepo = !!(t.repos && t.repos.length > 0);
        let badgesHtml = "";
        if (isKeynote) badgesHtml += '<span class="badge badge-keynote">🎙️ Keynote</span>';
        if (hasSlides) {
          if (isCommunitySlide) {
            badgesHtml += '<span class="badge" style="background: rgba(168, 85, 247, 0.12); color: #a855f7; border: 1px solid rgba(168, 85, 247, 0.3);" title="Exclusively added by author/community — not available on the official Sched conference site!">🌟 Author Added Slides</span>';
          } else {
            badgesHtml += '<span class="badge badge-slides" title="Official slides from Sched conference archive">📄 Slides Available</span>';
          }
        }
        if (hasRepo) badgesHtml += '<span class="badge badge-repo">💻 GitHub Repo</span>';

        const profile = getUserProfile();
        let scoreBadge = "";
        if (q && t._matchScore != null) {
          scoreBadge = `<span class="relevance-score match-active" title="Dynamic search query match score">🎯 Query Match: ${t._matchScore}%</span>`;
        } else if (profile) {
          scoreBadge = `<span class="relevance-score" title="Match based on your interest profile">🎯 Profile Fit: ${t._profileFit}%</span>`;
        } else {
          scoreBadge = `<span class="relevance-score" title="Intrinsic conference topic depth">⭐ Topic Depth: ${Math.round((t.relevance_score || 0.8) * 100)}%</span>`;
        }

        const track = getTrack();
        const isBookmarked = track.includes(t.id);
        const trackBtn = `<button class="btn-track-toggle ${isBookmarked ? "active" : ""}" onclick="toggleTrack('${t.id}')">${isBookmarked ? "★ In Track" : "☆ Add to Track"}</button>`;

        const firstSentence = (t.one_paragraph || "").split(/[.!?]\s/)[0].trim() + ".";
        const takeawayBadge = `<div class="card-takeaway-badge">💡 <strong>Key Takeaway:</strong> ${escapeHtml(firstSentence)}</div>`;

        let directSlideBtn = "";
        if (!hasSlides) {
          directSlideBtn = `<button class="btn-view-essence" onclick="openContributeModal('${t.id}')" style="background: rgba(56, 189, 248, 0.12); border-color: rgba(56, 189, 248, 0.4); color: var(--accent);" title="Upload missing presentation slides or claim session">[ + Add Slides ]</button>`;
        }

        return `
    <div class="session-card">
      <div class="card-header">
        <div class="card-meta">
          <span class="card-id">[${t.id}]</span>
          ${scoreBadge}
          ${trackBtn}
        </div>
        <h3 class="card-title session-title">${escapeHtml(cleanTitle)}</h3>
        ${takeawayBadge}
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
      <td><a href="#/session/${t.id}" class="card-id" style="text-decoration: none;" onclick="openEssenceModal('${t.id}')">[${t.id}]</a></td>
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
          ${hasSlides ? '' : `<button class="btn-view-essence" onclick="openContributeModal('${t.id}')" style="padding: 4px 8px; font-size: 0.78rem; background: rgba(56, 189, 248, 0.12); border-color: rgba(56, 189, 248, 0.4); color: var(--accent);">+ Slides</button>`}
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
  const talkObj = (typeof ALL_TALKS !== "undefined" && ALL_TALKS.length > 0) ? ALL_TALKS.find(t => t.id === sid) : null;
  sendTelemetry("talk_opened", { talk_id: sid, title: talkObj ? talkObj.title : sid });
  const modalBackdrop = document.getElementById("modal-backdrop");
  const modalBody = document.getElementById("modal-body");
  const titleEl = document.getElementById("essence-modal-title");
  const trackBtnContainer = document.getElementById("essence-modal-track-btn");
  
  if (location.hash !== `#/session/${sid}`) {
    history.pushState(null, "", `#/session/${sid}`);
  }
  
  const track = getTrack();
  const isBookmarked = track.includes(sid);
  const trackBtn = `<button class="btn-track-toggle ${isBookmarked ? "active" : ""}" onclick="toggleTrack('${sid}')">${isBookmarked ? "★ In Track" : "☆ Add to Track"}</button>`;

  if (titleEl) {
    titleEl.innerHTML = `Presentation Essence: <span style="color: var(--accent);">[${escapeHtml(sid)}]</span>`;
  }
  if (trackBtnContainer) {
    trackBtnContainer.innerHTML = trackBtn;
  }
  if (modalBody) {
    modalBody.innerHTML = `<div style="padding: 20px 0; color: var(--text-secondary);">Loading distilled Karpathy essence...</div>`;
  }
  if (modalBackdrop) modalBackdrop.classList.add("open");

  try {
    const res = await fetch(`/api/page?type=source&name=${sid}`);
    if (res.ok) {
      const data = await res.json();
      let rawContent = data.content || "No essence content found.";
      
      // CRITICAL FIX: Strip YAML frontmatter so raw metadata never bleeds above header or into markdown view
      rawContent = rawContent.replace(/^---[\s\S]*?---\n*/, "");

      // Transform [[wikilinks]]:
      // - If session ID (e.g. 2RBBJ), render interactive session pill
      // - If keyword/concept (e.g. sandboxing), render clean tag without brackets
      let processed = rawContent.replace(/\[\[([A-Za-z0-9_-]+)\]\]/g, (match, p1) => {
        const isSession = ALL_TALKS.some((t) => t.id.toLowerCase() === p1.toLowerCase());
        if (isSession) {
          return `<a href="#/session/${p1}" class="wikilink-pill" data-session-id="${p1}">[${p1}]</a>`;
        } else {
          return `<span class="card-tag" style="display: inline-block; margin: 2px 4px; font-size: 0.78rem;" onclick="closeModal(); filterByConcept('${escapeHtml(p1)}')">${escapeHtml(p1)}</span>`;
        }
      });

      const isCommunitySlide = (talkObj && talkObj.slide_source === "community") || sid === "2RBA6";
      if (isCommunitySlide) {
        const communityLink = `\n- [🌟 Author-Contributed Presentation Slides (Community Open Access)](/assets/slides/${sid}.pdf) — *Shared by presenter under community license*\n`;
        if (processed.includes("## Discovered Resources")) {
          processed = processed.replace("## Discovered Resources\n", `## Discovered Resources\n${communityLink}`);
        } else {
          processed += `\n\n## Discovered Resources\n${communityLink}`;
        }
      }

      let htmlOutput = "";
      if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
        htmlOutput = DOMPurify.sanitize(marked.parse(processed));
      } else {
        htmlOutput = `<div style="white-space: pre-wrap;">${escapeHtml(processed)}</div>`;
      }

      if (modalBody) {
        modalBody.innerHTML = `<div class="markdown-content">${htmlOutput}</div>`;
      }

      // Enhance code blocks with copy snippet buttons
      if (modalBody) {
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
      }

    } else {
      if (modalBody) {
        modalBody.innerHTML = `<p style="padding: 20px 0; color: var(--text-secondary);">Source essence for <strong>${escapeHtml(sid)}</strong> is currently in ingestion pipeline.</p>`;
      }
    }
  } catch (e) {
    if (modalBody) {
      modalBody.innerHTML = `<p style="padding: 20px 0; color: #f87171;">Error loading essence for ${escapeHtml(sid)}: ${escapeHtml(e.message)}</p>`;
    }
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

function normalizeChatCompletionsUrl(baseUrl) {
  let url = (baseUrl || "").trim().replace(/\/+$/, "");
  if (!url) return "";
  if (url.endsWith("/chat/completions")) return url;
  if (!url.endsWith("/v1")) {
    url = `${url}/v1`;
  }
  return `${url}/chat/completions`;
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
    const p = providerSelect ? providerSelect.value : "local";
    if (p === "local") {
      badge.textContent = "💻 Local LLM";
    } else if (p === "nvidia") {
      badge.textContent = "🔑 NVIDIA NIM";
    } else if (p === "kilocode") {
      badge.textContent = "🔑 Kilocode";
    } else if (p === "openrouter") {
      badge.textContent = "🔑 OpenRouter";
    } else {
      badge.textContent = "💻 Custom / BYOM";
    }
    badge.style.background = "rgba(34, 197, 94, 0.15)";
    badge.style.color = "#22c55e";
  }
}

function updateChatProfileIndicator() {
  const el = document.getElementById("chat-profile-text");
  if (!el) return;
  const profile = getUserProfile();
  if (profile && (profile.role || (profile.focus_areas && profile.focus_areas.length > 0))) {
    const roleStr = profile.role || "Specialist";
    const focusStr = (profile.focus_areas && profile.focus_areas.length > 0) ? profile.focus_areas.slice(0, 2).join(", ") : "General";
    el.innerHTML = `🎯 Tailored for: <strong style="color: var(--accent);">${escapeHtml(roleStr)}</strong> • ${escapeHtml(focusStr)} <a href="javascript:void(0)" onclick="document.getElementById('btn-open-profile').click()" style="color: var(--accent); margin-left: 6px; text-decoration: underline;">(Edit)</a>`;
  } else {
    el.innerHTML = `💡 <a href="javascript:void(0)" onclick="document.getElementById('btn-open-profile').click()" style="color: var(--accent); text-decoration: underline;">Set up your Profile</a> to get tailored recommendations and answers.`;
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
  updateChatProfileIndicator();

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

  toggleBtn.addEventListener("click", () => {
    chatPanel.classList.toggle("open");
    updateChatProfileIndicator();
  });
  chatClose.addEventListener("click", () => chatPanel.classList.remove("open"));

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const q = chatInput.value.trim();
    if (!q) return;

    appendMsg(q, "user");
    chatInput.value = "";

    const loadingHtml = `
      <div class="ai-loading-container">
        <span class="ai-spinner"></span>
        <span class="ai-loading-text">Synthesizing answer from conference knowledge base...</span>
      </div>
    `;
    const loadingId = appendMsg(loadingHtml, "bot", true);
    const onlySlides = document.getElementById("chat-slides-only") ? document.getElementById("chat-slides-only").checked : false;
    const breadthSelect = document.getElementById("rag-breadth-select");
    const breadth = breadthSelect ? breadthSelect.value : "auto";
    const tier = localStorage.getItem("agntcon_inference_tier") || "cloud";
    sendTelemetry("chat_query", { tier: tier, breadth: breadth });

    // 1. BYOM: Direct Browser-Side Execution (Local or Custom Cloud)
    if (tier === "byom") {
      const baseUrlInput = document.getElementById("model-base-url");
      const modelNameInput = document.getElementById("model-name-input");
      const apiKeyInput = document.getElementById("model-api-key");
      const rawBase = (baseUrlInput && baseUrlInput.value.trim()) || localStorage.getItem("agntcon_custom_base_url") || "http://127.0.0.1:1234/v1";
      const modelName = (modelNameInput && modelNameInput.value.trim()) || localStorage.getItem("agntcon_custom_model_name") || "";
      const apiKey = (apiKeyInput && apiKeyInput.value.trim()) || localStorage.getItem("agntcon_custom_key") || "";
      const completionsUrl = normalizeChatCompletionsUrl(rawBase);

      try {
        // Fetch RAG context from local search endpoint
        const searchRes = await fetch(`/api/search?q=${encodeURIComponent(q)}&only_with_slides=${onlySlides ? "1" : "0"}&limit=6`);
        const searchData = await searchRes.json();
        const topMatches = (Array.isArray(searchData) ? searchData : (searchData.results || [])).slice(0, 5);

        // Hydrate full source essence notes for focused candidates
        const candidatePromises = topMatches.map(async (m, idx) => {
          let fullText = m.one_paragraph || "";
          try {
            const pageRes = await fetch(`/api/page?type=source&name=${m.id}`);
            if (pageRes.ok) {
              const pageData = await pageRes.json();
              if (pageData.content) {
                fullText = pageData.content.replace(/^---[\s\S]*?---\n*/, "").trim();
              }
            }
          } catch (e) {}
          return `<candidate index="${idx + 1}" id="${m.id}">\nTitle: ${m.title}\nSpeakers: ${(m.speakers || []).join(", ")}\nSched URL: ${m.sched_url}\nSummary & Full Distilled Essence:\n${fullText}\n</candidate>`;
        });
        const contextSnippets = await Promise.all(candidatePromises);

        // Inject Attendee Profile for parity with Cloud Gateway
        const profile = getUserProfile();
        let profileSnippet = "";
        if (profile) {
          const parts = [];
          if (profile.role) parts.push(`Role: ${profile.role}`);
          if (profile.focus_areas && profile.focus_areas.length) parts.push(`Focus Areas: ${profile.focus_areas.join(", ")}`);
          if (profile.objective) parts.push(`Objective: ${profile.objective}`);
          if (profile.custom_notes) parts.push(`Specific Technical Goals / Notes: ${profile.custom_notes}`);
          if (parts.length) {
            profileSnippet = `\n\n<attendee_profile>\n${parts.join("\n")}\n</attendee_profile>`;
          }
        }

        const systemPrompt = `You are the research assistant for AGNTCon + MCPCon Europe 2026.
Answer the user's question clearly, thoroughly, and completely based strictly on the provided conference excerpts.

CRITICAL INVARIANTS:
1. Every major claim or practice described MUST cite the session ID (e.g. [2RBBJ]) and include an outbound Markdown link to the canonical Sched presentation: [Presentation Title](https://agntconmcpconeu26.sched.com/event/...).
2. If the user asks for a list, ranking, or comparison of multiple talks, enumerate all matching candidates using a structured numbered list or Markdown table. Complete all requested points in full without truncation.
3. If the topic was not discussed in the provided excerpts, state: "This topic was not covered in the conference sessions."
4. Always cite speakers by name.
5. Tailor technical depth, architectural framing, and practical takeaways to the attendee's declared profile where applicable.`;

        const userMsg = `Question: ${q}${profileSnippet}\n\n<conference_excerpts>\n${contextSnippets.join("\n\n")}\n</conference_excerpts>`;

        const headers = { "Content-Type": "application/json" };
        if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;

        const reqBody = {
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userMsg }
          ],
          max_tokens: 2500,
          temperature: 0.2
        };
        if (modelName) reqBody.model = modelName;

        const llmRes = await fetch(completionsUrl, {
          method: "POST",
          headers: headers,
          body: JSON.stringify(reqBody)
        });

        const botEl = document.getElementById(loadingId);
        if (llmRes.ok) {
          const llmData = await llmRes.json();
          const answerText = (llmData.choices && llmData.choices[0] && llmData.choices[0].message) ? llmData.choices[0].message.content : "No response content.";
          let html = `<div>${formatBotMarkdown(answerText)}</div>`;

          // Filter citations to only those actually referenced in the answer
          const citedSessions = topMatches.filter(m => 
            answerText.toLowerCase().includes(m.id.toLowerCase()) || 
            answerText.toLowerCase().includes(m.title.toLowerCase())
          );
          const displayedCitations = citedSessions.length > 0 ? citedSessions : topMatches.slice(0, 3);

          if (displayedCitations.length > 0) {
            html += `<div class="chat-citations" style="margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border); font-size: 0.82rem;">
              <strong style="color: var(--text-primary);">Referenced Presentations:</strong><br>
              ${displayedCitations.map((c) => `
                <div style="margin-top: 6px; line-height: 1.4;">
                  <strong>[${escapeHtml(c.id)}]</strong> ${escapeHtml(c.title)}<br>
                  <span style="font-size: 0.78rem;">
                    <a href="javascript:void(0)" onclick="openEssenceModal('${escapeHtml(c.id)}')" style="color: var(--accent); font-weight: 600; text-decoration: underline; margin-right: 8px;">📖 View Summary / Essence</a>
                    <a href="${escapeHtml(c.sched_url)}" target="_blank" rel="noopener" style="color: var(--text-secondary); text-decoration: underline;">Official Sched ↗</a>
                  </span>
                </div>
              `).join("")}
            </div>`;
          }

          const responseId = "resp_" + Math.random().toString(36).substring(2, 9);
          registerBotResponse(responseId, q, answerText, displayedCitations);
          html += renderBotActionsHtml(responseId);
          botEl.innerHTML = html;
        } else {
          botEl.innerHTML = `<div style="color: #f87171;">Local LLM error (HTTP ${llmRes.status}). Verify model name '${escapeHtml(modelName || "loaded model")}' at ${escapeHtml(completionsUrl)}.</div>`;
        }
      } catch (err) {
        const botEl = document.getElementById(loadingId);
        if (window.location.protocol === "https:" && completionsUrl.startsWith("http://")) {
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
              <strong style="color: #ef4444;">✕ Inference Provider at ${escapeHtml(completionsUrl)} is unreachable.</strong><br><br>
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
    const queueIndicator = document.getElementById("chat-queue-indicator");
    let queuePollInterval = null;

    if (queueIndicator) {
      queueIndicator.style.display = "inline";
      queueIndicator.textContent = "Checking queue...";
    }

    const pollQueue = async () => {
      try {
        const qRes = await fetch("/api/queue-status");
        if (qRes.ok) {
          const qData = await qRes.json();
          const waiting = qData.waiting_tasks ?? qData.waiting_depth ?? 0;
          if (queueIndicator) {
            if (waiting > 0) {
              queueIndicator.textContent = `Position in queue: #${waiting} (estimated wait: ~${waiting * 3}s)...`;
            } else {
              queueIndicator.textContent = "Synthesizing answer with grounded citations...";
            }
          }
        }
      } catch (e) {
        // ignore telemetry polling failure
      }
    };

    pollQueue();
    queuePollInterval = setInterval(pollQueue, 2000);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonSafe({ 
          question: q, 
          only_with_slides: onlySlides, 
          breadth: breadth,
          user_profile: getUserProfile()
        }),
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
                <strong>[${escapeHtml(c.id)}]</strong> ${escapeHtml(c.title)}<br>
                <span style="font-size: 0.78rem;">
                  <a href="javascript:void(0)" onclick="openEssenceModal('${escapeHtml(c.id)}')" style="color: var(--accent); font-weight: 600; text-decoration: underline; margin-right: 8px;">📖 View Summary / Essence</a>
                  <a href="${escapeHtml(c.sched_url)}" target="_blank" rel="noopener" style="color: var(--text-secondary); text-decoration: underline;">Official Sched ↗</a>
                </span>
              </div>
            `).join("")}
          </div>`;
        }

        const responseId = "resp_" + Math.random().toString(36).substring(2, 9);
        registerBotResponse(responseId, q, data.answer, data.citations);
        html += renderBotActionsHtml(responseId);
        botEl.innerHTML = html;
      } else if (res.status === 429) {
        botEl.innerHTML = `
          <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 12px; color: var(--text-primary); font-size: 0.85rem; line-height: 1.5;">
            <strong style="color: #ef4444;">⏳ Concurrency Queue Full (HTTP 429)</strong><br><br>
            ${escapeHtml(data.message || data.error || "The server is currently experiencing high concurrent traffic. Please wait a few seconds and try again.")}
          </div>
        `;
      } else if (res.status === 504) {
        botEl.innerHTML = `
          <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 12px; color: var(--text-primary); font-size: 0.85rem; line-height: 1.5;">
            <strong style="color: #ef4444;">⏱️ Request Timeout (HTTP 504)</strong><br><br>
            ${escapeHtml(data.message || data.error || "Inference request timed out after 45 seconds in queue/generation.")}
          </div>
        `;
      } else if (res.status === 503 || (data && (data.error === "cascade_unavailable" || data.error === "gateway_busy"))) {
        let citationsHtml = "";
        if (data.citations && data.citations.length > 0) {
          citationsHtml = `<div class="chat-citations" style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(234, 179, 8, 0.3); font-size: 0.8rem;">
            <strong>Relevant Presentations Matched by RAG:</strong><br>
            ${data.citations.map((c) => `
              <div style="margin-top: 4px;">
                <strong>[${escapeHtml(c.id)}]</strong> <a href="${escapeHtml(c.sched_url)}" target="_blank" rel="noopener" style="color: var(--accent); text-decoration: underline;">${escapeHtml(c.title)}</a>
              </div>
            `).join("")}
          </div>`;
        }
        botEl.innerHTML = `
          <div style="background: rgba(234, 179, 8, 0.12); border: 1px solid rgba(234, 179, 8, 0.35); border-radius: 8px; padding: 12px; color: var(--text-primary); font-size: 0.85rem; line-height: 1.5;">
            <strong style="color: #eab308; display: block; margin-bottom: 4px;">⚠️ Public Free Cloud Gateway Currently at Capacity</strong>
            All public free-tier models are currently busy or rate-limited.<br><br>
            <strong>To continue immediately without limits:</strong><br>
            • Connect local Ollama / LM Studio or your own free API key: <button class="btn-header" onclick="document.getElementById('btn-open-settings').click()" style="padding: 2px 8px; font-size: 0.78rem; margin: 2px 0;">⚙️ Open Settings</button><br>
            • Or query offline using our pre-indexed SQLite bundle.
            ${citationsHtml}
          </div>
        `;
      } else {
        botEl.innerHTML = `<div style="color: #f87171;">${escapeHtml(data.error || "Error retrieving response.")}</div>`;
      }
    } catch (err) {
      const botEl = document.getElementById(loadingId);
      botEl.innerHTML = `<div style="color: #f87171;">Connection error to /api/chat. Is serve.py running?</div>`;
    } finally {
      if (queuePollInterval) {
        clearInterval(queuePollInterval);
        queuePollInterval = null;
      }
      if (queueIndicator) {
        queueIndicator.style.display = "none";
        queueIndicator.textContent = "Queue: Ready";
      }
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });
}

function appendMsg(content, type, isHtml = false) {
  const chatMessages = document.getElementById("chat-messages");
  const id = "msg_" + Math.random().toString(36).substring(2, 9);
  const div = document.createElement("div");
  div.id = id;
  div.className = `chat-msg ${type}`;
  if (isHtml) {
    div.innerHTML = content;
  } else {
    div.textContent = content;
  }
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

// Global response store for copying and exporting assistant answers
window.BOT_RESPONSES = window.BOT_RESPONSES || {};
window.LATEST_BOT_RESPONSE = null;

function registerBotResponse(responseId, question, rawMarkdown, citations) {
  const resp = {
    id: responseId,
    question: question || "Conference Inquiry",
    answer: rawMarkdown || "",
    citations: citations || [],
    timestamp: new Date()
  };
  window.BOT_RESPONSES[responseId] = resp;
  window.LATEST_BOT_RESPONSE = resp;
  return resp;
}

function renderBotActionsHtml(responseId) {
  return `
    <div class="chat-msg-actions" data-response-id="${escapeHtml(responseId)}">
      <button type="button" class="chat-action-btn" onclick="copyResponseMarkdown('${escapeHtml(responseId)}', this)" title="Copy raw markdown to clipboard">
        <span>📋</span> <span class="action-text">Copy Markdown</span>
      </button>
      <button type="button" class="chat-action-btn" onclick="downloadResponseMarkdown('${escapeHtml(responseId)}')" title="Download response as Markdown file (.md)">
        <span>⬇️</span> <span>.md</span>
      </button>
      <button type="button" class="chat-action-btn" onclick="exportResponsePdf('${escapeHtml(responseId)}')" title="Save or print response as formatted PDF">
        <span>📄</span> <span>.pdf</span>
      </button>
    </div>
  `;
}

function copyResponseMarkdown(responseId, btn) {
  const resp = window.BOT_RESPONSES[responseId] || window.LATEST_BOT_RESPONSE;
  if (!resp || !resp.answer) return;

  const textToCopy = resp.answer;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(textToCopy).then(() => {
      showCopiedFeedback(btn);
    }).catch(() => fallbackCopy(textToCopy, btn));
  } else {
    fallbackCopy(textToCopy, btn);
  }
}

function fallbackCopy(text, btn) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand("copy");
    showCopiedFeedback(btn);
  } catch (e) {
    alert("Copy failed. Please select text manually.");
  }
  document.body.removeChild(ta);
}

function showCopiedFeedback(btn) {
  if (!btn) return;
  btn.classList.add("copied");
  const span = btn.querySelector(".action-text") || btn;
  const originalText = span.textContent;
  span.textContent = "✓ Copied!";
  setTimeout(() => {
    btn.classList.remove("copied");
    span.textContent = originalText;
  }, 2000);
}

function downloadResponseMarkdown(responseId) {
  const resp = window.BOT_RESPONSES[responseId] || window.LATEST_BOT_RESPONSE;
  if (!resp || !resp.answer) return;

  const dateStr = new Date(resp.timestamp).toISOString().split("T")[0];
  let md = `# AGNTCon + MCPCon Europe 2026 — Research Assistant Briefing\n\n`;
  md += `> **Query:** ${resp.question}\n`;
  md += `> **Date:** ${dateStr}\n`;
  md += `> **Source:** Unofficial Community Intelligence Hub (https://agntconmcpconeu26.sched.com/)\n\n`;
  md += `---\n\n`;
  md += `${resp.answer.trim()}\n\n`;

  if (resp.citations && resp.citations.length > 0) {
    md += `---\n\n### Referenced Presentations\n\n`;
    resp.citations.forEach(c => {
      md += `- **[${c.id}]** ${c.title} — [Official Sched](${c.sched_url})\n`;
    });
  }

  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const slug = resp.question.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "").slice(0, 30) || "response";
  a.href = url;
  a.download = `agntcon-briefing-${slug}-${dateStr}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function exportResponsePdf(responseId) {
  const resp = window.BOT_RESPONSES[responseId] || window.LATEST_BOT_RESPONSE;
  if (!resp || !resp.answer) return;

  const printable = document.getElementById("printable-dossier");
  if (!printable) {
    alert("Printable container not found in DOM.");
    return;
  }

  const dateStr = new Date(resp.timestamp).toLocaleDateString();
  const profile = getUserProfile();

  // Strip frontmatter if any
  const cleanMd = resp.answer.replace(/^---[\s\S]*?---\n*/, "");
  let formattedAnswerHtml = "";
  if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
    formattedAnswerHtml = DOMPurify.sanitize(marked.parse(cleanMd));
  } else {
    formattedAnswerHtml = `<div style="white-space: pre-wrap;">${escapeHtml(cleanMd)}</div>`;
  }

  let citationsHtml = "";
  if (resp.citations && resp.citations.length > 0) {
    citationsHtml = `
      <div class="print-briefing-citations">
        <h3 style="font-size: 12pt; margin-bottom: 8px;">Referenced Presentations</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 9.5pt;">
          <thead>
            <tr style="border-bottom: 2px solid #000;">
              <th style="text-align: left; padding: 4px;">ID</th>
              <th style="text-align: left; padding: 4px;">Presentation Title</th>
              <th style="text-align: left; padding: 4px;">Sched Link</th>
            </tr>
          </thead>
          <tbody>
            ${resp.citations.map(c => `
              <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 4px; font-weight: bold;">[${escapeHtml(c.id)}]</td>
                <td style="padding: 4px;">${escapeHtml(c.title.replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, ""))}</td>
                <td style="padding: 4px;"><a href="${escapeHtml(c.sched_url)}">${escapeHtml(c.sched_url)}</a></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  printable.innerHTML = `
    <div class="print-cover" style="padding-bottom: 15px; margin-bottom: 15px;">
      <h1>AGNTCon + MCPCon Europe 2026</h1>
      <div class="print-subtitle">Research Assistant Briefing Note</div>
      <p style="font-size: 9.5pt; color: #555; margin-top: 4px;"><strong>Generated:</strong> ${dateStr} • Unofficial Community Intelligence Hub</p>
      ${profile ? `
        <div style="margin-top: 10px; padding: 8px 12px; border: 1px solid #ddd; background: #f9f9f9; font-size: 9.5pt;">
          <strong>Attendee Profile:</strong> ${escapeHtml(profile.role || "Specialist")} | 
          <strong>Focus:</strong> ${escapeHtml((profile.focus_areas || []).join(", ") || "All")}
        </div>
      ` : ""}
    </div>

    <div class="print-briefing-q">
      <strong>User Query:</strong> ${escapeHtml(resp.question)}
    </div>

    <div class="print-briefing-a">
      ${formattedAnswerHtml}
    </div>

    ${citationsHtml}
  `;

  window.print();
}

function formatBotMarkdown(text) {
  if (!text) return "";

  // 1. Transform [[2RBBJ]] or [2RBBJ] into interactive essence links with single brackets [2RBBJ]
  let processed = text.replace(/\[\[([A-Za-z0-9_-]+)\]\]/g, (match, p1) => {
    return `<a href="javascript:void(0)" onclick="openEssenceModal('${p1}')" class="wikilink-chat" style="color: var(--accent); font-weight: 700; text-decoration: underline;" title="Open presentation summary">[${p1}]</a>`;
  });

  // Also match standalone [2RBBJ] (where 2RBBJ is a session ID) not followed by markdown link parens
  processed = processed.replace(/\[([A-Za-z0-9]{4,6})\](?!\s*[\(\[])/g, (match, p1) => {
    const isSession = ALL_TALKS.some(t => t.id.toLowerCase() === p1.toLowerCase());
    if (isSession) {
      return `<a href="javascript:void(0)" onclick="openEssenceModal('${p1}')" class="wikilink-chat" style="color: var(--accent); font-weight: 700; text-decoration: underline;" title="Open presentation summary">[${p1}]</a>`;
    }
    return match;
  });

  // 2. Use marked.js + DOMPurify (already loaded vendor libraries)
  if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
    const renderer = new marked.Renderer();
    renderer.link = function(href, title, text) {
      let h = typeof href === "object" ? href.href : href;
      let t = typeof href === "object" ? href.text : text;
      let tit = typeof href === "object" ? href.title : title;
      return `<a href="${h}" target="_blank" rel="noopener"${tit ? ` title="${tit}"` : ""}>${t} ↗</a>`;
    };

    const rawHtml = marked.parse(processed, { renderer: renderer, breaks: true, gfm: true });
    return DOMPurify.sanitize(rawHtml, {
      ADD_ATTR: ["target", "onclick", "class", "style"]
    });
  }

  // Safe fallback if vendor libraries are missing
  let out = escapeHtml(processed);
  out = out.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
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
        ALL_TALKS.map(t => `<option value="${t.id}" ${prefillSid === t.id ? 'selected' : ''}>[${t.id}] ${(t.title || '').replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, '').substring(0, 60)}...</option>`).join('');
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
  const btnOpenDisclaimerTop = document.getElementById("btn-open-disclaimer-top");
  if (btnOpenDisclaimerTop) btnOpenDisclaimerTop.addEventListener("click", openDisclaimer);
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

  const hideMixedContentWarning = () => {
    const warning = document.getElementById("https-mixed-content-warning");
    if (warning) warning.style.display = "none";
  };

  if (baseUrlInput) {
    baseUrlInput.addEventListener("input", hideMixedContentWarning);
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
      hideMixedContentWarning();
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

  // Forget Key button (Wipes all custom inputs and keys)
  const btnForgetKey = document.getElementById("btn-forget-key");
  if (btnForgetKey) {
    btnForgetKey.addEventListener("click", () => {
      if (apiKeyInput) apiKeyInput.value = "";
      if (baseUrlInput) baseUrlInput.value = "";
      if (modelNameInput) modelNameInput.value = "";
      if (providerSelect) providerSelect.value = "none";
      localStorage.removeItem("agntcon_custom_key");
      localStorage.removeItem("agntcon_custom_base_url");
      localStorage.removeItem("agntcon_custom_model_name");
      localStorage.removeItem("agntcon_custom_provider");
      btnForgetKey.textContent = "✓ Wiped All";
      setTimeout(() => (btnForgetKey.textContent = "🗑️ Forget Key"), 2000);
      updateChatEngineBadge();
    });
  }

  // Restore saved BYOM settings from localStorage if present
  if (apiKeyInput) {
    const savedKey = localStorage.getItem("agntcon_custom_key");
    if (savedKey) apiKeyInput.value = savedKey;
    apiKeyInput.addEventListener("change", (e) => {
      localStorage.setItem("agntcon_custom_key", e.target.value.trim());
    });
  }

  if (baseUrlInput) {
    const savedBaseUrl = localStorage.getItem("agntcon_custom_base_url");
    if (savedBaseUrl) baseUrlInput.value = savedBaseUrl;
    baseUrlInput.addEventListener("input", (e) => {
      localStorage.setItem("agntcon_custom_base_url", e.target.value.trim());
      hideMixedContentWarning();
    });
  }

  if (modelNameInput) {
    const savedModel = localStorage.getItem("agntcon_custom_model_name");
    if (savedModel) modelNameInput.value = savedModel;
    modelNameInput.addEventListener("input", (e) => {
      localStorage.setItem("agntcon_custom_model_name", e.target.value.trim());
      updateChatEngineBadge();
    });
  }

  // Provider presets: Unified Local LLM + Cloud APIs
  if (providerSelect) {
    const savedProvider = localStorage.getItem("agntcon_custom_provider");
    if (savedProvider) providerSelect.value = savedProvider;

    providerSelect.addEventListener("change", (e) => {
      const p = e.target.value;
      localStorage.setItem("agntcon_custom_provider", p);
      if (p === "local") {
        baseUrlInput.value = "http://127.0.0.1:1234/v1";
        modelNameInput.value = ""; // Clean blank! LM Studio uses active loaded model; Ollama user types model
      } else if (p === "nvidia") {
        baseUrlInput.value = "https://integrate.api.nvidia.com/v1";
        modelNameInput.value = "nvidia/llama-3.1-nemotron-70b-instruct";
      } else if (p === "openrouter") {
        baseUrlInput.value = "https://openrouter.ai/api/v1";
        modelNameInput.value = "meta-llama/llama-3.3-70b-instruct";
      } else if (p === "kilocode") {
        baseUrlInput.value = "https://api.kilo.ai/v1";
        modelNameInput.value = "kilo-auto/free";
      } else if (p === "none") {
        baseUrlInput.value = "";
        modelNameInput.value = "";
      }
      localStorage.setItem("agntcon_custom_base_url", baseUrlInput.value);
      localStorage.setItem("agntcon_custom_model_name", modelNameInput.value);
      hideMixedContentWarning();
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
      const rawBase = baseUrlInput ? baseUrlInput.value.trim() : "";
      const model = modelNameInput ? modelNameInput.value.trim() : "";
      const apiKey = apiKeyInput ? apiKeyInput.value.trim() : "";

      if (!rawBase) {
        testModelResult.style.color = "#f87171";
        testModelResult.textContent = "Error: Base URL cannot be empty.";
        return;
      }

      const probeUrl = normalizeChatCompletionsUrl(rawBase);
      testModelResult.style.color = "var(--text-secondary)";
      testModelResult.textContent = `Pinging ${probeUrl} (model: '${model || "default loaded"}')...`;
      const t0 = performance.now();

      try {
        const headers = { "Content-Type": "application/json" };
        if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;

        const payload = {
          messages: [{ role: "user", content: "ping" }],
          max_tokens: 10
        };
        if (model) payload.model = model;

        const res = await fetch(probeUrl, {
          method: "POST",
          headers: headers,
          body: JSON.stringify(payload)
        });

        const elapsed = Math.round(performance.now() - t0);
        if (res.ok) {
          hideMixedContentWarning();
          const data = await res.json();
          if (data.choices && data.choices.length > 0) {
            testModelResult.style.color = "#22c55e";
            testModelResult.textContent = `✓ Online & Validated LLM inference! TTFT: ${elapsed}ms (HTTP ${res.status})`;
          } else {
            testModelResult.style.color = "#eab308";
            testModelResult.textContent = `⚠️ Endpoint responded (${elapsed}ms), but missing choices[0].message. Verify model name or server format.`;
          }
        } else {
          const errText = await res.text().catch(() => "");
          testModelResult.style.color = "#f87171";
          testModelResult.textContent = `✕ Server responded HTTP ${res.status} (${elapsed}ms): ${errText.slice(0, 100)}`;
        }
      } catch (err) {
        const elapsed = Math.round(performance.now() - t0);
        testModelResult.style.color = "#f87171";
        testModelResult.textContent = `✕ Connection error (${elapsed}ms): Network/CORS failure. Verify CORS/server is running.`;
        if (window.location.protocol === "https:" && rawBase.startsWith("http://")) {
          const warning = document.getElementById("https-mixed-content-warning");
          if (warning) {
            warning.style.display = "block";
            warning.innerHTML = `
              <strong>💡 Local Model Connection Troubleshooting:</strong><br>
              • If using <strong>Safari</strong> or <strong>Firefox</strong>, browsers block <code>http://</code> from HTTPS pages.<br>
              • <strong>Quick Fix 1:</strong> Use <strong>Chrome</strong>, <strong>Brave</strong>, or <strong>Edge</strong> (which allow <code>http://127.0.0.1</code> natively).<br>
              • <strong>Quick Fix 2:</strong> Expose your local port via Cloudflare tunnel: <code>cloudflared tunnel --url http://127.0.0.1:1234</code>.<br>
              • <strong>Quick Fix 3:</strong> Ensure LM Studio / Ollama is running and CORS is enabled.
            `;
          }
        }
      }
    });
  }

  // Internal Traffic & Analytics Exclusion Toggle
  const toggleIgnoreAnalytics = document.getElementById("toggle-ignore-analytics");
  const analyticsExclusionStatus = document.getElementById("analytics-exclusion-status");

  const updateAnalyticsExclusionUI = () => {
    const isAdmin = !!localStorage.getItem("agntcon_admin_token");
    const isIgnored = localStorage.getItem("agntcon_ignore_telemetry") === "true";
    const dnt = (typeof navigator !== "undefined" && navigator.doNotTrack === "1") ||
                (typeof window !== "undefined" && window.doNotTrack === "1");

    if (toggleIgnoreAnalytics) {
      toggleIgnoreAnalytics.checked = isIgnored || isAdmin;
      if (isAdmin) {
        toggleIgnoreAnalytics.disabled = true;
      }
    }
    if (analyticsExclusionStatus) {
      if (isAdmin) {
        analyticsExclusionStatus.innerHTML = "🔒 <strong>Admin Session Active:</strong> Telemetry is permanently muted for this browser.";
        analyticsExclusionStatus.style.color = "#38bdf8";
      } else if (isIgnored) {
        analyticsExclusionStatus.innerHTML = "✓ <strong>Excluded:</strong> No beacons or usage events will be sent from this browser.";
        analyticsExclusionStatus.style.color = "#22c55e";
      } else if (dnt) {
        analyticsExclusionStatus.innerHTML = "ℹ️ <strong>Do Not Track Active:</strong> Respected by client. Telemetry muted.";
        analyticsExclusionStatus.style.color = "var(--text-secondary)";
      } else {
        analyticsExclusionStatus.innerHTML = "Standard mode: Anonymous Zero-PII engagement events enabled.";
        analyticsExclusionStatus.style.color = "var(--text-secondary)";
      }
    }
  };

  if (toggleIgnoreAnalytics) {
    updateAnalyticsExclusionUI();
    toggleIgnoreAnalytics.addEventListener("change", (e) => {
      if (e.target.checked) {
        localStorage.setItem("agntcon_ignore_telemetry", "true");
      } else {
        localStorage.removeItem("agntcon_ignore_telemetry");
      }
      updateAnalyticsExclusionUI();
    });
  }

  if (btnOpenSettings) {
    btnOpenSettings.addEventListener("click", () => {
      updateAnalyticsExclusionUI();
    });
  }

  // ── Community Contribution / Claim Session Logic (Sprint 13) ──────────────
  const urlParams = new URLSearchParams(window.location.search);
  const magicToken = urlParams.get("token");
  if (magicToken) {
    const parts = magicToken.split(".");
    if (parts.length === 3) {
      openContributeModal(parts[0], magicToken);
    }
  }

  const contribForm = document.getElementById("contribute-form");
  if (contribForm) {
    contribForm.addEventListener("submit", handleContributeSubmit);
  }

  const contribRole = document.getElementById("contrib-role");
  if (contribRole) {
    contribRole.addEventListener("change", (e) => {
      updateConsentText(e.target.value);
      updateSessionPickerVisibility();
    });
  }

  const contribPicker = document.getElementById("contrib-select-session");
  if (contribPicker) {
    contribPicker.addEventListener("change", (e) => {
      updateSelectedSessionPreview(e.target.value);
    });
  }
}

function updateConsentText(role) {
  const label = document.getElementById("contrib-license-label");
  if (!label) return;
  if (role === "organizer") {
    label.innerHTML = "I confirm that I am an authorized representative of the AGNTCon organizing committee, and these presentations were publicly presented and cleared for attendee distribution.";
  } else {
    label.innerHTML = "I confirm that I am the author or authorized co-presenter of this presentation. I grant AGNTCon Community Hub a non-exclusive, revocable, royalty-free license to host, display, index, and summarize this material for community search.";
  }
}

function updateSessionPickerVisibility() {
  const pickerWrap = document.getElementById("contrib-session-picker-wrap");
  const tokenInput = document.getElementById("contrib-input-token");
  const roleSelect = document.getElementById("contrib-role");
  if (!pickerWrap) return;

  const hasToken = !!(tokenInput && tokenInput.value.trim());
  const role = roleSelect ? roleSelect.value : "speaker";

  // Lock-In Precedence (CLA-3009-01):
  // When opened via ?token=***, session ID is hard-locked; dropdown is hidden.
  // Dropdown is active only without token or with role 'organizer'.
  if (hasToken) {
    pickerWrap.style.display = "none";
  } else {
    pickerWrap.style.display = "block";
  }
}

function populateContribSessionPicker(selectedId = "") {
  const picker = document.getElementById("contrib-select-session");
  if (!picker) return;

  const unattached = ALL_TALKS.filter((t) => !t.has_slides);
  const items = unattached.map((t) => {
    const cleanTitle = (t.title || "").replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
    const spk = (t.speakers || []).join(", ") || "Speaker";
    return {
      id: t.id,
      title: cleanTitle,
      speakers: spk,
      label: `[${t.id}] ${cleanTitle} — ${spk}`,
    };
  });

  items.sort((a, b) => a.label.localeCompare(b.label));

  picker.innerHTML = items
    .map((it) => `<option value="${escapeHtml(it.id)}">${escapeHtml(it.label)}</option>`)
    .join("");

  if (selectedId) {
    if (!Array.from(picker.options).some((o) => o.value === selectedId)) {
      const talk = ALL_TALKS.find((t) => t.id === selectedId);
      if (talk) {
        const cleanTitle = (talk.title || "").replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
        const spk = (talk.speakers || []).join(", ") || "Speaker";
        const opt = document.createElement("option");
        opt.value = selectedId;
        opt.textContent = `[${talk.id}] ${cleanTitle} — ${spk}`;
        picker.prepend(opt);
      }
    }
    picker.value = selectedId;
  }
}

function updateSelectedSessionPreview(sessionId) {
  if (!sessionId) return;
  const inputSid = document.getElementById("contrib-input-session-id");
  if (inputSid) inputSid.value = sessionId;

  const sessIdEl = document.getElementById("contrib-session-id");
  if (sessIdEl) sessIdEl.textContent = `Session [[${sessionId}]]`;

  const talk = ALL_TALKS.find((t) => t.id === sessionId);
  if (talk) {
    const cleanTitle = (talk.title || "").replace(/^(?:AGNTCon\s*\+\s*MCPCon(?:\s*Europe)?\s*2026\s*:\s*)/i, "").trim();
    const titleEl = document.getElementById("contrib-session-title");
    if (titleEl) titleEl.textContent = cleanTitle || "Session";
    const spkEl = document.getElementById("contrib-session-speakers");
    if (spkEl) spkEl.textContent = (talk.speakers || []).join(", ") || "Speaker";
  } else {
    fetch(`/api/contribute/session-info?session_id=${sessionId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) {
          const titleEl = document.getElementById("contrib-session-title");
          if (titleEl) titleEl.textContent = data.title || "Session";
          const spkEl = document.getElementById("contrib-session-speakers");
          if (spkEl) spkEl.textContent = (data.speakers || []).join(", ") || "Speaker";
        }
      })
      .catch(() => {});
  }
}

async function openContributeModal(sessionId = "", token = "") {
  const backdrop = document.getElementById("contribute-modal-backdrop");
  if (!backdrop) return;

  const tokenInput = document.getElementById("contrib-input-token");
  if (tokenInput) tokenInput.value = token || "";

  populateContribSessionPicker(sessionId);
  updateSessionPickerVisibility();

  const picker = document.getElementById("contrib-select-session");
  const effectiveSessionId = sessionId || (picker ? picker.value : "");

  const idInput = document.getElementById("contrib-input-session-id");
  if (idInput) idInput.value = effectiveSessionId;

  const roleSelect = document.getElementById("contrib-role");
  const role = roleSelect ? roleSelect.value : "speaker";
  updateConsentText(role);

  updateSelectedSessionPreview(effectiveSessionId);

  const statusMsg = document.getElementById("contrib-status-msg");
  if (statusMsg) statusMsg.style.display = "none";

  backdrop.classList.add("open");

  if (token && effectiveSessionId) {
    try {
      const res = await fetch(`/api/contribute/session-info?session_id=${effectiveSessionId}&token=${token}`);
      if (res.ok) {
        const data = await res.json();
        const titleEl = document.getElementById("contrib-session-title");
        if (titleEl) titleEl.textContent = data.title || "Session";
        const spkEl = document.getElementById("contrib-session-speakers");
        if (spkEl) spkEl.textContent = (data.speakers || []).join(", ") || "Speaker";
      }
    } catch (e) {
      // preview already updated from ALL_TALKS
    }
  }
}

function closeContributeModal() {
  const backdrop = document.getElementById("contribute-modal-backdrop");
  if (backdrop) backdrop.classList.remove("open");
}

async function handleContributeSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const submitBtn = document.getElementById("contrib-submit-btn");
  const statusMsg = document.getElementById("contrib-status-msg");

  const fileInput = document.getElementById("contrib-file");
  const urlInput = document.getElementById("contrib-url");
  const hasFile = fileInput.files && fileInput.files.length > 0;
  const hasUrl = !!urlInput.value.trim();

  if (!hasFile && !hasUrl) {
    statusMsg.style.display = "block";
    statusMsg.style.background = "rgba(239, 68, 68, 0.15)";
    statusMsg.style.color = "#f87171";
    statusMsg.style.border = "1px solid rgba(239, 68, 68, 0.3)";
    statusMsg.textContent = "Please either upload a PDF slide deck or provide a public presentation URL.";
    return;
  }

  const formData = new FormData(form);

  submitBtn.disabled = true;
  submitBtn.textContent = "⏳ Uploading & Screening...";
  statusMsg.style.display = "block";
  statusMsg.style.background = "rgba(56, 189, 248, 0.15)";
  statusMsg.style.color = "var(--accent)";
  statusMsg.style.border = "1px solid rgba(56, 189, 248, 0.3)";
  statusMsg.textContent = "Uploading presentation to secure quarantine and running security scrubber...";

  try {
    const res = await fetch("/api/contribute/upload", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (res.ok && data.status === "received") {
      statusMsg.style.background = "rgba(16, 185, 129, 0.15)";
      statusMsg.style.color = "#10b981";
      statusMsg.style.border = "1px solid rgba(16, 185, 129, 0.4)";
      statusMsg.innerHTML = `
        <div style="margin-bottom: 8px;">
          ✓ <strong>Received!</strong> Reference ID: <code>${escapeHtml(data.submission_id)}</code>.<br>
          Your presentation has been queued for verification. Thank you for contributing to AGNTCon!
        </div>
        <div style="margin-top: 8px;">
          <button type="button" id="btn-submit-another" class="btn-header" style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #10b981; font-weight: 600; padding: 6px 14px; font-size: 0.82rem; cursor: pointer; border-radius: 4px;">
            + Submit Another Presentation
          </button>
        </div>
      `;
      submitBtn.textContent = "✓ Uploaded";

      const btnAnother = document.getElementById("btn-submit-another");
      if (btnAnother) {
        btnAnother.addEventListener("click", () => {
          if (fileInput) fileInput.value = "";
          if (urlInput) urlInput.value = "";
          const licenseCheck = document.getElementById("contrib-license");
          if (licenseCheck) licenseCheck.checked = false;

          statusMsg.style.display = "none";
          submitBtn.disabled = false;
          submitBtn.textContent = "🚀 Submit for Indexing";

          populateContribSessionPicker();
          const pickerEl = document.getElementById("contrib-select-session");
          if (pickerEl && pickerEl.options.length > 0) {
            updateSelectedSessionPreview(pickerEl.value);
          }
          updateMissingSlidesCount();
        });
      }
    } else {
      statusMsg.style.background = "rgba(239, 68, 68, 0.15)";
      statusMsg.style.color = "#f87171";
      statusMsg.style.border = "1px solid rgba(239, 68, 68, 0.3)";
      statusMsg.textContent = `Upload failed: ${data.error || "Unknown server error"}`;
      submitBtn.disabled = false;
      submitBtn.textContent = "🚀 Submit for Indexing";
    }
  } catch (err) {
    statusMsg.style.background = "rgba(239, 68, 68, 0.15)";
    statusMsg.style.color = "#f87171";
    statusMsg.style.border = "1px solid rgba(239, 68, 68, 0.3)";
    statusMsg.textContent = `Network error: ${err.message}`;
    submitBtn.disabled = false;
    submitBtn.textContent = "🚀 Submit for Indexing";
  }
}
