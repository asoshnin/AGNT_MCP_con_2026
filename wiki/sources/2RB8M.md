---
id: "2RB8M"
title: "An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers"
speakers: ["Muhammad Ahsan Ayaz"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8M/an-orchestra-of-agents-what-i-learned-running-a-multi-agent-system-for-5000+-developers-muhammad-ahsan-ayaz-scania"
concepts: ["mcp", "orchestration", "agent-gateway", "evaluation", "security"]
relevance_score: 0.91
relevance_rationale: "High-relevance production case study on multi-agent orchestration patterns, ADK architecture, MCP integration, and concurrency failure modes at scale."
resources:
  - url: "https://github.com/AhsanAyaz/code-with-ahsan"
    label: "Official Implementation"
---

# An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers

**Canonical Presentation on Sched:** [An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers](https://agntconmcpconeu26.sched.com/event/2RB8M/an-orchestra-of-agents-what-i-learned-running-a-multi-agent-system-for-5000+-developers-muhammad-ahsan-ayaz-scania)  
**Speakers:** Muhammad Ahsan Ayaz  
**Relevance Score:** `0.91`

## Essence

Muhammad Ahsan Ayaz presents a postmortem of a multi-agent system (16 agents, 5,000+ developers) built on Google's ADK (Agent Development Kit) with MCP integration. The core architectural lesson is the route-only root pattern: the orchestrator root_agent must carry only routing instructions and zero tools, otherwise it hoards turns and starves leaf sub-agents. A single break statement in the root caused a cascading outage where all 5,000 developers saw 'dev.to temporarily unavailable' — illustrating how one bad routing decision poisons the entire fan-out. Temporal context is injected via a 10-token system_instruction append rather than a get_date tool call, saving round-trip latency. The critical production bug was a fan-out race: the external_knowledge_synthesizer must produce its final response faster than the fastest leaf, otherwise is_final_response() fires per-agent and the stream drains incorrectly. ADK's Event.is_final_response() semantics change when multiple agents participate — each agent can emit its own final event, so the orchestrator must drain the complete stream per-agent, not assume a single terminal event. The speaker confesses the fix shipped without a regression test, then writes the missing async test validating synthesizer beats leaf in race conditions.

## Key Takeaways & Recommendations

- Use route-only root_agent with instruction=ROUTING_INSTRUCTION and zero tools; all work lives in leaf sub_agents
- Inject temporal context via system_instruction append (≈10 tokens) instead of a tool call to avoid round-trip latency
- Drain the full event stream checking is_final_response() per participating agent — never assume a single terminal event in multi-agent invocations
- Write regression tests for concurrency/race conditions before considering any fix complete; async test_synthesizer_beats_fastest_leaf_in_fan_out_race is the template
- Prefer determinism where possible; deploy LLM only where necessary, and keep production receipts for every routing decision

## Production Gotchas & Failure Modes

- Root agent hoarding tool calls starves leaf sub-agents — the orchestrator routes, never answers; any tool attached to root steals turns from leaves
- Fan-out race condition where synthesizer loses to fastest leaf, causing premature stream drain and incomplete answers
- Missing regression tests for concurrency fixes — the speaker shipped the fix for weeks before writing the draining test

## Discovered Resources

- [Official Implementation](https://github.com/AhsanAyaz/code-with-ahsan)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[agent-gateway]]
- [[evaluation]]
- [[security]]
