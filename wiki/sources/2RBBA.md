---
id: "2RBBA"
title: "Attribution by Design: Skills, MCP, and Where Provenance Gets Built In"
speakers: ["Ola Hungerford"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBBA/attribution-by-design-skills-mcp-and-where-provenance-gets-built-in-ola-hungerford-model-context-protocol"
concepts: ["mcp", "orchestration", "tool-use", "observability"]
relevance_score: 0.95
relevance_rationale: "Directly discusses the Model Context Protocol (MCP) and its application to managing and attributing 'Skills' in agent systems, which is central to AGNTCon and MCPCon themes."
resources:
---

# Attribution by Design: Skills, MCP, and Where Provenance Gets Built In

**Canonical Presentation on Sched:** [Attribution by Design: Skills, MCP, and Where Provenance Gets Built In](https://agntconmcpconeu26.sched.com/event/2RBBA/attribution-by-design-skills-mcp-and-where-provenance-gets-built-in-ola-hungerford-model-context-protocol)  
**Speakers:** Ola Hungerford (Principal Engineer, Nordstrom)  
**Relevance Score:** `0.95`

## Essence

This talk addresses the critical challenge of maintaining provenance and attribution for human expertise and other content encoded as 'Skills' within AI agent systems, especially as these systems increasingly rely on the Model Context Protocol (MCP). It highlights that without explicit design, attribution is lost, making MCP and Skills a crucial decision point for embedding provenance. The core technical insight involves leveraging MCP's 'Interceptors' – deterministic hooks in clients, servers, and gateways – to standardize how, why, and when Skills are served and attributed. This architecture enables the creation of an attribution gateway for centralized authorship validation and recording, alongside standardized client-side hooks to log and credit authors upon Skill invocation, ensuring that human contributions are properly recognized and auditable.

## Key Takeaways & Recommendations

- Design for provenance explicitly within Skill and MCP implementations, rather than assuming it will emerge.
- Utilize MCP Interceptors as deterministic hooks to embed attribution logic at various points in the request lifecycle (client, server, gateway).
- Implement a centralized attribution gateway to validate and record authorship for Skills.
- Develop standardized client-side hooks to log and credit authors whenever Skills are invoked by an agent.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[tool-use]]
- [[observability]]
