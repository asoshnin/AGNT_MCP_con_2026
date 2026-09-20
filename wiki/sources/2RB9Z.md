---
id: "2RB9Z"
title: "MCP Borrowed LSP's Design. It Skipped LSP's Lesson"
speakers: ["Gorkem Ercan"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9Z/mcp-borrowed-lsps-design-it-skipped-lsps-lesson-gorkem-ercan-jozu"
concepts: ["mcp", "security", "sandboxing", "orchestration"]
relevance_score: 0.98
relevance_rationale: "Directly addresses a critical security vulnerability in MCP server packaging and trust, proposing a concrete architectural solution using established cloud-native practices. This is highly relevant to AGNTCon and MCPCon attendees concerned with agent security and robust deployment."
resources:
---

# MCP Borrowed LSP's Design. It Skipped LSP's Lesson

**Canonical Presentation on Sched:** [MCP Borrowed LSP's Design. It Skipped LSP's Lesson](https://agntconmcpconeu26.sched.com/event/2RB9Z/mcp-borrowed-lsps-design-it-skipped-lsps-lesson-gorkem-ercan-jozu)  
**Speakers:** Gorkem Ercan (CTO, Jozu)  
**Relevance Score:** `0.98`

## Essence

The talk highlights that the Multi-Agent Communication Protocol (MCP) has adopted the design principles of the Language Server Protocol (LSP) but critically overlooked LSP's decade-long struggle with packaging and trust. While LSP standardized communication, it failed to standardize server packaging and verification, leading to fragmented distribution and belated, vendor-specific signing. MCP, by repeating this oversight, faces a significantly larger security threat, as MCP servers execute arbitrary code with access to sensitive credentials and local systems. The core insight is that MCP can leverage existing Open Container Initiative (OCI) artifact packaging, signing, attestation, and policy tooling to establish open, registry-neutral provenance and verifiable trust before server execution, rather than reinventing a fragmented system.

## Key Takeaways & Recommendations

- Package MCP servers as OCI artifacts to inherit existing signing, attestation, and policy tooling from the container ecosystem.
- Ensure provenance is portable and verifiable *before* an agent loads and executes an MCP server.
- Avoid vendor-specific signing solutions, as they do not foster open trust across the ecosystem.
- Recognize that packaging is an integral part of the security model for MCP servers.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[security]]
- [[sandboxing]]
- [[orchestration]]
