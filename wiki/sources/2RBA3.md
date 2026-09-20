---
id: "2RBA3"
title: "From "Works on My Prompt" To Production SLOs: Building Agent Observability"
speakers: ["Manik Khandelwal"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBA3/from-works-on-my-prompt-to-production-slos-building-agent-observability-manik-khandelwal-microsoft"
concepts: ["observability", "evaluation", "orchestration", "mcp"]
relevance_score: 0.92
relevance_rationale: "Directly addresses the critical need for observability and evaluation in production AI agents, a core concern for AGNTCon, and mentions MCP server usage."
resources:
---

# From "Works on My Prompt" To Production SLOs: Building Agent Observability

**Canonical Presentation on Sched:** [From "Works on My Prompt" To Production SLOs: Building Agent Observability](https://agntconmcpconeu26.sched.com/event/2RBA3/from-works-on-my-prompt-to-production-slos-building-agent-observability-manik-khandelwal-microsoft)  
**Speakers:** Manik Khandelwal (Senior Software engineer, Microsoft)  
**Relevance Score:** `0.92`

## Essence

This talk addresses the critical challenge of achieving production-grade reliability for AI agents, moving beyond 'works on my prompt' to measurable Service Level Objectives (SLOs). The core insight is that traditional monitoring fails to capture silent agent degradations like plausible-but-wrong outputs or inefficient tool use. The proposed solution involves a specialized observability and evaluation stack that integrates OpenTelemetry for granular instrumentation of agentic workflows, LLM-as-judge evaluation for qualitative assessment of agent responses, and automated regression gates within CI/CD pipelines. This architecture aims to make agent failures visible and catchable proactively, ensuring robust performance in real-world scenarios.

## Key Takeaways & Recommendations

- Implement OpenTelemetry for granular instrumentation of agentic workflows, capturing traces and metrics specific to LLM calls, tool invocations, and reasoning steps.
- Utilize LLM-as-judge evaluation for qualitative assessment of agent outputs, moving beyond simple correctness checks to evaluate relevance, coherence, and efficiency.
- Integrate automated regression gates into CI/CD pipelines to prevent degraded agent performance from reaching production.
- Design observability specifically for agents, recognizing that traditional system metrics are insufficient for detecting subtle AI failures.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[observability]]
- [[evaluation]]
- [[orchestration]]
- [[mcp]]
