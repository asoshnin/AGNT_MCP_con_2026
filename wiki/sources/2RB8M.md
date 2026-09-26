---
id: "2RB8M"
title: "An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers"
speakers: ["Muhammad Ahsan Ayaz"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8M/an-orchestra-of-agents-what-i-learned-running-a-multi-agent-system-for-5000+-developers-muhammad-ahsan-ayaz-scania"
concepts: ["mcp", "orchestration", "sandboxing"]
relevance_score: 0.94
relevance_rationale: "This session provides a production-grade blueprint for scaling multi-agent systems to enterprise levels (5,000+ developers). It covers critical architectural patterns (delegation over hoarding), protocol integration (MCP), and operational safeguards (deterministic streaming, regression testing). The concrete examples — such as the root-agent tool-hoarding pitfall and the 10-token date-context optimization — offer immediate, actionable guidance for engineers building similar systems."
resources:
  - url: "https://agntconmcpconeu26.sched.com/event/2RB8M/an-orchestra-of-agents-what-i-learned-running-a-multi-agent-system-for-5000+-developers-muhammad-ahsan-ayaz-scania"
    label: "Original Session"
  - url: "/assets/slides/2RB8M.pdf"
    label: "Slide Deck"
---

# An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers

**Canonical Presentation on Sched:** [An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers](https://agntconmcpconeu26.sched.com/event/2RB8M/an-orchestra-of-agents-what-i-learned-running-a-multi-agent-system-for-5000+-developers-muhammad-ahsan-ayaz-scania)  
**Speakers:** Muhammad Ahsan Ayaz  
**Relevance Score:** `0.94`

## Essence

Running a multi-agent system for 5,000+ developers reveals that orchestration must separate routing from execution. The core problem is preventing 'root hoarding' — when a root agent retains too many tools (e.g., search_blog_posts) it starves sub-agents because they lack access to the same capabilities. The fix is a strict delegation pattern: the root agent receives a ROUTING_INSTRUCTION and delegates all work to leaf sub-agents (content_agent, mentorship_agent, etc.), ensuring no single node monopolizes the toolset. This pattern scales linearly — with 16 agents across the system, each leaf operates independently without contention.

MCP serves as the glue protocol binding these agents. The speaker demonstrates a 10-token optimization: instead of invoking a dedicated date-tool (which adds a round-trip latency), the system-injects current UTC time directly into the LLM prompt via a custom function `inject_current_date`. This avoids unnecessary tool calls while keeping context fresh for third-party content queries. The architecture also enforces deterministic behavior where possible — draining the complete event stream from orchestrators ensures consistent state reconstruction, even under fan-out racing conditions (as shown in the synthesizer vs. leaf race test).

Security-wise, the design treats each sub-agent as an isolated sandbox: tools are scoped per-deployment, and the root agent acts purely as a router. No agent harvests another's tool inventory, eliminating cross-contamination risks. The system also guards against regressions through targeted tests that compare aggregated outputs from the synthesizer against individual leaf responses, catching drift before deployment.

## Key Takeaways & Recommendations

- Enforce a strict separation between the orchestrator (router) and worker agents: the root agent should only hold a routing instruction and delegate all tool usage to leaf sub-agents. This prevents capability monopolization and enables independent scaling.
- Inject contextual metadata (like current UTC timestamp) via system-level function calls rather than dedicated tool invocations. This reduces latency and eliminates unnecessary round trips in real-time queries.
- Implement comprehensive regression testing that compares aggregated outputs from all leaf agents against a canonical synthesizer response. Use structured event streams with explicit `is_final_response()` tracking to catch divergence early.

## Production Gotchas & Failure Modes

- Root agent hoarding tools (e.g., search_blog_posts) causes sub-agents to starve due to resource contention and missing capabilities.
- Race conditions in fan-out architectures where multiple leaf agents compete to produce final responses, requiring deterministic stream-draining and explicit synchronization.

## Discovered Resources

- [Original Session](https://agntconmcpconeu26.sched.com/event/2RB8M/an-orchestra-of-agents-what-i-learned-running-a-multi-agent-system-for-5000+-developers-muhammad-ahsan-ayaz-scania)
- [Slide Deck](/assets/slides/2RB8M.pdf)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[sandboxing]]
