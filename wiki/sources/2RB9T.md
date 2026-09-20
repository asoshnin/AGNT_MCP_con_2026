---
id: "2RB9T"
title: "Distributed Mess: A Production Guide To Multi-Agent Failures"
speakers: ["Huong Vu"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9T/distributed-mess-a-production-guide-to-multi-agent-failures-huong-vu-databricks"
concepts: ["mcp", "orchestration", "evaluation", "observability"]
relevance_score: 0.98
relevance_rationale: "Directly addresses critical failure modes and architectural considerations in multi-agent systems, particularly concerning inter-agent communication and context management, which are central to MCP principles. The focus on tracing and governance is highly relevant to building robust agentic systems."
resources:
  - url: "https://docs.databricks.com/aws/en/mlflow/"
    label: "MLflow Documentation"
---

# Distributed Mess: A Production Guide To Multi-Agent Failures

**Canonical Presentation on Sched:** [Distributed Mess: A Production Guide To Multi-Agent Failures](https://agntconmcpconeu26.sched.com/event/2RB9T/distributed-mess-a-production-guide-to-multi-agent-failures-huong-vu-databricks)  
**Speakers:** Huong Vu (Sr. Forward Deployed Engineer, Databricks)  
**Relevance Score:** `0.98`

## Essence

This talk addresses the critical, often overlooked, failure mode in multi-agent systems: 'polluted context' arising from flawed handoffs between agents. Unlike single-agent failures, these issues stem from a supervisor agent passing incorrect tool outputs, misrouted state, or plausible hallucinations downstream, leading subsequent agents to confidently operate on a corrupted foundation. The core insight is that traditional end-to-end testing is insufficient because the final output can still appear reasonable despite internal corruption. The solution involves robust tracing across agent boundaries, distinguishing error types (model, routing, context corruption), and evaluating the coordination layer, not just individual agent outputs, to build truly trustworthy agentic systems.

## Key Takeaways & Recommendations

- Instrument your multi-agent system with MLflow for comprehensive tracing, specifically using `mlflow.<flavor>.autolog()`.
- Apply the 'Four Dimensions of Governance' (Operational Health, Cost Management, Compliance and Audit, Quality and Value) across your multi-agent operations.
- Shift evaluation focus from solely end-to-end outputs to include coordination (conflict resolution) and agent handoff (information transfer).
- Implement guardrails like circuit breakers, retries, fallbacks, policy gates, and automated evaluation to enforce stability and quality.

## Discovered Resources

- [MLflow Documentation](https://docs.databricks.com/aws/en/mlflow/)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[evaluation]]
- [[observability]]
