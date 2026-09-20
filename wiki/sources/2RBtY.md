---
id: "2RBtY"
title: "Workshop: Governing AI Agent Actions: MCP and Beyond"
speakers: ["Shannon Williams", "Chris Urwin"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBtY/workshop-governing-ai-agent-actions-mcp-and-beyond-shannon-williams-chris-urwin-obot-ai"
concepts: ["mcp", "security", "orchestration", "identity", "observability"]
relevance_score: 0.98
relevance_rationale: "Directly addresses the architectural and security challenges of governing AI agent actions, including and extending beyond MCP, which is central to AGNTCon + MCPCon."
resources:
---

# Workshop: Governing AI Agent Actions: MCP and Beyond

**Canonical Presentation on Sched:** [Workshop: Governing AI Agent Actions: MCP and Beyond](https://agntconmcpconeu26.sched.com/event/2RBtY/workshop-governing-ai-agent-actions-mcp-and-beyond-shannon-williams-chris-urwin-obot-ai)  
**Speakers:** Shannon Williams (President, Obot AI), Chris Urwin (VP of Field Engineering, Obot AI)  
**Relevance Score:** `0.98`

## Essence

This workshop addresses the critical architectural challenges of governing AI agent actions beyond the Model Context Protocol (MCP), encompassing CLIs, Skills, and direct API calls from generated code. The core insight is that while MCP facilitates agent-tool connection, comprehensive enterprise-grade control requires a unified policy framework for all agent actions. This framework must define allowed actions, enforce user/group-based access control, and integrate human-in-the-loop approvals. The solution necessitates managed registries for MCP servers and Skills to establish a trusted ecosystem, alongside robust logging and auditing capabilities for compliance and the proactive discovery and management of 'shadow AI' to ensure security and cost visibility.

## Key Takeaways & Recommendations

- Implement a unified policy engine for agent actions that applies across MCP servers, CLIs, Skills, and agent-generated code, incorporating allowlists and user/group-based access control.
- Establish managed registries for MCP servers and Skills, requiring administrative review and approval to enhance the trust model.
- Develop comprehensive logging and auditing mechanisms to capture all agent and tool activity, enabling export to enterprise storage and report generation for compliance.
- Actively discover and manage 'shadow AI' (unmanaged agents, MCPs, and Skills) to either block them or bring them under organizational governance.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[security]]
- [[orchestration]]
- [[identity]]
- [[observability]]
