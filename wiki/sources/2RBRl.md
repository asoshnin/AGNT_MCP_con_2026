---
id: "2RBRl"
title: "Sponsored Session: Beyond the Easy 80%: Bringing Legacy, Spatial, and Locked-Down Data to MCP"
speakers: ["Sanae Mendoza"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBRl/sponsored-session-beyond-the-easy-80-bringing-legacy-spatial-and-locked-down-data-to-mcp-sanae-mendoza-safe-software"
concepts: ["mcp", "security", "orchestration", "tool-use", "sandboxing"]
relevance_score: 0.98
relevance_rationale: "Directly addresses a fundamental challenge in MCP: integrating diverse, often sensitive, and complex enterprise data sources as callable tools for agents, focusing on architectural separation and data governance."
resources:
  - url: "https://docs.google.com/file/d/15SynMIVa9vrMjjt2QZm4d5rU4Z_9tYeI/preview"
    label: "Beyond the Easy 80% (Slides)"
---

# Sponsored Session: Beyond the Easy 80%: Bringing Legacy, Spatial, and Locked-Down Data to MCP

**Canonical Presentation on Sched:** [Sponsored Session: Beyond the Easy 80%: Bringing Legacy, Spatial, and Locked-Down Data to MCP](https://agntconmcpconeu26.sched.com/event/2RBRl/sponsored-session-beyond-the-easy-80-bringing-legacy-spatial-and-locked-down-data-to-mcp-sanae-mendoza-safe-software)  
**Speakers:** Sanae Mendoza (Customer Solutions Specialist, Safe Software)  
**Relevance Score:** `0.98`

## Essence

This talk addresses the critical challenge of integrating 'hard' enterprise data – legacy systems, spatial formats, real-time feeds, and regulated on-premise data – into the Multi-Agent Collaboration Protocol (MCP) ecosystem. While MCP excels at standardizing tool discovery and invocation for readily available 'easy 80%' data (e.g., SaaS APIs), the 'hard 20%' often contains the most decision-relevant information but lacks direct agent access due to issues of representation, locality, complex computation, and strict authority requirements. The core insight is to treat complex data integration workflows themselves as callable MCP tools, effectively abstracting away the underlying data complexity and ensuring data remains in place when necessary. This approach emphasizes separating the agent's control plane (what it can call) from the execution plane (where data resides and is processed), enabling agents to leverage diverse, sensitive, and proprietary data sources without compromising security or data governance.

## Key Takeaways & Recommendations

- Treat complex data integration workflows as callable MCP tools, rather than one-off scripts, to expose hard-to-reach data.
- Separate the control plane (what an agent is allowed to call) from the execution plane (where the data actually lives and stays) to manage data locality and security.
- Build integration solutions that can both consume MCP tools and expose custom tools, avoiding hardwiring to a single model or vendor.
- Focus on addressing the 'hard 20%' of enterprise data, which often holds the most decision-relevant context for agents, by tackling representation, locality, computation, and authority challenges.

## Discovered Resources

- [Beyond the Easy 80% (Slides)](https://docs.google.com/file/d/15SynMIVa9vrMjjt2QZm4d5rU4Z_9tYeI/preview)

## Related Concepts

- [[mcp]]
- [[security]]
- [[orchestration]]
- [[tool-use]]
- [[sandboxing]]
