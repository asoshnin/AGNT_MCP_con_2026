---
id: "2RBBG"
title: "Gating High-Risk Agentic Actions at the Relying Party With Exogenous (Out-of-Band) Inputs"
speakers: ["Andrew Bud"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBBG/gating-high-risk-agentic-actions-at-the-relying-party-with-exogenous-out-of-band-inputs-andrew-bud-iproov"
concepts: ["security", "mcp", "orchestration", "identity"]
relevance_score: 0.95
relevance_rationale: "Directly addresses a critical security vulnerability (Confused Deputy) in agentic systems and proposes an architectural pattern for mitigating high-risk actions, highly relevant to AGNTCon and MCPCon themes."
resources:
---

# Gating High-Risk Agentic Actions at the Relying Party With Exogenous (Out-of-Band) Inputs

**Canonical Presentation on Sched:** [Gating High-Risk Agentic Actions at the Relying Party With Exogenous (Out-of-Band) Inputs](https://agntconmcpconeu26.sched.com/event/2RBBG/gating-high-risk-agentic-actions-at-the-relying-party-with-exogenous-out-of-band-inputs-andrew-bud-iproov)  
**Speakers:** Andrew Bud (Founder & CEO, iProov)  
**Relevance Score:** `0.95`

## Essence

The talk addresses the 'Confused Deputy' problem in agentic systems, where an agent, despite having valid credentials, is coerced (e.g., via prompt injection) into performing high-risk actions unintended by its principal. The core insight is that while access might be authenticated, the principal's consent to specific actions is not guaranteed. To mitigate this, the proposed architecture introduces an exogenous (out-of-band) gatekeeper at the relying party (RP). This gatekeeper requires a proof of intent and presence that the compromised agent cannot generate, ensuring that high-risk actions are explicitly consented to by the human principal before execution. This decentralized, open-source pattern integrates with existing authentication schemes like OAuth, MCP, and passkeys, establishing a crucial intent boundary for agent-mediated workflows and providing a legally auditable record.

## Key Takeaways & Recommendations

- Deploy an exogenous gatekeeper at the relying party to distinguish between authorized access and authorized actions.
- Require an out-of-band proof of principal presence and consent for high-risk agentic actions, independent of the agent's context.
- Implement a decentralized, open-source relying-party pattern that composes with existing authentication standards (OAuth, MCP, passkeys) to add an intent boundary.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[security]]
- [[mcp]]
- [[orchestration]]
- [[identity]]
