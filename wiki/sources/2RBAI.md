---
id: "2RBAI"
title: "Economies of Scale for MCP and Agents: Why You Need an Identity Broker"
speakers: ["Magnus Jungsbluth", "Jan Brennenstuhl"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBAI/economies-of-scale-for-mcp-and-agents-why-you-need-an-identity-broker-magnus-jungsbluth-jan-brennenstuhl-zalando-se"
concepts: ["mcp", "security", "orchestration", "identity"]
relevance_score: 0.98
relevance_rationale: "Directly addresses the core problem of scaling security and identity management for MCPs and agentic systems, proposing a concrete architectural solution (Identity Broker) and drawing parallels to microservice scaling challenges."
resources:
---

# Economies of Scale for MCP and Agents: Why You Need an Identity Broker

**Canonical Presentation on Sched:** [Economies of Scale for MCP and Agents: Why You Need an Identity Broker](https://agntconmcpconeu26.sched.com/event/2RBAI/economies-of-scale-for-mcp-and-agents-why-you-need-an-identity-broker-magnus-jungsbluth-jan-brennenstuhl-zalando-se)  
**Speakers:** Magnus Jungsbluth (Senior Principal Engineer, Zalando SE), Jan Brennenstuhl (Principal Software Engineer, Zalando SE)  
**Relevance Score:** `0.98`

## Essence

Scaling agentic systems and Multi-Agent Collaboration Platforms (MCPs) necessitates abstracting authentication and authorization concerns into a dedicated infrastructure layer, mirroring lessons learned from microservice architectures. Zalando's Agentic Identity Broker, an open-source solution, centralizes identity management for agents and MCPs, enabling delegated access chains across diverse applications. This broker integrates with existing identity providers and projects like CNCF's agentgateway, offloading complex security logic from individual agents and MCP servers. By shifting these shared concerns to the platform, product teams can focus on core agent behavior and domain-specific tools, ensuring consistent security, governance, and simplified development for large-scale agent deployments.

## Key Takeaways & Recommendations

- Shift common implementation concerns like authentication and authorization into a shared platform layer, rather than rebuilding them within each agent or MCP.
- Utilize an identity broker to centralize delegated access for agents and MCPs, integrating with existing identity providers and IAM investments.
- Apply just enough governance through the platform to manage tool approvals and human-in-the-loop enforcement centrally, without requiring agent or MCP authors to implement these features.
- Focus product engineering teams on agent behavior and domain tools by abstracting away infrastructure-level security complexities.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[security]]
- [[orchestration]]
- [[identity]]
