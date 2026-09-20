---
id: "2RB8S"
title: "Stateless: The Future of MCP Transports"
speakers: ["Kurtis Van Gent", "Shaun Smith"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8S/stateless-the-future-of-mcp-transports-kurtis-van-gent-google-shaun-smith-hugging-face"
concepts: ["mcp", "orchestration"]
relevance_score: 0.95
relevance_rationale: "Directly addresses a core architectural evolution of MCP, a foundational protocol for agent communication, impacting scalability and deployment patterns."
resources:
---

# Stateless: The Future of MCP Transports

**Canonical Presentation on Sched:** [Stateless: The Future of MCP Transports](https://agntconmcpconeu26.sched.com/event/2RB8S/stateless-the-future-of-mcp-transports-kurtis-van-gent-google-shaun-smith-hugging-face)  
**Speakers:** Kurtis Van Gent (MCP Core Maintainer, Google), Shaun Smith (Open Source Agents / MCP, Hugging Face)  
**Relevance Score:** `0.95`

## Essence

The talk announces a pivotal shift in the MCP (Multi-Agent Communication Protocol) architecture towards a stateless transport layer, marking one of its most significant changes since inception. This fundamental redesign aims to simplify the deployment of highly robust and scalable MCP servers, essential for accommodating the burgeoning demand from AI agents and new applications like MCP Apps. By moving to a stateless model, the protocol can better support serverless patterns for core operations such as Elicitation, Sampling, and Session management. The speakers, key members of the Transports Working Group from Google and Hugging Face, will present the motivations behind this change, backed by real-world data, and outline the new application and infrastructure patterns that leverage the stateless protocol, along with migration timelines.

## Key Takeaways & Recommendations

- Adopt serverless patterns for Elicitation, Sampling, and Sessions to leverage the new stateless MCP transport.
- Design applications and infrastructure to take advantage of the stateless protocol for enhanced scalability and robustness.
- Stay informed on the MCP roadmap and migration timelines for transitioning existing deployments to the stateless model.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[orchestration]]
