---
id: "2WF5u"
title: "Your Agents Need a Router: One Integration for Every Model and Tool"
speakers: ["Ignasi Barrera"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2WF5u/your-agents-need-a-router-one-integration-for-every-model-and-tool-ignasi-barrera-tetrateio"
concepts: ["mcp", "security", "agent-gateway", "orchestration", "observability"]
relevance_score: 0.92
relevance_rationale: "High‑relevance production case study on unifying model and tool integration via a declarative AI gateway, covering routing, spend control, and secure MCP tool exposure."
resources:
  - url: "https://router.example/v1"
    label: "Router Example Endpoint"
  - url: "https://github.com/theagentrouter/agent-router"
    label: "Official Implementation"
---

# Your Agents Need a Router: One Integration for Every Model and Tool

**Canonical Presentation on Sched:** [Your Agents Need a Router: One Integration for Every Model and Tool](https://agntconmcpconeu26.sched.com/event/2WF5u/your-agents-need-a-router-one-integration-for-every-model-and-tool-ignasi-barrera-tetrateio)  
**Speakers:** Ignasi Barrera (Founding Engineer, Tetrate.io)  
**Relevance Score:** `0.92`

## Essence

Agent Router is an open‑source, Envoy‑based AI gateway that collapses multi‑provider model and tool integration into a single, declarative API. By exposing an OpenAI‑compatible endpoint, it lets agents request logical model names (e.g., “claude‑4‑sonnet”) without embedding provider SDKs, credentials, or retry logic. The router translates these logical names to provider‑specific identifiers via `modelNameOverride` and supports traffic‑splitting or failover using weighted priorities and Envoy‑driven retry policies. A `BackendTrafficPolicy` defines retry triggers (connect failures, 5xx) and limits, while `AIGatewayRoute` resources declare routes, backends, and quotas in Kubernetes custom resources. Spend control is achieved with `QuotaPolicy` objects that attach CEL‑evaluated token‑cost expressions to per‑model buckets, allowing per‑tenant or per‑team limits and shadow‑mode evaluation before enforcement. The MCP gateway aggregates disparate MCP servers behind a single endpoint, applying `toolSelector` filters, JWT‑based authorization, and CEL expressions to restrict which tools each agent can invoke. Operational maturity follows a three‑step path: local experimentation with `aigw run`, safe policy iteration using telemetry, and production deployment via Kubernetes Gateway API resources. Extensibility is inherent because the router sits on Envoy, enabling custom policies and extensions without waiting for upstream releases.

## Key Takeaways & Recommendations

- Virtualize all model names behind logical identifiers and keep provider credentials, API keys, and retry logic inside the router’s declarative configuration.
- Iterate on routing and quota policies using shadow mode and Envoy telemetry before enforcing them in production to avoid surprise throttling or routing failures.
- Apply fine‑grained spend controls with CEL expressions that reflect actual token costs, and isolate buckets by tenant or team using request headers.
- Secure MCP tool exposure with JWT scopes and CEL‑based filters, and regularly audit `toolSelector` rules to ensure least‑privilege access.
- Leverage the Envoy data‑plane metrics and tracing to continuously tune retry, circuit‑breaker, and failover policies for optimal availability.

## Production Gotchas & Failure Modes

- Mis‑aligned `modelNameOverride` values cause routing to the wrong provider, breaking inference and leading to unexpected errors.
- Incorrect quota or rate‑limit configuration (e.g., overly restrictive CEL cost expressions) can silently block legitimate traffic or allow runaway spend.
- Overly permissive MCP `toolSelector` or missing JWT scopes expose unauthorized tools, creating security gaps in the agent’s capability set.

## Discovered Resources

- [Router Example Endpoint](https://router.example/v1)
- [Official Implementation](https://github.com/theagentrouter/agent-router)

## Related Concepts

- [[mcp]]
- [[security]]
- [[agent-gateway]]
- [[orchestration]]
- [[observability]]
