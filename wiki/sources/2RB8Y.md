---
id: "2RB8Y"
title: "Pull Requests Are Dead, Long Live Peer Review"
speakers: ["Dylan Ratcliffe"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8Y/pull-requests-are-dead-long-live-peer-review-dylan-ratcliffe-overmind"
concepts: ["mcp", "orchestration", "evaluation", "tool-use"]
relevance_score: 0.92
relevance_rationale: "Directly addresses the integration of AI agents into the software development lifecycle, focusing on the critical aspect of human-agent collaboration and the re-architecture of peer review processes, which is central to AGNTCon themes."
resources:
---

# Pull Requests Are Dead, Long Live Peer Review

**Canonical Presentation on Sched:** [Pull Requests Are Dead, Long Live Peer Review](https://agntconmcpconeu26.sched.com/event/2RB8Y/pull-requests-are-dead-long-live-peer-review-dylan-ratcliffe-overmind)  
**Speakers:** Dylan Ratcliffe (Founder & CEO, Overmind)  
**Relevance Score:** `0.92`

## Essence

The talk addresses the breakdown of traditional pull request-based peer review in AI-assisted development, where AI generates the majority of code. Overmind's solution shifts human review from the generated code diff to the initial 'plan' or intent, allowing engineers to focus on the strategic thinking before code generation. An in-house MCP server facilitates this plan review within the IDE. Post-generation, CI automatically compares the generated code against the approved plan, flagging only deviations for human re-review, thereby maintaining accountability and quality while significantly improving development velocity and engineer satisfaction by re-centering collaboration on intent rather than machine output.

## Key Takeaways & Recommendations

- Shift human review from code diffs to the initial development plan or intent.
- Implement automated deviation checking in CI to compare generated code against approved plans.
- Foster a culture where everyone operates as a team lead, encouraging ownership and strategic thinking.
- Radiate customer context across the entire team to inform agent-assisted development.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[evaluation]]
- [[tool-use]]
