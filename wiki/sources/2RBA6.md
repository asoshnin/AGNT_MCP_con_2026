---
id: "2RBA6"
title: "From MCP Playground To Org-Wide Infrastructure: Lessons From Building Booking.com's Agent Foundry"
speakers: ["Anushka Bhandari"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBA6/from-mcp-playground-to-org-wide-infrastructure-lessons-from-building-bookingcoms-agent-foundry-anushka-bhandari-bookingcom"
concepts: ["mcp", "orchestration", "identity", "security", "tool-use"]
relevance_score: 0.98
relevance_rationale: "Directly discusses the architectural and organizational challenges and solutions for scaling MCPs in an enterprise context, focusing on infrastructure, identity, and contribution management."
resources:
---

# From MCP Playground To Org-Wide Infrastructure: Lessons From Building Booking.com's Agent Foundry

**Canonical Presentation on Sched:** [From MCP Playground To Org-Wide Infrastructure: Lessons From Building Booking.com's Agent Foundry](https://agntconmcpconeu26.sched.com/event/2RBA6/from-mcp-playground-to-org-wide-infrastructure-lessons-from-building-bookingcoms-agent-foundry-anushka-bhandari-bookingcom)  
**Speakers:** Anushka Bhandari (Software Engineer, Booking.com)  
**Relevance Score:** `0.98`

## Essence

Booking.com's Agent Foundry addresses the critical organizational and infrastructural challenges of scaling Multi-Agent Collaboration Platforms (MCPs) from proof-of-concept to enterprise-wide production. The core insight is that the primary hurdles are not technical, but rather revolve around shared ownership, consistent contribution review, and unified identity management across diverse user types (humans and agents). Their solution involves a two-tier MCP gateway integrating with over 20 enterprise services, featuring a single OAuth flow for both human and agent authentication. This architecture includes a skills registry with AI-reviewed contributions and composable profiles, enabling the bundling of MCPs and skills into workflow-specific harnesses, thereby fostering skill reuse and compounding value across teams.

## Key Takeaways & Recommendations

- Implement a unified identity and access management (IAM) system (e.g., single OAuth flow) for both human users and autonomous agents to streamline access to enterprise resources.
- Establish a centralized skills registry with automated (AI-assisted) review processes to ensure quality, security, and reusability of agent contributions.
- Design composable agent profiles and harnesses that allow for flexible bundling of MCPs and skills, enabling rapid deployment of workflow-specific agentic solutions.
- Focus on building robust, shared infrastructure that abstracts away underlying complexities, allowing diverse teams to contribute and leverage agentic capabilities without deep institutional knowledge of production incidents.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[identity]]
- [[security]]
- [[tool-use]]
