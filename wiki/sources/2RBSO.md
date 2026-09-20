---
id: "2RBSO"
title: "Sponsored Workshop: Total Recall: Agent Memory and Harness Engineering"
speakers: ["Ignacio Martinez"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBSO/sponsored-workshop-total-recall-agent-memory-and-harness-engineering-ignacio-martinez-oracle"
concepts: ["orchestration", "memory", "rag", "tool-use", "mcp"]
relevance_score: 0.95
relevance_rationale: "Directly addresses core AGNTCon themes of agent architecture, memory management, and harness engineering, with a focus on practical implementation and consolidation strategies."
resources:
  - url: "https://workshopwaitingroom.com"
    label: "Workshop Waiting Room"
  - url: "https://bit.ly/4xPIrH1"
    label: "Oracle AI Agent Memory Course"
  - url: "https://github.com/oracle-devrel/oracle-ai-developer-hub/"
    label: "Oracle AI Developer Hub GitHub"
---

# Sponsored Workshop: Total Recall: Agent Memory and Harness Engineering

**Canonical Presentation on Sched:** [Sponsored Workshop: Total Recall: Agent Memory and Harness Engineering](https://agntconmcpconeu26.sched.com/event/2RBSO/sponsored-workshop-total-recall-agent-memory-and-harness-engineering-ignacio-martinez-oracle)  
**Speakers:** Ignacio Martinez (AI Developer Advocate, Oracle)  
**Relevance Score:** `0.95`

## Essence

This workshop focuses on building robust autonomous agents by consolidating disparate components into a unified memory core, specifically leveraging Oracle's AI Database. The core technical insight is that by integrating vector stores, state management, rerankers, and memory layers directly within a single database kernel, developers can significantly reduce cognitive load and engineering complexity. This architecture, exemplified by the Oracle AI Agent Memory Package (OAMP), enables optionality in memory substrates and retrieval strategies without leaving the core, allowing agents to write and run their own automations more tractably. The approach emphasizes a single ACID boundary for all agent state, promoting a more cohesive and manageable agent harness.

## Key Takeaways & Recommendations

- Consolidate agent harness components (vector store, state, reranker, memory) onto a single, unified memory core to reduce cognitive load and improve tractability.
- Utilize a database kernel that supports in-database embeddings, rerankers, and various retrieval strategies to minimize data movement and simplify the architecture.
- Implement a robust memory package (like OAMP) that provides persistent memory, context compaction, and substrate-aware offloading.
- Leverage a state graph framework (e.g., LangGraph) with database-backed checkpoints for reliable agent orchestration.

## Discovered Resources

- [Workshop Waiting Room](https://workshopwaitingroom.com)
- [Oracle AI Agent Memory Course](https://bit.ly/4xPIrH1)
- [Oracle AI Developer Hub GitHub](https://github.com/oracle-devrel/oracle-ai-developer-hub/)

## Related Concepts

- [[orchestration]]
- [[memory]]
- [[rag]]
- [[tool-use]]
- [[mcp]]
