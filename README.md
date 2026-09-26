# AGNTCon + MCPCon Europe 2026 — Intelligence Hub & Native MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI Quality Gate](https://github.com/asoshnin/AGNT_MCP_con_2026/actions/workflows/ci.yml/badge.svg)](https://github.com/asoshnin/AGNT_MCP_con_2026/actions)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-agntcon--demo.vwoosh.com-emerald.svg)](https://agntcon-demo.vwoosh.com)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![MCP Standard](https://img.shields.io/badge/MCP-2024--11--05-brightgreen.svg)](https://modelcontextprotocol.io/)
[![SQLite FTS5](https://img.shields.io/badge/SQLite-FTS5%20%2B%20Vector-orange.svg)](https://www.sqlite.org/)
[![Zero-Server PII](https://img.shields.io/badge/Privacy-100%25%20Client%20Local-success.svg)](#)
[![100% Free Inference](https://img.shields.io/badge/Inference-100%25%20Free%20Cascade-blueviolet.svg)](#)

An independent, fair-use research wiki, interactive AI assistant, and Model Context Protocol (MCP) server for **AGNTCon + MCPCon Europe 2026** (17–18 September 2026, RAI Amsterdam).

> **Academic & Community Fair-Use Notice:**  
> This is an unofficial, independent open-source research and intelligence project. Original conference presentations, schedules, and materials are copyright © **The Linux Foundation / Agentic AI Foundation** and their respective speakers. This repository contains original analytical syntheses, verified open-source tool repositories, and outbound links to official [Sched presentation pages](https://agntconmcpconeu26.sched.com/). No speaker slides are reproduced or hosted.

---

## 🏛️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HARVESTER & EXTRACTION PIPELINE                       │
│  [Sched Web Scraper] ──> [PDF Magic-Byte Validator] ──> [Karpathy Synthesizer]
│                                                                │
│                                                     [GroundingCritic Gate]
│                                                                ▼
└──────────────────────────────────────────────────────────────┬──────────────┘
                                                               │
                                                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HIGH-PERFORMANCE DATA & INDEX LAYER                      │
│        wiki/index.json  │  agntcon2026.sqlite (FTS5 BM25 + BGE Embeddings)   │
│        wiki/sources/*.md  │  crm.sqlite (Inquiries)  │ analytics.sqlite     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 UNIFIED GATEWAY & MCP SERVER (serve.py)                     │
│  ┌───────────────────────────────┐     ┌──────────────────────────────────┐ │
│  │   Active Concurrency Queue    │     │      8 Native MCP Tools          │ │
│  │   (asyncio.Semaphore(2))      │     │  search_talks   │ get_page       │ │
│  │   45s lease timeout           │     │  answer_conf    │ get_talk       │ │
│  │   Telemetry /api/queue-status │     │  list_talks     │ list_concepts  │ │
│  └──────────────┬────────────────┘     │  get_conf_prof  │ get_queue_stat │ │
│                 │                      └─────────────────┬────────────────┘ │
└─────────────────┼────────────────────────────────────────┼──────────────────┘
                  ▼                                        ▼
┌──────────────────────────────────┐     ┌──────────────────────────────────┐
│        WEB CLIENT (app.js)       │     │       AGENT / IDE CLIENTS        │
│  • #chat-queue-indicator live UX │     │  • Cursor (.cursor/mcp.json)     │
│  • Obsidian 2nd-Brain JSZip      │     │  • Claude Desktop (mcp.json)     │
│  • Client-Side BYOM (Ollama/LM)  │     │  • OpenClaw Gateway Agent        │
└──────────────────────────────────┘     └──────────────────────────────────┘
```

---

## 🚀 Quick Start (Local Setup in 30 Seconds)

### Option A: Using `uv` (Recommended)
```bash
git clone https://github.com/asoshnin/AGNT_MCP_con_2026.git
cd AGNT_MCP_con_2026
uv venv
uv pip install -r requirements.txt
uv run python serve.py
```

### Option B: Using standard Python `venv`
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python serve.py --port 8080
```

Open **`http://localhost:8080`** in your browser.

---

## 🤖 Model Context Protocol (MCP) Server Setup

This repository provides a standard JSON-RPC 2.0 stdio MCP server exposing **8 deterministic tools** for agentic systems:

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `search_talks` | `query`, `topic`, `only_with_slides`, `limit` | Hybrid lexical BM25 + dense vector search over all 113 conference sessions. |
| `get_page` | `page_type` (`source` \| `concept`), `name_or_id` | Retrieves full Karpathy source essence markdown or architectural concept synthesis. |
| `answer_conference` | `question`, `breadth`, `only_with_slides`, `user_context` | Two-Tier Adaptive RAG grounded strictly in conference sessions with canonical citations. |
| `get_talk` | `talk_id` | Structured talk metadata: speakers, official Sched URL, tags, and summary. |
| `list_talks` | `limit`, `offset`, `only_with_slides` | Paginated catalog enumeration with slide availability filter. |
| `list_concepts` | _(none)_ | Lists all 10 cross-cutting architectural concept documents. |
| `get_conference_profile` | _(none)_ | High-level conference tracks, themes, attendee distribution, and branding tokens. |
| `get_queue_status` | _(none)_ | Live server inference concurrency telemetry and active queue depth. |

### 1. Claude Desktop Setup
Add the following snippet to your `claude_desktop_config.json`:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "agntcon-2026": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/02_public_hub/mcp_server.py"]
    }
  }
}
```

### 2. Cursor IDE Setup
Add to `.cursor/mcp.json` in your workspace root:

```json
{
  "mcpServers": {
    "agntcon-2026": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
```

### 3. OpenClaw Setup
Add to your `openclaw.json` under `plugins.mcp.servers`:

```json
{
  "agntcon": {
    "command": "python",
    "args": ["/absolute/path/to/02_public_hub/mcp_server.py"]
  }
}
```

---

## 🛡️ Active Concurrency Queue & Zero-Cost Failover (Sprint P-04e)

The cloud gateway shields upstream community inference endpoints through an active FIFO queue:
- **Bounded Concurrency**: `MAX_CONCURRENT_CHATS = 2` simultaneous tasks with `asyncio.Semaphore(2)`.
- **45-Second Lease Timeout**: Requests exceeding 45 seconds return `HTTP 504 Gateway Timeout`.
- **Capacity Gate**: If waiting queue exceeds 10 requests, immediate `HTTP 429` with `Retry-After: 15`.
- **Live UI Telemetry**: Client polls `/api/queue-status` every 2s, rendering live queue positioning (`Position in queue: #1 (estimated wait: ~3s)...`).
- **Free Gateway Cascade**: Primary `openrouter/free` ➔ Secondary Kilocode / NVIDIA NIM free tiers ➔ Honest `HTTP 503` capacity notice if all are saturated.
- **Strict Zero Financial Harm**: Never falls back to billable personal API keys.

---

## 🛠️ Bring Your Own Model (BYOM) / Local Offline Setup

Visitors who prefer 100% offline, zero-telemetry local inference can configure local models directly in the web UI Settings drawer:

### Local LM Studio
1. Launch **LM Studio** and load any instruction-tuned model.
2. Start the Local Inference Server on port `1234` with CORS enabled.
3. In Hub Settings, select **Local Ollama / LM Studio** (`http://127.0.0.1:1234/v1`).

### Local Ollama
1. Start Ollama with browser origin access:
   ```bash
   OLLAMA_ORIGINS="*" ollama serve
   ```
2. Pull a recommended model:
   - **Standard Laptop (8–16 GB RAM)**: `ollama pull qwen2.5:7b-instruct` or `ollama pull llama3.1:8b`
   - **Lightweight (4–8 GB RAM)**: `ollama pull llama3.2:3b-instruct`
   - **High-End / GPU (16+ GB VRAM)**: `ollama pull qwen2.5:14b-instruct` or `ollama pull deepseek-r1:14b`
3. In Hub Settings, set Base URL to `http://127.0.0.1:11434/v1`.

*Note: All BYOM queries run strictly browser-to-model via `window.fetch()`. Custom keys and prompts are never sent to or logged by the server.*

---

## 🧠 Obsidian Second-Brain Export

Download pre-formatted markdown notes tailored for [Obsidian](https://obsidian.md/):
1. Click **📦 My Track** in the header.
2. Select desired talks or click **Select All (113 Talks)**.
3. Click **Download Obsidian Vault (.zip)**.
4. Client-side `JSZip` packages the notes with complete YAML frontmatter, tags, and bi-directional `[[wikilinks]]` with zero server computation.

---

## 🔍 Corpus-Driven Dynamic Word Segmentation & RAG Resilience

To bridge lexical gaps in conference queries without brittle hardcoded dictionaries or slow LLM rewrite latency:
- **Corpus-Driven Dynamic Segmentation:** Extracts the canonical domain vocabulary (2,257 unique terms) directly from the conference database at startup. Any compound query word (e.g. `redteaming`, `promptinjection`, `agenticworkflow`) is dynamically decomposed in $O(N)$ time into constituent terms (`['red', 'teaming']`), automatically expanding the FTS5 search to `(term OR "left right" OR (left AND right))`.
- **Softened RAG Guardrails:** Replaced rigid binary refusals with architectural equivalence reasoning. If an exact term is not named in excerpts, the assistant analyzes related security, evaluation, and orchestration patterns (e.g. boundary enforcement, vulnerability remediation), preserving grounded citations.
- **Client-Side Session Persistence:** Chat conversations persist across tab switches, link clicks, and back-navigation in `sessionStorage` (40-turn circular buffer, 100% private to the client).
- **Outbound Link Sandboxing:** All external Sched, GitHub, and slide links in modals enforce `target="_blank" rel="noopener noreferrer"`.

---

## 📊 Zero-PII Engagement Analytics & Operator Console

The platform provides privacy-preserving engagement telemetry for operators and maintainers to measure real community adoption without third-party tracking cookies:

- **Anonymous Event Ingestion:** `POST /api/telemetry` logs client-side high-intent actions (`page_view`, `search`, `talk_opened`, `track_curate`, `track_export_obsidian`, `track_export_pdf`, `chat_query`) with non-blocking beacons (`navigator.sendBeacon`).
- **Zero-PII Storage:** Stored in `data/analytics.sqlite` (SQLite WAL mode). Raw IP addresses are **never stored**; visitor deduplication uses daily-salted, non-reversible SHA-256 hashes (`hash(IP + daily_salt)[:12]`).
- **Edge Geodistribution:** Country metrics are derived automatically from Cloudflare Edge request headers (`CF-IPCountry`).
- **Cloudflare GraphQL Edge Sync:** Live integration querying Cloudflare's GraphQL API (`CLOUDFLARE_ANALYTICS_TOKEN` & `CLOUDFLARE_ZONE_ID`) with in-memory caching to monitor 7-day zone requests, pageviews, bandwidth, and cache ratios.
- **4-Tier Tester Exclusion:** Automatic client-side muting when logged into `/admin`, opt-out magic link (`?internal=1`), settings toggle, and server IP denylist (`ANALYTICS_IGNORE_IPS`).
- **Operator Dashboard:** Accessible at `/admin` (password-protected) with conversion funnels, top clicked talks, top searched keywords, and top AI assistant queries with BYOM inference tier breakdowns.

---

## 🖥️ Server Infrastructure Observability & Telegram Watchdog

To maintain permanent, zero-cost operations on Oracle Cloud Infrastructure (OCI Always Free) with zero manual SSH maintenance:

- **Autonomous Out-of-Band Watchdog (`scripts/watchdog.py`):** Runs independently via systemd timer or cron every 5 minutes to inspect:
  - Local HTTP availability (`/api/health` 200 OK ping).
  - Cloudflare Zero Trust Edge Tunnel status (`cloudflared.service`).
  - Host RAM available vs total from `/proc/meminfo` (alerts at $\ge 90\%$ utilization).
  - NVMe disk space via `shutil.disk_usage` (alerts at $\ge 85\%$ utilization).
  - Host CPU load averages (1m, 5m, 15m) and zombie/defunct sub-workers (`stat == 'Z'`).
  - Rolling 7-day snapshot history stored in `data/infra_history.sqlite` ($\le 350$ KB).
- **Out-of-Band Telegram Alerting Gateway (`ToyProjectsBot`):**
  - Sends instant, actionable Markdown alerts to the maintainer's Telegram for P0 critical failures (tunnel down, web server unreachable) or P1 warnings (disk $\ge 85\%$, RAM $\ge 90\%$).
  - **Token-Bucket Anti-Spam Cooldown:** Maximum 1 alert per 30 minutes for persistent conditions.
  - **Automated Recovery Notice:** Dispatches an immediate `🟢 Incident Resolved` notification when failed services recover.
- **Oracle Cloud Always Free & Anti-Reclamation Guard (`scripts/anti_reclamation_worker.py`):**
  - Monitors the 7-day 95th-percentile compute metrics against Oracle's 20% idle reclamation threshold.
  - Respects Pay-As-You-Go (`OCI_PAYG_PROTECTED=true`) status, which officially provides 100% exemption from idle reclamation.
  - For standard Free Tier accounts, executes a gentle, low-priority (`nice -n 19`) off-peak maintenance task (03:30 UTC) to ensure the instance is never reclaimed by automated OCI reapers.
- **Operator Health Console (`/admin`):**
  - Dedicated **🖥️ Server Health** tab with live CPU, RAM, Disk, and Host Uptime dials.
  - Real-time service status badges for `agntcon-hub` and `cloudflared`.
  - Sanitized, read-only Linux `/proc` Process Inspector with zero secret exposure.
  - 1-click **`[🔔 Test Telegram]`** button to verify out-of-band alerting connectivity.

---

## 🌟 Community Crowdsourcing & Slide Contribution Pipeline

To solve the classic post-conference challenge of missing slide decks, the platform features a complete crowdsourced ingestion and verification pipeline:

- **1-Click Contribution Modal (`[ + Add Slides ]`):** Presenters and organizing committee representatives can upload missing presentations directly via the web UI.
- **Dual Contributor Roles:**
  - **Presenter Mode:** Automatically binds to the active session, claims speaker authorship, and records the presenter's contact info.
  - **Organizer / Committee Mode:** Exposes a full session search/picker across all missing presentations with tailored open-access archiving legal consent.
- **Automated AI Safety & Authenticity Gate:**
  - **PyMuPDF Validation:** Verifies PDF magic bytes, structure, slide count, and extracts raw text.
  - **LLM Authenticity Matcher:** Evaluates whether the uploaded deck matches the official Sched session abstract, assigning a 0–100% confidence score.
  - **Quarantine Storage:** Unverified uploads are placed in `quarantine/` with cryptographically randomized tokens.
- **Operator Moderation Queue (`/admin`):**
  - Instant inspection of submissions, slide preview, AI score, and submitter credentials.
  - 1-click **`[✓ Approve & Publish]`** automatically moves the PDF to `site/assets/slides/{session_id}.pdf`, updates `wiki/index.json`, and triggers zero-reboot incremental RAG re-indexing in 0.02s!

---

## 💬 Private Community Feedback System

Visitors and attendees can submit suggestions, report bugs, or propose agent tools via the dedicated **`[ 💬 Feedback ]`** modal:
- **Zero Public Spam:** All feedback is strictly private — no public comment sections or troll vectors.
- **Real-Time Push Alerts:** Instantly routes to the project maintainer's Telegram bot and dispatches an HTML alert email to `alex@vwoosh.com`.
- **CRM Integration:** Stored in `data/crm.sqlite` and visible under the **Inquiries** tab in the `/admin` console.
- **Honeypot Anti-Bot Shield:** Automatically filters automated spam without CAPTCHA friction.

---

## 🔄 Sched Incremental Re-Scanner

The platform includes an automated delta scanner for official Sched presentations:
- **CLI Command:** `python scripts/rescan_sched_slides.py` compares the live Sched event pages against local storage.
- **Admin Trigger:** 1-click `[🔄 Re-scan Sched for New Slides]` button in `/admin` to ingest newly posted official slides without server restarts.

---

## 🧪 Testing & Quality Gates

Run the automated test suite and linter:

```bash
# Run 126 deterministic unit & integration tests (100% green)
pytest tests/ -v

# Run Ruff linter
ruff check .

# Run AST secrets & credential leak audit
python ../scripts/audit_secrets.py

# Run Concurrency burst harness (4 concurrent requests)
python ../scripts/test_queue_concurrency.py
```

---

## ⚖️ Open-Source Governance & License

- **Source Code**: Released under the permissive [MIT License](LICENSE).
- **Contributing**: Please review [CONTRIBUTING.md](CONTRIBUTING.md) before submitting pull requests.
- **Security & Responsible Disclosure**: See [SECURITY.md](SECURITY.md).
- **Conference Attribution**: Organized by [The Linux Foundation](https://www.linuxfoundation.org/) and the [Agentic AI Foundation](https://agentic-ai-foundation.org/).
- **Engineered by**: [vwoosh.com](https://vwoosh.com).
