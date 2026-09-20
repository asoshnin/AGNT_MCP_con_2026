---
id: "2RBAL"
title: "Agents Can Pay. Can They Prove It?"
speakers: ["Diego Zuluaga"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBAL/agents-can-pay-can-they-prove-it-diego-zuluaga-open-mobile-hub"
concepts: ["mcp", "security", "identity", "orchestration"]
relevance_score: 0.98
relevance_rationale: "Directly addresses the core problem of secure, verifiable identity and payment integration for AI agents, a fundamental challenge in agentic commerce and trust."
resources:
  - url: "https://github.com/dzuluaga/mcp-apps-shopping-demo"
    label: "MCP Apps Shopping Demo"
---

# Agents Can Pay. Can They Prove It?

**Canonical Presentation on Sched:** [Agents Can Pay. Can They Prove It?](https://agntconmcpconeu26.sched.com/event/2RBAL/agents-can-pay-can-they-prove-it-diego-zuluaga-open-mobile-hub)  
**Speakers:** Diego Zuluaga (Lead, Open Mobile Hub (Linux Foundation), Open Mobile Hub)  
**Relevance Score:** `0.98`

## Essence

This talk addresses the critical, often-overlooked challenge of securely integrating real-world, government-grade digital identity and payment credentials into AI agent workflows. It demonstrates a full architectural chain where an AI agent, via an MCP server, requests verifiable credentials (like mdoc or SD-JWT) from a user's hardware-secured mobile wallet (e.g., StrongBox, TEE, Secure Enclave). The process leverages open standards such as W3C Digital Credentials API, OpenID4VP, and FIDO caBLE for cross-device communication, ensuring user intent is explicitly bound and proven. The core insight is enabling AI agents to not just 'pay' or 'verify' but to cryptographically 'prove' authorization and identity using robust, open-source digital credential infrastructure, moving beyond mere demo-ware to production-ready solutions.

## Key Takeaways & Recommendations

- Utilize open standards like W3C Digital Credentials API, OpenID4VP, and FIDO caBLE for interoperable digital credential exchange.
- Implement hardware-backed security (StrongBox, TEE, Secure Enclave) for storing and processing sensitive digital credentials.
- Develop and deploy open-source Digital Credential MCP servers to facilitate secure agent-credential interactions.
- Ensure explicit user intent binding (e.g., via AP2 mandate) for all agent-initiated credential requests.

## Discovered Resources

- [MCP Apps Shopping Demo](https://github.com/dzuluaga/mcp-apps-shopping-demo)

## Related Concepts

- [[mcp]]
- [[security]]
- [[identity]]
- [[orchestration]]
