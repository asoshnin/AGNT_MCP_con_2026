# PI Agent Execution Prompt: Sprint 04 — Corpus-Driven Hybrid RAG & UX Persistence

```markdown
You are the autonomous PI Agent executing Sprint 04 for AGNTCon + MCPCon Europe 2026.

## Objective
Implement zero-hardcoding corpus-driven compound word segmentation in SQLite FTS5 search, soften the negative system prompt guardrail, enforce target="_blank" on external modal links, and implement sessionStorage chat history persistence.

## Mandatory Context to Read
1. Read `@02_public_hub/40_SPRINTS/Sprint_04_Hybrid_RAG_And_UX/01_baseline_audit.md`
2. Read `@02_public_hub/40_SPRINTS/Sprint_04_Hybrid_RAG_And_UX/02_target_architecture_delta.md`
3. Read `@02_public_hub/40_SPRINTS/Sprint_04_Hybrid_RAG_And_UX/03_tasks.md`

## Invariants to Uphold
1. Zero Hardcoding: The vocabulary MUST be dynamically extracted from `agntcon2026.sqlite` at startup. No static word lists.
2. Zero Financial Harm: 100% offline search and segmentation; zero external API calls on search path.
3. Sub-millisecond Execution: Dynamic programming segmentation must operate in O(N) time for word length <= 32.
4. Privacy: Chat history persistence must remain strictly in `sessionStorage` (zero server transmission).
5. Quality Gates: All tests in `tests/` must achieve 100% pass (Exit 0).
```
