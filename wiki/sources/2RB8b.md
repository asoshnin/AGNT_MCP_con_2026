---
id: "2RB8b"
title: "Call Now, Fetch Later: Durable MCP Tasks on an Event Log"
speakers: ["Jeremy Frenay"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8b/call-now-fetch-later-durable-mcp-tasks-on-an-event-log-jeremy-frenay-lenses"
concepts: ["mcp", "orchestration", "observability"]
relevance_score: 0.95
relevance_rationale: "Directly addresses the implementation challenges and architectural solutions for MCP's new asynchronous Tasks primitive, which is central to agentic orchestration and tool-use."
resources:
---

# Call Now, Fetch Later: Durable MCP Tasks on an Event Log

**Canonical Presentation on Sched:** [Call Now, Fetch Later: Durable MCP Tasks on an Event Log](https://agntconmcpconeu26.sched.com/event/2RB8b/call-now-fetch-later-durable-mcp-tasks-on-an-event-log-jeremy-frenay-lenses)  
**Speakers:** Jeremy Frenay (Field CTO, Lenses)  
**Relevance Score:** `0.95`

## Essence

The MCP's new asynchronous Tasks primitive, designed for long-running tool calls, presents significant implementation challenges regarding durability, state management, and exactly-once delivery. This talk proposes an append-only event log as a robust, vendor-neutral backend for these tasks. By modeling tasks as state machines where transitions are logged as events, the system achieves durability through log replay for recovery and enables stateless servers. This architecture addresses critical production failure modes like orphaned tasks and duplicate side effects, while acknowledging current MCP roadmap gaps in retry and expiry mechanisms.

## Key Takeaways & Recommendations

- Implement MCP Tasks using an append-only event log to manage task state and ensure durability.
- Model tasks as state machines, where creation, status updates, and completion are recorded as events in the log.
- Leverage log replay for recovery, enabling stateless task servers and resilience against restarts.
- Design for exactly-once delivery semantics to prevent duplicate side effects, especially for critical operations.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[observability]]
