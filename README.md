# AGNTCon + MCPCon Europe 2026 — Intelligence Hub & Native MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
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
│        wiki/sources/*.md  │  wiki/concepts/*.md  │  crm.sqlite (Inquiries)  │
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

## 🧪 Testing & Quality Gates

Run the automated test suite and linter:

```bash
# Run 21 deterministic unit & integration tests
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
