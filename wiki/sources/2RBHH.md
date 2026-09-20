---
id: "2RBHH"
title: "Keynote: Reactive Agents: Your Agent Doesn't Need to Be Always On"
speakers: ["Clare Liguori"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBHH/keynote-reactive-agents-your-agent-doesnt-need-to-be-always-on-clare-liguori-mcp-core-maintainer-senior-principal-engineer-aws"
concepts: ["mcp", "orchestration", "observability"]
relevance_score: 0.95
relevance_rationale: "Directly addresses a core architectural and operational challenge for agents, with explicit mention of MCP's role in enabling this paradigm."
resources:
---

# Keynote: Reactive Agents: Your Agent Doesn't Need to Be Always On

**Canonical Presentation on Sched:** [Keynote: Reactive Agents: Your Agent Doesn't Need to Be Always On](https://agntconmcpconeu26.sched.com/event/2RBHH/keynote-reactive-agents-your-agent-doesnt-need-to-be-always-on-clare-liguori-mcp-core-maintainer-senior-principal-engineer-aws)  
**Speakers:** Clare Liguori (MCP Core Maintainer & Senior Principal Engineer, AWS)  
**Relevance Score:** `0.95`

## Essence

Clare Liguori's keynote introduces the concept of 'reactive agents' to address the inefficiency of always-on agent runtimes. Traditional agents often maintain persistent processes, consuming resources while idly awaiting external events or long-duration tasks. A reactive agent, in contrast, only materializes as a running process when actively engaged in computation. During quiescent periods, its state is persisted to a database or file system, effectively 'sleeping' until an external event triggers its reactivation. This paradigm shift, which MCP is evolving to support, aims to drastically reduce operational costs and resource consumption by aligning agent execution with actual workload demands, rather than continuous availability.

## Key Takeaways & Recommendations

- Design agents to be event-driven, only activating when an external trigger necessitates action.
- Implement state persistence mechanisms (e.g., database rows, file storage) for agents during idle periods.
- Leverage evolving MCP capabilities to enable and manage reactive agent lifecycles.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[observability]]
