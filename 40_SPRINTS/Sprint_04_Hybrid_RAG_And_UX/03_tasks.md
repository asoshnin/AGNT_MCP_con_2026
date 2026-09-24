# Tasks: Sprint 04 — Corpus-Driven Hybrid RAG & UX Persistence

**Target Branch:** `main`  
**Status:** In Progress (0/5 completed)  
**Parent Contract:** `pipe-final-sprint-hybrid-rag-and-ux-v1`  

---

## Phase 1: Core Engine Refactoring
- [ ] Task 1.1: Implement Corpus-Driven Dynamic Segmentation in `mcp_server.py` & `serve.py` <!-- status: pending -->
  - **Locus:** `02_public_hub/mcp_server.py`, `02_public_hub/serve.py`
  - **DoD:** `CONFERENCE_VOCAB` loaded on startup; `segment_compound_query()` dynamically decomposes words like `redteaming`, expanding FTS5 queries.
  - **Verification:** `python3 -c "from mcp_server import tool_search_talks; assert any(t['id'] == '2RBBJ' for t in tool_search_talks('redteaming'))"` (Exit 0).

- [ ] Task 1.2: Soften System Prompt Rule #3 in `mcp_server.py` <!-- status: pending -->
  - **Locus:** `02_public_hub/mcp_server.py`
  - **DoD:** Binary refusal replaced with conceptual and architectural equivalence instruction.
  - **Verification:** Inspection of `system_prompt` in `mcp_server.py`.

## Phase 2: Frontend UX Hardening
- [ ] Task 2.1: Enforce `target="_blank" rel="noopener noreferrer"` on Modal Markdown Links <!-- status: pending -->
  - **Locus:** `02_public_hub/site/assets/app.js`
  - **DoD:** All external links inside `openEssenceModal` automatically open in new tabs.
  - **Verification:** DOM inspection verifies `target="_blank"` on rendered Sched anchor tags.

- [ ] Task 2.2: Implement `sessionStorage` Chat Persistence with Circular Buffer <!-- status: pending -->
  - **Locus:** `02_public_hub/site/assets/app.js`
  - **DoD:** Chat messages saved to `agntcon_chat_history_v2`; reloaded upon reopening chat or navigating back; `🔄 New` button resets storage.
  - **Verification:** Automated unit test verifies serialization and reload logic.

## Phase 3: Documentation & Production Sync
- [ ] Task 3.1: Reflect Hybrid RAG & UX Improvements in `README.md` <!-- status: pending -->
  - **Locus:** `02_public_hub/README.md`, `README.md`
  - **DoD:** Document Corpus-Driven Dynamic Word Segmentation, Softened RAG Guardrails, and Session Persistence.
  - **Verification:** Markdown diff audit.
