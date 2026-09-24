---
id: "2RB8M"
title: "An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers"
speakers: ["Muhammad Ahsan Ayaz"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8M/an-orchestra-of-agents-what-i-learned-running-a-multi-agent-system-for-5000+-developers-muhammad-ahsan-ayaz-scania"
concepts: ["mcp", "orchestration", "evaluation", "security", "observability"]
relevance_score: 0.95
relevance_rationale: "Production case study of a 16-agent ADK system serving 5,000+ developers with concrete orchestration patterns, MCP tool integration, and battle-tested fixes for stream draining, recency drift, and root-agent anti-patterns."
resources:
  - url: "https://github.com/AhsanAyaz/code-with-ahsan"
    label: "Production Multi-Agent System Code"
  - url: "https://bio.link/codewithahsan"
    label: "Speaker Profile & Links"
  - url: "https://twitter.com/codewith_ahsan"
    label: "Speaker Twitter"
---

# An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers

**Canonical Presentation on Sched:** [An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers](https://agntconmcpconeu26.sched.com/event/2RB8M/an-orchestra-of-agents-what-i-learned-running-a-multi-agent-system-for-5000+-developers-muhammad-ahsan-ayaz-scania)  
**Speakers:** Muhammad Ahsan Ayaz (Software Architect, Scania)  
**Relevance Score:** `0.95`

## Essence

Muhammad Ahsan Ayaz details the production architecture of a 16-agent system serving 5,000+ developers, built on Google's Agent Development Kit (ADK) with MCP tool integration. The system decomposes community queries into a tree of specialist agents coordinated through three orchestration primitives: sequential pipelines (onboarding chains three agents), parallel fan-out (external knowledge agents query GitHub, Dev.to, and StackOverflow simultaneously), and LLM-driven dynamic routing at the root. The critical architectural invariant is a route-only root agent—stripped of tools and opinions—that delegates exclusively to leaf agents, avoiding the "busy conductor pitfall" where a tool-holding root starves sub-agents. Recency drift (surfacing 2020 content in 2026) was fixed with a ten-token callback injecting the current UTC date into system_instruction, eliminating a round-trip get_date tool call. A drain-loop bug cancelled ParallelAgent mid-flight because ADK's Event.is_final_response() returns true per participating agent; the fix requires fully draining the event stream and handling synthesizer/leaf race conditions in fan-out. A cross-cutting callback layer handles PII sanitization, caching, and observability—none documented in tutorials. The guiding principle: determinism where possible, LLMs only where necessary, and always drain the whole stream.

## Key Takeaways & Recommendations

- Enforce route-only root agents: orchestrators route, leaves work. Never attach tools to the root agent; all MCP tool use lives in specialist leaf agents.
- Inject current date via callback_context.append_instructions() (≈10 tokens) instead of a get_date tool to eliminate latency and prevent recency drift in external knowledge retrieval.
- Always drain the complete event stream in multi-agent invocations; handle Event.is_final_response() per participant and write regression tests for fan-out race conditions (synthesizer vs. fastest leaf).
- Build a reusable callback layer for cross-cutting concerns: PII sanitization, response caching, and structured observability hooks before they become production incidents.
- Prefer deterministic orchestration primitives (sequential, parallel, explicit routing) over LLM-driven planning for predictable latency and debuggability at scale.

## Production Gotchas & Failure Modes

- Drain-loop cancels ParallelAgent mid-flight when the orchestrator stops consuming events after the first Event.is_final_response(), leaving parallel branches unfinished.
- Recency drift surfaces stale third-party content (e.g., 2020 articles in 2026) because the LLM lacks a grounded current date; fixed by callback-injected date, not a tool call.
- Root agent hoarding tools (busy conductor pitfall) starves leaf agents of turns, breaking delegation; the root must be route-only with zero tools.

## Discovered Resources

- [Production Multi-Agent System Code](https://github.com/AhsanAyaz/code-with-ahsan)
- [Speaker Profile & Links](https://bio.link/codewithahsan)
- [Speaker Twitter](https://twitter.com/codewith_ahsan)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[evaluation]]
- [[security]]
- [[observability]]
