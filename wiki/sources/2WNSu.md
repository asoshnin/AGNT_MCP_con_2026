---
id: "2WNSu"
title: "Self-Healing Agents Need Observability"
speakers: ["Marcelo Trylesinski", "Founder Engineer @ PydanticPython MCP maintainerUvicorn/Starlette maintainer"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2WNSu/self-healing-agents-need-observability-marcelo-trylesinski-pydantic"
concepts: ["observability", "evaluation", "orchestration", "mcp"]
relevance_score: 0.95
relevance_rationale: "Directly addresses the critical role of observability in building reliable, self-healing agent systems, a core theme for AGNTCon + MCPCon."
resources:
---

# Self-Healing Agents Need Observability

**Canonical Presentation on Sched:** [Self-Healing Agents Need Observability](https://agntconmcpconeu26.sched.com/event/2WNSu/self-healing-agents-need-observability-marcelo-trylesinski-pydantic)  
**Speakers:** Marcelo Trylesinski (Software Engineer, Pydantic), Founder Engineer @ PydanticPython MCP maintainerUvicorn/Starlette maintainer  
**Relevance Score:** `0.95`

## Essence

Reliable self-healing agents necessitate a robust observability framework, moving beyond mere guesswork to informed improvement. This involves instrumenting agent runs with comprehensive tracing across prompts, model calls, tool selections, and MCP server interactions to reconstruct execution paths. A critical feedback loop is established through continuous evaluation of agent behavior, identifying failures from telemetry, and proposing fixes. Proposed changes must undergo validation and policy checks, with sensitive actions requiring human or policy approval, enabling safe and bounded self-improvement in production agent systems.

## Key Takeaways & Recommendations

- Implement comprehensive tracing across all agent execution steps, including prompts, model calls, tool selection, and MCP server interactions.
- Establish a continuous feedback loop incorporating evaluations, approvals, and rollback mechanisms for agent proposed changes.
- Design policy checks and human approval gates for sensitive or high-impact agent actions to ensure safety and control.
- Utilize telemetry to detect various failure modes and inform the agent's understanding of what went wrong.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[observability]]
- [[evaluation]]
- [[orchestration]]
- [[mcp]]
