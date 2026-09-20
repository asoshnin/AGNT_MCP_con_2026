---
id: "2RB9l"
title: "What a Year of Breaking MCP Tells Builders: Protocol Gaps and What Ships Next"
speakers: ["Amine Raji"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9l/what-a-year-of-breaking-mcp-tells-builders-protocol-gaps-and-what-ships-next-amine-raji-molntek-ab"
concepts: ["mcp", "security", "sandboxing", "identity", "orchestration"]
relevance_score: 0.98
relevance_rationale: "Directly addresses critical security vulnerabilities and protocol gaps in Model Context Protocol (MCP) deployments, offering concrete architectural recommendations for builders. This is central to AGNTCon + MCPCon themes."
resources:
  - url: "https://github.com/aminrj-labs/mcp-attack-labs"
    label: "mcp-attack-labs GitHub Repository"
---

# What a Year of Breaking MCP Tells Builders: Protocol Gaps and What Ships Next

**Canonical Presentation on Sched:** [What a Year of Breaking MCP Tells Builders: Protocol Gaps and What Ships Next](https://agntconmcpconeu26.sched.com/event/2RB9l/what-a-year-of-breaking-mcp-tells-builders-protocol-gaps-and-what-ships-next-amine-raji-molntek-ab)  
**Speakers:** Amine Raji (AI Security Lead, Molntek)  
**Relevance Score:** `0.98`

## Essence

Amine Raji's talk dissects critical security vulnerabilities within Model Context Protocol (MCP) deployments, revealing a pervasive issue where trust checks rely on unverified string comparisons, leading to an 85% attack success rate. The core problem stems from a 'flat namespace' in SDKs and protocol specifications that acknowledge trust boundaries but fail to enforce them, enabling attack classes like tool description poisoning and cross-server shadowing. Raji argues that model choice is not a sufficient control; instead, structural protocol changes are required to establish robust identity and authentication mechanisms. The presentation culminates in concrete JSON-RPC schema diffs proposing protocol enhancements to close these gaps, emphasizing that more capable models are paradoxically more susceptible to poisoned instructions.

## Key Takeaways & Recommendations

- Verify the publisher before verifying the content in MCP interactions.
- Authenticate inbound requests separately from downstream communications.
- Snapshot the definition surface of MCP configurations and block on any detected drift.
- Implement structural protocol changes rather than relying solely on model-side alignment for security.

## Discovered Resources

- [mcp-attack-labs GitHub Repository](https://github.com/aminrj-labs/mcp-attack-labs)

## Related Concepts

- [[mcp]]
- [[security]]
- [[sandboxing]]
- [[identity]]
- [[orchestration]]
