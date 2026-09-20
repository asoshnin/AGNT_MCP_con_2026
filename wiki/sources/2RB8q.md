---
id: "2RB8q"
title: "A2A Goes Stable: What Changed, Why, and What's Next"
speakers: ["Sam Betts", "Kuba Herczy\u0144ski"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8q/a2a-goes-stable-what-changed-why-and-whats-next-sam-betts-cisco-systems-kuba-herczynski-google"
concepts: ["orchestration", "security", "mcp", "evaluation"]
relevance_score: 0.98
relevance_rationale: "Directly addresses the stabilization and future of agent-to-agent communication, a core theme of AGNTCon, with explicit mentions of MCP and architectural considerations for agent systems."
resources:
  - url: "https://agent.example.com/v03"
    label: "Example Agent v0.3"
  - url: "https://agent.example.com/v1"
    label: "Example Agent v1"
---

# A2A Goes Stable: What Changed, Why, and What's Next

**Canonical Presentation on Sched:** [A2A Goes Stable: What Changed, Why, and What's Next](https://agntconmcpconeu26.sched.com/event/2RB8q/a2a-goes-stable-what-changed-why-and-whats-next-sam-betts-cisco-systems-kuba-herczynski-google)  
**Speakers:** Sam Betts (Engineering Technical Leader, Cisco Systems), Kuba Herczyński (Staff Software Engineer, Google)  
**Relevance Score:** `0.98`

## Essence

The A2A Protocol v1.0 marks a critical transition from an experimental agent-to-agent communication standard to a stable, production-ready foundation. This release prioritizes maturity and enterprise capabilities, introducing features like signed Agent Cards, multi-tenancy, and modern OAuth flows, all built on a web-aligned architecture. Key changes include a single normative source of truth (a2a.proto), explicit compatibility rules with per-interface versioning, and formally specified bindings for JSON-RPC, HTTP+JSON, and gRPC. The protocol maintains backward compatibility with v0.3 through official SDKs, enabling progressive migration rather than forced cutovers, and supports extensibility via custom protocol bindings while preserving core semantics. This stability allows organizations to confidently commit to A2A for robust inter-agent communication.

## Key Takeaways & Recommendations

- If building an agent (not just a long-running tool), expose it over A2A.
- Utilize the official A2A SDKs for v1.0, noting that migration from v0.3 is progressive.
- Contribute to the A2A working group on GitHub to help shape future protocol versions and tooling.
- Explore custom protocol bindings to replace default transports while maintaining A2A semantics.

## Discovered Resources

- [Example Agent v0.3](https://agent.example.com/v03)
- [Example Agent v1](https://agent.example.com/v1)

## Related Concepts

- [[orchestration]]
- [[security]]
- [[mcp]]
- [[evaluation]]
