---
id: "2RB8Y"
title: "Pull Requests Are Dead, Long Live Peer Review"
speakers: ["Dylan Ratcliffe"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8Y/pull-requests-are-dead-long-live-peer-review-dylan-ratcliffe-overmind"
concepts: ["mcp", "orchestration", "agent-gateway", "governance"]
relevance_score: 0.91
relevance_rationale: "High-relevance production case study on rearchitecting the SDLC loop for AI-assisted development, with concrete MCP tooling, metrics, and cultural patterns."
resources:
  - url: "https://until.dev"
    label: "Official Implementation"
---

# Pull Requests Are Dead, Long Live Peer Review

**Canonical Presentation on Sched:** [Pull Requests Are Dead, Long Live Peer Review](https://agntconmcpconeu26.sched.com/event/2RB8Y/pull-requests-are-dead-long-live-peer-review-dylan-ratcliffe-overmind)  
**Speakers:** Dylan Ratcliffe (Founder & CEO, Overmind)  
**Relevance Score:** `0.91`

## Essence

When AI generates 80–90% of a team's code, traditional pull-request review collapses: reviewers audit machine-produced diffs instead of collaborating with peers, destroying accountability and morale. Ratcliffe's architecture replaces diff-centric review with plan-centric review. The critical shift is moving human attention left—engineers review the intent and trade-off decisions written before any code is generated, then an agent fills in the implementation. The core loop pattern is an `until` loop (not `do...while`): the agent researches, writes a plan with human input, then implements repeatedly until it matches the approved plan. This inverts the control flow—decisions happen once up front, and the agent self-checks against the plan. An in-house MCP server integrates plan review directly into the IDE, and every PR triggers automated deviation-checking against the approved plan; only deviations route back to the original reviewer. Production metrics from a two-week trial on the same team: 3.2× issues completed, 3.4× commits, lead time dropped from 3.2 days to 1.3 days (−59%), and engineer efficiency rose from 11% to 63%. The cultural bets are equally architectural: everyone operates as a team lead, no questions until working code exists, and customer context is radiated to the whole team rather than siloed in PR comments.

## Key Takeaways & Recommendations

- Adopt the until-loop pattern: define the acceptance condition (plan match) before the agent implements, and automate the match-check so only deviations reach humans.
- Build an MCP server for plan review that integrates into the IDE, ensuring human intent is captured and approved before any code generation begins.
- Instrument PRs with automated deviation detection against the approved plan, routing only non-matching diffs back to the original reviewer to preserve review bandwidth.
- Measure lead time and engineer efficiency (attention-to-working-code ratio), not just throughput metrics like commits or issues closed.
- Radiate customer context to the full team via shared artifacts so that plan-level decisions reflect real user needs, not just technical correctness.

## Production Gotchas & Failure Modes

- Vague or underspecified plans give the agent too much implementation latitude, causing silent deviations that automated checks miss because the plan itself lacks sufficient constraint surface.
- The MCP server for IDE plan review can become a synchronous bottleneck if plan-review latency exceeds the agent's iteration cycle, stalling the until-loop.
- Assuming 'everyone operates as a team lead' without prior context-radiation practices leads to conflicting decisions and plan drift across parallel agent instances.

## Discovered Resources

- [Official Implementation](https://until.dev)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[agent-gateway]]
- [[governance]]
