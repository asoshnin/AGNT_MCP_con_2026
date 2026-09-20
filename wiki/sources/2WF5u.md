---
id: "2WF5u"
title: "Your Agents Need a Router: One Integration for Every Model and Tool"
speakers: ["Ignasi Barrera"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2WF5u/your-agents-need-a-router-one-integration-for-every-model-and-tool-ignasi-barrera-tetrateio"
concepts: ["orchestration", "mcp", "security", "observability", "tool-use"]
relevance_score: 0.98
relevance_rationale: "Directly addresses the core challenges of integrating and managing multiple models and MCP tools for agentic systems, providing a concrete architectural solution (Agent Router) that aligns with AGNTCon's focus on agent infrastructure and MCPCon's emphasis on multi-cloud/provider strategies."
resources:
  - url: "https://router.example/v1"
    label: "Example Router API Endpoint"
  - url: "https://github.com/theagentrouter/agent-router"
    label: "Agent Router GitHub Repository"
---

# Your Agents Need a Router: One Integration for Every Model and Tool

**Canonical Presentation on Sched:** [Your Agents Need a Router: One Integration for Every Model and Tool](https://agntconmcpconeu26.sched.com/event/2WF5u/your-agents-need-a-router-one-integration-for-every-model-and-tool-ignasi-barrera-tetrateio)  
**Speakers:** Ignasi Barrera (Founding Engineer, Tetrate.io)  
**Relevance Score:** `0.98`

## Essence

The Agent Router addresses the growing complexity of integrating multiple LLM providers and MCP tools into agentic applications. It centralizes traffic management, policy enforcement, and operational concerns into a single, declarative API layer, abstracting away provider-specific SDKs, credentials, and fallback logic from the agent's core reasoning. By acting as an OpenAI-compatible proxy, the router enables agents to request logical models, while the platform handles dynamic routing, failover, cost attribution, and tool access control. This architecture shifts integration glue out of application code, allowing agents to focus purely on their intended tasks and providing a robust, observable, and extensible foundation for production-grade agent deployments.

## Key Takeaways & Recommendations

- Keep agent application code focused on reasoning, offloading integration complexities like credentials, retries, and token management to a router.
- Declare routing, retry behavior, token budgets, tool exposure, and credentials in a platform layer, external to the agent's application code.
- Utilize the router's model virtualization to separate logical model names requested by agents from provider-specific model identifiers, enabling flexible traffic patterns like weighted distribution or priority-based failover.
- Leverage Envoy's extensibility (WebAssembly, Dynamic Modules, External Processing) to implement custom policies or integrate new AI protocols not yet supported by the router's core.

## Discovered Resources

- [Example Router API Endpoint](https://router.example/v1)
- [Agent Router GitHub Repository](https://github.com/theagentrouter/agent-router)

## Related Concepts

- [[orchestration]]
- [[mcp]]
- [[security]]
- [[observability]]
- [[tool-use]]
