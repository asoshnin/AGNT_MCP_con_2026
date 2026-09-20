---
id: "2RB9x"
title: "Potential Issues for Cross-domain Multi-hop API Calls and Their Solution Proposal"
speakers: ["Takashi Norimatsu"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9x/potential-issues-for-cross-domain-multi-hop-api-calls-and-their-solution-proposal-takashi-norimatsu-hitachi-ltd"
concepts: ["mcp", "security", "identity"]
relevance_score: 0.95
relevance_rationale: "Directly addresses security and identity management within the MCP framework, a core theme of MCPCon, focusing on practical issues in multi-domain API interactions."
resources:
---

# Potential Issues for Cross-domain Multi-hop API Calls and Their Solution Proposal

**Canonical Presentation on Sched:** [Potential Issues for Cross-domain Multi-hop API Calls and Their Solution Proposal](https://agntconmcpconeu26.sched.com/event/2RB9x/potential-issues-for-cross-domain-multi-hop-api-calls-and-their-solution-proposal-takashi-norimatsu-hitachi-ltd)  
**Speakers:** Takashi Norimatsu (Chief OSS Specialist, Hitachi, Ltd.)  
**Relevance Score:** `0.95`

## Essence

This talk addresses critical security and operational challenges arising from cross-domain, multi-hop API calls within the Model Context Protocol (MCP) ecosystem, specifically focusing on 'elicitation in URL mode' and 'token exchange.' The core problem lies in ensuring consistent user identity and authorization across disparate domains when an MCP server needs to access an external API, each requiring its own access token. Elicitation in URL mode risks user swapping, while token exchange can lead to information leaks and fraudulent token use. The proposed solutions aim to mitigate these vulnerabilities by establishing robust mechanisms for correlating user identities across different authorization servers, even when user identifiers vary between domains, thereby preventing unauthorized access and maintaining system integrity.

## Key Takeaways & Recommendations

- Implement robust mechanisms to correlate user identities across different authorization servers, even when user identifiers vary between domains.
- Carefully design external authorization servers to adhere to strong security practices, preventing well-known attacks that could bypass initial MCP-compliant authorization.
- Prioritize secure token exchange protocols to prevent information leaks, fraudulent access token use, and availability problems.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[security]]
- [[identity]]
