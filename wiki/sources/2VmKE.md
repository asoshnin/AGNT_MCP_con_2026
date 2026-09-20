---
id: "2VmKE"
title: "Most MCP Servers are Empty"
speakers: ["David Golverdingen"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2VmKE/most-mcp-servers-are-empty-david-golverdingen-warmtebouw"
concepts: ["mcp", "evaluation", "orchestration", "rag", "tool-use"]
relevance_score: 0.98
relevance_rationale: "Directly addresses a critical problem in MCP and agent tool-use: the lack of semantic grounding and contextual meaning in tool descriptions, offering a practical methodology for improvement."
resources:
  - url: "https://github.com/DaveGold/mcp-metadata-demo"
    label: "MCP Metadata Demo Repo"
---

# Most MCP Servers are Empty

**Canonical Presentation on Sched:** [Most MCP Servers are Empty](https://agntconmcpconeu26.sched.com/event/2VmKE/most-mcp-servers-are-empty-david-golverdingen-warmtebouw)  
**Speakers:** David Golverdingen (Senior Engineer & MCP Architect, Warmtebouw)  
**Relevance Score:** `0.98`

## Essence

This talk argues that most MCP (Multi-Agent Communication Protocol) servers are 'empty' because they fail to convey crucial domain-specific meaning to agents, leading to misinterpretations even when data is technically correct. The core problem isn't data quality but the absence of contextual interpretation within tool descriptions, forcing agents to guess meaning. Golverdingen proposes a 'maturity ladder' for MCP tools, moving from simple API wrappers to 'self-teaching' tools that embed domain knowledge directly. He introduces 'Introspective Context Engineering,' an iterative loop (Examine, Flag, Validate, Encode, Iterate) where AI identifies patterns and human experts refine them, augmented by telemetry that logs agent intent to expose meaning gaps. This approach aims to enrich tool descriptions, ensuring agents understand the 'why,' 'how,' and 'what' of tool usage at every stage of interaction.

## Key Takeaways & Recommendations

- Scaffold MCP tools from API documentation, then ship a simple version to establish a baseline.
- Implement Introspective Context Engineering: an iterative loop of Examine, Flag, Validate, Encode, and Iterate to embed domain knowledge into tool descriptions.
- Utilize telemetry to log `queryIntent` for every tool call, revealing the agent's perceived action and exposing gaps in understanding.
- Ensure tool descriptions provide context for 'why/why not' to use a tool (before selection), 'how' to call it (after selection), and 'what' the result means (after response).

## Discovered Resources

- [MCP Metadata Demo Repo](https://github.com/DaveGold/mcp-metadata-demo)

## Related Concepts

- [[mcp]]
- [[evaluation]]
- [[orchestration]]
- [[rag]]
- [[tool-use]]
