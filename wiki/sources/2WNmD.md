---
id: "2WNmD"
title: "From Advisory to Autonomous: A Staged Model for Agent Adoption"
speakers: ["Milos Mandic"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2WNmD/from-advisory-to-autonomous-a-staged-model-for-agent-adoption-milos-mandic-fde-hub"
concepts: ["mcp", "evaluation", "orchestration"]
relevance_score: 0.95
relevance_rationale: "The talk directly addresses the practical challenges of deploying AI agents, focusing on human-agent collaboration and the critical role of trust in adoption, which is central to AGNTCon's themes. It provides a structured approach relevant to MCP for managing agent lifecycle and integration."
resources:
---

# From Advisory to Autonomous: A Staged Model for Agent Adoption

**Canonical Presentation on Sched:** [From Advisory to Autonomous: A Staged Model for Agent Adoption](https://agntconmcpconeu26.sched.com/event/2WNmD/from-advisory-to-autonomous-a-staged-model-for-agent-adoption-milos-mandic-fde-hub)  
**Speakers:** Milos Mandic (Founder & Editor, FDE Hub)  
**Relevance Score:** `0.95`

## Essence

Milos Mandic's talk addresses the critical 'trust gap' in AI agent adoption, where rapid development often outpaces human operator trust, hindering production deployment. He proposes a four-stage model for moving agents from advisory to full autonomy, emphasizing that trust must be earned, not assumed. The core insight is that probabilistic software, human intuition, fear of replacement, and the '100% illusion' create this gap, especially when agents fail silently on 'unknown unknowns' not covered by eval sets. The talk highlights that the cost of an error dictates the required evidence for each stage progression, advocating for a deliberate, staged approach to integrate agents into human-in-the-loop workflows, ensuring continuous validation and ownership of the agent's evolving knowledge base.

## Key Takeaways & Recommendations

- Plan for both build time and trust-building time, recognizing that the latter often takes significantly longer.
- Assess the cost of a mistake early in the project, as this directly determines the pace at which an agent can progress through autonomy stages.
- Implement mechanisms for humans to continuously validate and confirm changes to an agent's 'beliefs' or rules, treating these changes with the same rigor as initial deployment.
- Design agent systems to explicitly handle 'unknown unknowns' and provide visibility into cases where human intervention is needed, rather than silently proceeding with potentially incorrect actions.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[evaluation]]
- [[orchestration]]
