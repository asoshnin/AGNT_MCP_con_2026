---
id: "2RBAy"
title: "Spotify’s Bet on MCP and Investment in Open Source"
speakers: ["Reinoud Kruithof", "Yannick Epstein"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBAy/spotifys-bet-on-mcp-and-investment-in-open-source-reinoud-kruithof-yannick-epstein-spotify"
concepts: ["mcp", "orchestration", "observability"]
relevance_score: 0.95
relevance_rationale: "Directly discusses the architectural evolution and sustainability challenges of an MCP gateway for AI agents, a core topic for AGNTCon + MCPCon."
resources:
---

# Spotify’s Bet on MCP and Investment in Open Source

**Canonical Presentation on Sched:** [Spotify’s Bet on MCP and Investment in Open Source](https://agntconmcpconeu26.sched.com/event/2RBAy/spotifys-bet-on-mcp-and-investment-in-open-source-reinoud-kruithof-yannick-epstein-spotify)  
**Speakers:** Reinoud Kruithof (Senior SRE, Spotify), Yannick Epstein (Senior Software Engineer, Spotify)  
**Relevance Score:** `0.95`

## Essence

Spotify rapidly adopted MCP servers, necessitating a custom 'MCP gateway' to expose internal APIs to AI agents. This initial bespoke solution, while effective, quickly became unsustainable due to rapid growth, uncertain ownership, and maintenance challenges. To address this, Spotify re-architected its gateway by leveraging open-source technologies like Envoy proxy, kgateway, kro, and the Gateway API. This transition allowed for deep integration with Spotify's existing infrastructure, service discovery, and microservice ecosystem, while distributing ownership and support across specialized teams. The new architecture ensures better long-term sustainability and scalability for their agentic API exposure.

## Key Takeaways & Recommendations

- Prioritize sustainability and clear domain ownership for critical infrastructure components, even in rapid development scenarios.
- Rebase custom solutions onto open-source technologies where possible to leverage community support and specialized expertise.
- Integrate new gateway solutions deeply with existing infrastructure management planes and service discovery mechanisms.
- Utilize standard APIs like Gateway API to ensure interoperability and future-proofing.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[observability]]
