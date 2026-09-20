---
id: "2RB8w"
title: "What *IS* an Agent's Identity?"
speakers: ["Christian Posta"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8w/what-is-an-agents-identity-christian-posta-soloio"
concepts: ["identity", "security", "orchestration", "mcp", "tool-use"]
relevance_score: 0.95
relevance_rationale: "Directly addresses a fundamental security and governance challenge for AI agents, which is central to both AGNTCon and MCPCon themes, particularly concerning agent orchestration and interaction with enterprise resources."
resources:
  - url: "https://blog.christianposta.com"
    label: "Christian Posta's Blog"
---

# What *IS* an Agent's Identity?

**Canonical Presentation on Sched:** [What *IS* an Agent's Identity?](https://agntconmcpconeu26.sched.com/event/2RB8w/what-is-an-agents-identity-christian-posta-soloio)  
**Speakers:** Christian Posta (Global Field CTO, Solo.io)  
**Relevance Score:** `0.95`

## Essence

The talk addresses the critical challenge of defining and managing identity for AI agents within enterprise environments, distinguishing it from traditional human or service account identities. It posits that an agent's identity is a composite of its authentication, delegated authority, provenance, and established trust, all crucial for accountability and revocation. The core insight is that agents, driven by intent and tool invocation, require a robust identity framework to answer 'who', 'what allowed', and 'what done' questions. The session explores how existing technologies like OAuth, OpenID Connect, and SPIFFE, alongside emerging standards like AAuth, can be leveraged to construct this framework, providing a practical approach to securing and governing agent interactions.

## Key Takeaways & Recommendations

- Adopt a composite view of agent identity, encompassing authentication, delegated authority, provenance, and trust.
- Leverage existing identity standards (OAuth, OpenID Connect, SPIFFE) where applicable, while exploring emerging solutions like AAuth for agent-specific challenges.
- Prioritize mechanisms for delegated authority and clear provenance tracking to ensure agent accountability.
- Implement robust revocation capabilities for agent authority as a fundamental security measure.

## Discovered Resources

- [Christian Posta's Blog](https://blog.christianposta.com)

## Related Concepts

- [[identity]]
- [[security]]
- [[orchestration]]
- [[mcp]]
- [[tool-use]]
