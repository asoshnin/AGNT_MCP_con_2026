---
id: "2RB9K"
title: "What Networking Got Right That Agentic AI Risks Getting Wrong: The Case for an Agent Control Plane"
speakers: ["Parisa Foroughi"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9K/what-networking-got-right-that-agentic-ai-risks-getting-wrong-the-case-for-an-agent-control-plane-parisa-foroughi-nokia"
concepts: ["mcp", "security", "sandboxing", "orchestration", "identity"]
relevance_score: 0.98
relevance_rationale: "Directly addresses a critical security and orchestration challenge in agentic AI by proposing a novel architectural pattern (Agent Control Plane) inspired by networking principles, which is highly relevant to both MCP and AGNTCon themes."
resources:
  - url: "https://www.linkedin.com/in/parisa-foroughi/"
    label: "Parisa Foroughi LinkedIn"
  - url: "https://agntconmcpconeu26.sched.com/user/25690998"
    label: "Parisa Foroughi Sched Profile"
---

# What Networking Got Right That Agentic AI Risks Getting Wrong: The Case for an Agent Control Plane

**Canonical Presentation on Sched:** [What Networking Got Right That Agentic AI Risks Getting Wrong: The Case for an Agent Control Plane](https://agntconmcpconeu26.sched.com/event/2RB9K/what-networking-got-right-that-agentic-ai-risks-getting-wrong-the-case-for-an-agent-control-plane-parisa-foroughi-nokia)  
**Speakers:** Parisa Foroughi (Senior research specialist, Nokia)  
**Relevance Score:** `0.98`

## Essence

This talk argues for an 'Agent Control Plane' to address the conflation of task execution and policy enforcement in current agent orchestration frameworks, drawing parallels from inter-domain routing in networking. It proposes separating the control layer, external to the agent, to perform authority checks and policy enforcement at defined domain boundaries. The core insight is that agent interoperability requires standardizing the semantics of boundary crossings, not internal agent policies. This is achieved through a semantic model built on five invariants, introducing runtime artifacts like the Agent Control Envelope (ACE) for authorization and Agent Activity Envelope (AAE) for behavioral constraints, ensuring trust without inspecting internal agent behavior or payload content.

## Key Takeaways & Recommendations

- Standardize the semantics of boundary crossings for agent interactions, rather than attempting to standardize internal agent policies or execution logic.
- Implement an external Agent Control Plane that operates at domain boundaries to enforce policy and authority, independent of individual agent logic.
- Define 'Agent Control Domains' (ACDs) as the primary unit of inter-domain control, analogous to Autonomous Systems in networking, to manage authority and delegation.
- Utilize 'crossing classes' as permission units, allowing domains to declare what types of work they will transit, enabling refusal by class before agent identification.

## Discovered Resources

- [Parisa Foroughi LinkedIn](https://www.linkedin.com/in/parisa-foroughi/)
- [Parisa Foroughi Sched Profile](https://agntconmcpconeu26.sched.com/user/25690998)

## Related Concepts

- [[mcp]]
- [[security]]
- [[sandboxing]]
- [[orchestration]]
- [[identity]]
