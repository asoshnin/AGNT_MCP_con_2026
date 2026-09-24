# Sprint 04 — Baseline Diagnostic & Audit: FTS5 Lexical Gap and Modal Navigation State

**Sprint Identifier:** `Sprint_04_Hybrid_RAG_And_UX`  
**Archetype:** Archetype 3 (Refactoring & Hardening)  
**Parent Contract:** `pipe-final-sprint-hybrid-rag-and-ux-v1`  
**Status:** Approved  

---

## 1. Problem Statement & Baseline Symptoms

### 1.1 FTS5 Lexical Disconnect on Compound Domain Terms
* **Symptom:** Querying `"what's your takeaway on redteaming?"` (compound word) returned 0 hits for talk `[2RBBJ]` (*"AGNTCon + MCPCon Europe 2026: Infrastructure Red Teaming With Ablitera..."*).
* **Root Cause:** Standard SQLite FTS5 tokenizer splits text by whitespace. The token `redteaming` (10 chars) does not match discrete tokens `red` and `teaming`.
* **Consequence:** FTS5 fell back to secondary query tokens, retrieving irrelevant security talks. The system prompt's rigid negative guardrail (*"state: This topic was not covered..."*) forced the cloud model to falsely claim red teaming was not covered at the conference.
* **Contrast:** Querying `"what's your takeaway on red teaming?"` (with space) matched `[2RBBJ]` directly.

### 1.2 Modal Link Navigation & Chat History Eviction
* **Symptom:** Clicking `Canonical Presentation on Sched` inside the session essence modal navigated the current tab to `agntconmcpconeu26.sched.com`.
* **Root Cause:** `marked.parse()` generates `<a href="...">` tags without `target="_blank"`.
* **Consequence:** When the user clicked the browser Back button (`<-`), the single-page application reloaded, completely destroying the in-memory chat history in `#chat-messages`.

---

## 2. Baseline Code Locations & Coupling

1. `02_public_hub/mcp_server.py`:
   * `tool_search_talks()` performs direct FTS5 `MATCH` without morphological or compound decomposition.
   * `system_prompt` rule #3 contains binary refusal guardrail.
2. `02_public_hub/serve.py`:
   * `/api/search` queries SQLite FTS5 directly without token splitting.
3. `02_public_hub/site/assets/app.js`:
   * `openEssenceModal()` renders Markdown into `modalBody` without enforcing `target="_blank"` on outbound links.
   * `setupChat()` stores message elements solely in the live DOM without `sessionStorage` synchronization.
