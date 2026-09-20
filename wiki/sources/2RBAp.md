---
id: "2RBAp"
title: "Agent-Smith: Never Send a Human To Do a Machine’s Job"
speakers: ["Glenn ten Cate", "Jorge Carvalho"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBAp/agent-smith-never-send-a-human-to-do-a-machines-job-glenn-ten-cate-the-linux-foundation-jorge-carvalho-nedap"
concepts: ["mcp", "security", "sandboxing", "orchestration", "tool-use", "evaluation"]
relevance_score: 0.98
relevance_rationale: "The talk directly addresses the core themes of AGNTCon and MCPCon by presenting a novel, open-source autonomous agent architecture for penetration testing, emphasizing security, sandboxing, tool-use, and the MCP paradigm for agent control and reliability."
resources:
  - url: "https://github.com/0x0pointer/agent-smith"
    label: "Agent-Smith GitHub Repository"
  - url: "https://docs.google.com/file/d/12l-RDEeEHO9jtxLh88qHjfvsl-za0zi6/preview"
    label: "Agent-Smith Presentation Slides (Preview 1)"
  - url: "https://nullpointer.studio"
    label: "Nullpointer Studio Website"
  - url: "https://docs.google.com/file/d/10shMqz4j2dqhImHnwe8S7vFHijBVZCmK/preview"
    label: "Agent-Smith Presentation Slides (Preview 2)"
---

# Agent-Smith: Never Send a Human To Do a Machine’s Job

**Canonical Presentation on Sched:** [Agent-Smith: Never Send a Human To Do a Machine’s Job](https://agntconmcpconeu26.sched.com/event/2RBAp/agent-smith-never-send-a-human-to-do-a-machines-job-glenn-ten-cate-the-linux-foundation-jorge-carvalho-nedap)  
**Speakers:** Glenn ten Cate (Senior Cybersecurity trainer, The Linux Foundation), Jorge Carvalho (Application Security Engineer, Nedap)  
**Relevance Score:** `0.98`

## Essence

Agent-Smith is an open-source autonomous penetration testing agent designed to scale security assessments beyond human capacity. Unlike traditional AI security agents that merely wrap fixed scripts, Agent-Smith inverts this paradigm: the LLM acts as the operator, reasoning about security methodology encoded as reusable skills. It autonomously investigates, chains tools within ephemeral Docker sandboxes, validates findings with evidence-binding gates, and determines its next action across diverse attack surfaces like web, cloud, and Active Directory. This architecture prioritizes model portability, server-side controls for cost and execution, and human-in-the-loop oversight, enabling the agent to progress from reconnaissance to a verified finding, reproducible PoC, remediation guidance, and even code patches without human intervention.

## Key Takeaways & Recommendations

- Encode security methodology as code, teaching the model how to think rather than hard-coding specific actions.
- Implement evidence-binding gates to ensure no claim is made without a verifiable artifact on disk, making 'lying' structurally impossible.
- Utilize server-side budgets and isolation, capping cost, execution time, and tool calls, with every tool running in a disposable container.
- Integrate a depth-enforcing watchdog component to supervise agent execution, catching stalls, shortcuts, and runaway processes.

## Discovered Resources

- [Agent-Smith GitHub Repository](https://github.com/0x0pointer/agent-smith)
- [Agent-Smith Presentation Slides (Preview 1)](https://docs.google.com/file/d/12l-RDEeEHO9jtxLh88qHjfvsl-za0zi6/preview)
- [Nullpointer Studio Website](https://nullpointer.studio)
- [Agent-Smith Presentation Slides (Preview 2)](https://docs.google.com/file/d/10shMqz4j2dqhImHnwe8S7vFHijBVZCmK/preview)

## Related Concepts

- [[mcp]]
- [[security]]
- [[sandboxing]]
- [[orchestration]]
- [[tool-use]]
- [[evaluation]]
