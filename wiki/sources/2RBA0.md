---
id: "2RBA0"
title: "Workshop: Keep Infrastructure Out of Your AI Agents: The Agent Gateway Pattern"
speakers: ["Lin Sun"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBA0/workshop-keep-infrastructure-out-of-your-ai-agents-the-agent-gateway-pattern-lin-sun-soloio"
concepts: ["mcp", "security", "orchestration", "observability"]
relevance_score: 0.95
relevance_rationale: "Directly discusses a core architectural pattern (Agent Gateway) for managing and securing AI agents and MCP servers, which is highly relevant to AGNTCon and MCPCon themes."
resources:
  - url: "https://jqlang.org/"
    label: "jq - command-line JSON processor"
  - url: "https://jqlang.org/Docker"
    label: "jq Docker"
---

# Workshop: Keep Infrastructure Out of Your AI Agents: The Agent Gateway Pattern

**Canonical Presentation on Sched:** [Workshop: Keep Infrastructure Out of Your AI Agents: The Agent Gateway Pattern](https://agntconmcpconeu26.sched.com/event/2RBA0/workshop-keep-infrastructure-out-of-your-ai-agents-the-agent-gateway-pattern-lin-sun-soloio)  
**Speakers:** Lin Sun (Head of Open Source, Solo.io)  
**Relevance Score:** `0.95`

## Essence

The 'Agent Gateway Pattern' addresses the growing complexity of deploying AI agents in production by centralizing infrastructure concerns. Instead of embedding security, observability, routing, and policy enforcement directly into each agent, MCP server, or application, this pattern introduces a unified gateway layer. This gateway acts as a control plane, functioning as an MCP, LLM, inference, and traditional API gateway, abstracting away critical operational challenges. It enables secure, scalable, and governable AI systems by providing a single point for traffic management, access control, rate limiting, and end-to-end visibility, thereby simplifying operations and reducing code changes within the agents themselves.

## Key Takeaways & Recommendations

- Adopt an agent gateway pattern to centralize infrastructure concerns like security, routing, and observability, rather than embedding them in individual agents.
- Utilize a unified gateway to manage traffic across multiple LLM providers, enabling failover and consistent policy enforcement.
- Implement the gateway for enforcing authentication, authorization, and usage policies without modifying agent code.
- Leverage the gateway for end-to-end observability into agent interactions and traffic.

## Discovered Resources

- [jq - command-line JSON processor](https://jqlang.org/)
- [jq Docker](https://jqlang.org/Docker)

## Related Concepts

- [[mcp]]
- [[security]]
- [[orchestration]]
- [[observability]]
