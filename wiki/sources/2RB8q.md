---
id: "2RB8q"
title: "A2A Goes Stable: What Changed, Why, and What's Next"
speakers: ["Sam Betts", "Kuba Herczy\u0144ski"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8q/a2a-goes-stable-what-changed-why-and-whats-next-sam-betts-cisco-systems-kuba-herczynski-google"
concepts: ["a2a", "security", "identity", "orchestration", "governance"]
relevance_score: 0.91
relevance_rationale: "High-relevance production case study on A2A Protocol v1.0 stabilization, covering security architecture (signed Agent Cards, OAuth hardening), enterprise multi-tenancy, and migration strategy from v0.3 — directly applicable to platform engineers building agent-to-agent communication systems."
resources:
  - url: "https://agent.example.com/v03"
    label: "A2A v0.3 Reference"
  - url: "https://agent.example.com/v1"
    label: "A2A v1.0 Reference"
---

# A2A Goes Stable: What Changed, Why, and What's Next

**Canonical Presentation on Sched:** [A2A Goes Stable: What Changed, Why, and What's Next](https://agntconmcpconeu26.sched.com/event/2RB8q/a2a-goes-stable-what-changed-why-and-whats-next-sam-betts-cisco-systems-kuba-herczynski-google)  
**Speakers:** Sam Betts (Engineering Technical Leader, Cisco Systems), Kuba Herczyński (Staff Software Engineer, Google)  
**Relevance Score:** `0.91`

## Essence

A2A Protocol v1.0 marks the transition from experimental agent-to-agent communication to a production-grade, Linux Foundation-governed standard. The core architectural shift addresses v0.3's trust-on-first-use Agent Card model, which was unacceptable for enterprise deployment. v1.0 establishes a single normative artifact (a2a.proto) as the universal protocol definition, decoupled from any specific transport. Three binding formats — JSON-RPC, HTTP+JSON, and gRPC — are formally specified with equivalence guarantees, enabling heterogeneous environments without stack lock-in. The web-aligned architecture allows A2A interactions to begin with a single HTTP request, leveraging existing load balancers, API gateways, WAFs, and tracing infrastructure, eliminating the need for specialized agent meshes. Delivery patterns support polling, streaming, and webhooks. Enterprise capabilities center on four pillars: Signed Agent Cards using JWS (RFC 7515) over RFC 8785 canonical forms, closing the trust gap at the discovery layer; multi-tenancy via URL sub-path routing, auth credentials, or opaque tenant fields in the Agent Card; modern OAuth flows (Device Code RFC 8628, PKCE RFC 7636) with Implicit and Password flows explicitly removed per OAuth 2.0 Security BCP; and a per-interface versioning strategy enabling progressive migration from v0.3 without forced cutover. Six official SDKs (Python, Go, Java, JavaScript, .NET, Rust) maintain backward compatibility while supporting v1.0 features. The governance model involves an eight-company steering committee with 150+ partner organizations, ensuring no single-vendor control.

## Key Takeaways & Recommendations

- Always verify JWS signatures (RFC 7515) on Agent Cards over RFC 8785 canonical form before any interaction — never trust-on-first-use. Verify identity before sending credentials, tasks, or any payload.
- Implement per-interface versioning to enable progressive migration from v0.3 to v1.0, allowing teams to upgrade interfaces independently rather than performing a forced cutover rewrite.
- Leverage existing web infrastructure (API gateways, WAFs, load balancers, tracing) for A2A deployments rather than deploying specialized agent meshes — the web-aligned architecture (JSON+HTTP, JSON-RPC, gRPC) is designed to work with what you already have.
- Explicitly disable legacy OAuth flows (Implicit and Password) and enforce modern flows: Device Code (RFC 8628) and PKCE (RFC 7636) to align with OAuth 2.0 Security BCP.
- Contribute to the A2A working group (github.com/a2aproject) to shape v1.1 priorities: bidirectional streaming support, .NET and Rust SDK parity, and custom protocol bindings that replace default transport while preserving A2A semantics.

## Production Gotchas & Failure Modes

- Lookalike Agent Cards in registries — without JWS signature verification, an attacker can register a card mimicking a legitimate agent, intercepting credentials and tasks before any interaction occurs.
- Stale cards with swapped auth endpoints — if an Agent Card is fetched once and cached indefinitely without re-verification, subsequent auth endpoint swaps go undetected, enabling credential interception and task redirection.
- Compromised discovery paths — the .well-known endpoint or registry serving Agent Cards becomes a single point of failure if not cryptographically verified at the discovery layer before any credentials or tasks are exchanged.

## Discovered Resources

- [A2A v0.3 Reference](https://agent.example.com/v03)
- [A2A v1.0 Reference](https://agent.example.com/v1)

## Related Concepts

- [[a2a]]
- [[security]]
- [[identity]]
- [[orchestration]]
- [[governance]]
