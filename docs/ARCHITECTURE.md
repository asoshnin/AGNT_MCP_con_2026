# 🏛️ Architecture & System Design
**Project:** AGNTCon + MCPCon Europe 2026 Community Intelligence Hub  
**Specification Level:** Production Open-Source Showcase  
**Live Portal:** [https://agntcon-demo.vwoosh.com](https://agntcon-demo.vwoosh.com)

---

## 1. System Overview

The **AGNTCon + MCPCon Europe 2026 Intelligence Hub** is an open-source, zero-cost knowledge engine designed for software engineers and autonomous AI agents (OpenClaw, Cursor, Claude Code, Windsurf) to search, query, and analyze conference architectures.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PUBLIC INTERNET                                      │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ HTTPS (Encrypted Outbound Tunnel)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CLOUDFLARE GLOBAL EDGE                                    │
│                    SSL Termination • DDoS Mitigation • WAF Shield                      │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼ (cloudflared connector)
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         HOST COMPUTE (Oracle VM / Container)                           │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                      LIGHTWEIGHT PYTHON HTTP SERVER                            │   │
│   │                         (serve.py • Port 8088)                                 │   │
│   │                                                                                │   │
│   │   ├── REST API: /api/search • /api/page • /api/chat • /api/health              │   │
│   │   ├── Admin & CRM: /api/admin/submissions • /api/admin/inquiries               │   │
│   │   └── Static Web App: site/index.html (Vanilla JS + CSS, zero node_modules)    │   │
│   └───────────────┬──────────────────────────────────────────┬─────────────────────┘   │
│                   │                                          │                         │
│                   ▼                                          ▼                         │
│   ┌───────────────────────────────┐          ┌─────────────────────────────────────┐   │
│   │      MCP KNOWLEDGE ENGINE     │          │    BACKGROUND SYNTHESIS PIPELINE    │   │
│   │        (mcp_server.py)        │          │       (essence_pipeline.py)         │   │
│   │                               │          │                                     │   │
│   │   • Two-Tier Adaptive RAG     │          │   • Stratified Slide Stride Sample  │   │
│   │   • Entity-First Boosting     │          │   • v2.2 Metaprompt Synthesis       │   │
│   │   • Stop-Word Filtering       │          │   • Failure Modes & Benchmark Extr. │   │
│   │   • Sched Outbound Linking    │          │   • Non-Blocking Daemon Worker      │   │
│   └───────────────┬───────────────┘          └─────────────────┬───────────────────┘   │
│                   │                                            │                       │
│                   ▼                                            ▼                       │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                          LOCAL STORAGE & DATA LAYER                            │   │
│   │                                                                                │   │
│   │   ├── SQLite FTS5 Full-Text Index (wiki/agntcon2026.sqlite)                    │   │
│   │   ├── Karpathy-Style Markdown Archive (wiki/sources/*.md)                      │   │
│   │   ├── Presentation Slide Decks (site/assets/slides/*.pdf)                      │   │
│   │   └── Submissions & CRM State (data/submissions.sqlite, data/crm.sqlite)       │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ Outbound API Calls (Zero Key Leakage)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          MULTI-GATEWAY FREE LLM CASCADE                                │
│   Tier 1: OpenRouter (openrouter/free) ➔ Tier 2: Kilocode ➔ Tier 3: NVIDIA NIM         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 The Two-Tier Adaptive RAG Engine (`mcp_server.py`)
The search and reasoning engine is calibrated for sub-second retrieval and strict factual grounding:
1. **Entity-First Ranking:**
   - Exact Session ID match (`2RB8Y`): **$+50$ points**.
   - Full Speaker Name match in query (`"Dylan Ratcliffe"`): **$+30$ points**.
   - Partial Name match: **$+15$ points**.
   - Filtered Content Tokens in Title: **$+8$ points**.
   - Body/Summary Match: **$+2$ points**.
2. **Conversational Stop-Word Elimination:**
   Natural question preambles (*«what is the takeaway from...»*, *«tell me about...»*) are filtered via `QUERY_STOP_WORDS`, preventing common prepositions (*from*, *your*, *what*) from skewing results toward unrelated sessions.
3. **Adaptive Context Sizing:**
   - Point queries ($k \le 3$): Injects complete Karpathy Markdown source essences (`wiki/sources/{id}.md`).
   - Broad landscape surveys ($k > 3$): Injects compressed one-paragraph digests to preserve the model context window.

### 2.2 Model Context Protocol (MCP) Tools
The server exposes 3 standard MCP primitives over stdio and HTTP:
* **`search_talks(query, topic, only_with_slides, limit)`**: Search session metadata, speakers, and topics with relevance ranking.
* **`get_page(page_type, name_or_id)`**: Retrieve full markdown source essences (`page_type="source"`) or cross-cutting concept syntheses (`page_type="concept"`).
* **`answer_conference(question, breadth, only_with_slides, user_context)`**: Execute end-to-end RAG reasoning with canonical Sched citations.

### 2.3 Automated Essence Synthesis Pipeline (`essence_pipeline.py`)
When a speaker uploads a slide deck via the crowdsourcing portal and an administrator approves it:
1. **Immediate Response:** Approval, file promotion, and basic indexing execute in $< 50$ ms.
2. **Asynchronous Synthesis:** A detached background daemon thread invokes `essence_pipeline.py`:
   - Extracts all pages using `pypdf`.
   - Performs **stratified stride sampling** (capturing intro context, 8 evenly distributed architecture slides from the middle deck, and conclusions) to eliminate *middle-deck amnesia*.
   - Evaluates the deck using the **v2.2 Metaprompt** through the free LLM cascade.
   - Generates a verified Markdown essence containing:
     - `## Essence` (300–450 words with concrete architectural decisions).
     - `## Key Takeaways & Recommendations` (actionable engineering practices).
     - `## Production Gotchas & Failure Modes` (edge cases, vulnerabilities, and real-world gotchas).
     - `## Discovered Resources` (verified links only).
   - Re-indexes the session into `wiki/index.json` and SQLite FTS5.

---

## 3. Security & Isolation Architecture

| Layer | Security Control | Purpose |
| :--- | :--- | :--- |
| **Network Perimeter** | Outbound Cloudflare Tunnel (`cloudflared`) | **Zero open inbound ports**; eliminates brute-force and port-scan attack surface. |
| **Application Layer** | 500-char input clamping & IP rate limiter | Prevents payload inflation and DoS attacks on inference endpoints. |
| **Data Boundary** | Untrusted Data Fencing in Metaprompt | Instructs the LLM to treat all slide text strictly as data, neutralizing prompt injection attacks from external PDFs. |
| **Worker Isolation** | PDF extraction subprocess | Runs PDF parsing in a detached subprocess to isolate parent server memory from malformed PDF exploits. |
| **Privacy Air-Gap** | Local SQLite CRM & Submissions DB | Lead emails and inquiries reside locally on disk and are **strictly excluded from Git tracking**. |

---

## 4. Zero-Cost Infrastructure Invariant

The entire platform operates on **100% free and open-source tiers**:
* **Hosting:** Oracle Cloud Infrastructure (OCI) Ampere A1 (Always Free, 4 OCPU, 24 GB RAM, 200 GB SSD).
* **Routing & SSL:** Cloudflare Free Plan.
* **Inference:** Multi-gateway free cascade (`openrouter/free`, `kilo-auto/free`, `nvidia/nim`) with automated circuit breakers and fallbacks.
