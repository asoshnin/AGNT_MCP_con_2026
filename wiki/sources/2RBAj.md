---
id: "2RBAj"
title: "From API Catalogs To Agent Catalogs: Solving MCP Server Discovery With Open Resource Discovery"
speakers: ["Vyshnavi Gadamsetti", "Sebastian Wennemers"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBAj/from-api-catalogs-to-agent-catalogs-solving-mcp-server-discovery-with-open-resource-discovery-vyshnavi-gadamsetti-sebastian-wennemers-sap-se"
concepts: ["mcp", "orchestration", "tool-use", "evaluation"]
relevance_score: 0.95
relevance_rationale: "Directly addresses a core challenge in scaling MCP ecosystems – server discovery and metadata management – by proposing a standardized, open-source solution (ORD) that is highly relevant to agent orchestration and tool-use."
resources:
  - url: "https://open-resource-discovery.github.io/mcp-server-card-ui/"
    label: "MCP Server Card UI"
  - url: "https://github.com/modelcontextprotocol/ext-server-card/issues/30"
    label: "SEP-2127 Discussion"
  - url: "https://github.com/open-resource-discovery/ord-mcp-server-card-demo"
    label: "ORD MCP Server Card Demo"
  - url: "https://open-resource-discovery.org/"
    label: "Open Resource Discovery Official Site"
---

# From API Catalogs To Agent Catalogs: Solving MCP Server Discovery With Open Resource Discovery

**Canonical Presentation on Sched:** [From API Catalogs To Agent Catalogs: Solving MCP Server Discovery With Open Resource Discovery](https://agntconmcpconeu26.sched.com/event/2RBAj/from-api-catalogs-to-agent-catalogs-solving-mcp-server-discovery-with-open-resource-discovery-vyshnavi-gadamsetti-sebastian-wennemers-sap-se)  
**Speakers:** Vyshnavi Gadamsetti (Software Development Architect, SAP SE), Sebastian Wennemers (Chief Architect, SAP SE)  
**Relevance Score:** `0.95`

## Essence

The talk addresses the critical problem of MCP server discovery and fragmentation, mirroring the API landscape a decade ago. It proposes extending Open Resource Discovery (ORD) to create 'Agent Catalogs,' enabling MCP servers to self-describe their capabilities, including tools and prompts, via a static, machine-readable 'Server Card' at a well-known endpoint. This allows registries and gateways to crawl and aggregate these descriptions, facilitating efficient discovery and reasoning about thousands of MCP servers without requiring live connections. The core insight is to shift from point-to-point integration to a standardized, declarative metadata publication model, significantly enhancing scalability and governance for agent ecosystems.

## Key Takeaways & Recommendations

- Adopt Open Resource Discovery (ORD) for MCP server self-description to enable scalable discovery.
- Implement 'Server Cards' at well-known endpoints for MCP servers to publish their tools, prompts, and metadata.
- Contribute to and leverage community standards like SEP-2127 for MCP server description.
- Utilize aggregators and registries to build catalogs from published Server Cards, decoupling discovery from live server connections.

## Discovered Resources

- [MCP Server Card UI](https://open-resource-discovery.github.io/mcp-server-card-ui/)
- [SEP-2127 Discussion](https://github.com/modelcontextprotocol/ext-server-card/issues/30)
- [ORD MCP Server Card Demo](https://github.com/open-resource-discovery/ord-mcp-server-card-demo)
- [Open Resource Discovery Official Site](https://open-resource-discovery.org/)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[tool-use]]
- [[evaluation]]
