---
id: "2RBAg"
title: "Agents Talking To Agents: MCP, A2A, and the Reality of Multi-Agent Orchestration in Production"
speakers: ["Willem Berroubache"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBAg/agents-talking-to-agents-mcp-a2a-and-the-reality-of-multi-agent-orchestration-in-production-willem-berroubache-orange"
concepts: ["mcp", "orchestration", "security", "sandboxing", "evaluation"]
relevance_score: 0.98
relevance_rationale: "Directly addresses multi-agent orchestration, MCP, A2A protocols, and security challenges in production environments, aligning perfectly with AGNTCon + MCPCon themes."
resources:
  - url: "https://www.linkedin.com/in/willem-b"
    label: "Willem Berroubache's LinkedIn"
---

# Agents Talking To Agents: MCP, A2A, and the Reality of Multi-Agent Orchestration in Production

**Canonical Presentation on Sched:** [Agents Talking To Agents: MCP, A2A, and the Reality of Multi-Agent Orchestration in Production](https://agntconmcpconeu26.sched.com/event/2RBAg/agents-talking-to-agents-mcp-a2a-and-the-reality-of-multi-agent-orchestration-in-production-willem-berroubache-orange)  
**Speakers:** Willem Berroubache (AI for Security Project Manager, Orange)  
**Relevance Score:** `0.98`

## Essence

This talk dissects the critical challenges of deploying multi-agent systems in production, moving beyond theoretical 'happy paths' to address real-world failures in context preservation, ownership, authority, and causality. It introduces a practical architecture pattern: A2A (Agent-to-Agent) for delegation and MCP (Multi-Agent Communication Protocol) for execution. The core insight is to leverage A2A for high-level task handoffs while strictly enforcing execution boundaries and verifying outcomes via MCP servers. This approach aims to prevent issues like agents losing context, trust boundary collapses, and unauthorized actions by ensuring task-scoped authority and robust validation, particularly crucial in regulated environments.

## Key Takeaways & Recommendations

- Implement a durable workflow engine to own state transitions, allowing LLMs to reason within bounded specialist nodes.
- Issue short-lived, task-scoped authority via policy, with MCP servers verifying scope before any mutation.
- Establish governed feedback loops where verified outcomes drive evaluation, and human review is directed to ambiguity and high-impact changes, rather than universal approvals.

## Discovered Resources

- [Willem Berroubache's LinkedIn](https://www.linkedin.com/in/willem-b)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[security]]
- [[sandboxing]]
- [[evaluation]]
