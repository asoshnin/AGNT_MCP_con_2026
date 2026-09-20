---
id: "2RB9f"
title: "Verify, Abstain, or Amplify: A Field Guide To Confidently-Wrong Agents"
speakers: ["Michal Orzechowski"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9f/verify-abstain-or-amplify-a-field-guide-to-confidently-wrong-agents-michal-orzechowski-sano-centre-for-computational-personalised-medicine"
concepts: ["evaluation", "orchestration", "security", "mcp"]
relevance_score: 0.95
relevance_rationale: "Directly addresses the critical problem of agent reliability and correctness, offering architectural strategies for managing confidently-wrong agents, which is central to building robust multi-agent systems and ensuring operational integrity."
resources:
---

# Verify, Abstain, or Amplify: A Field Guide To Confidently-Wrong Agents

**Canonical Presentation on Sched:** [Verify, Abstain, or Amplify: A Field Guide To Confidently-Wrong Agents](https://agntconmcpconeu26.sched.com/event/2RB9f/verify-abstain-or-amplify-a-field-guide-to-confidently-wrong-agents-michal-orzechowski-sano-centre-for-computational-personalised-medicine)  
**Speakers:** Michal Orzechowski (Agentic AI & Cloud Architect, Sano – Centre for Computational Personalised Medicine)  
**Relevance Score:** `0.95`

## Essence

This talk addresses the critical challenge of 'confidently wrong' agents, where traditional evaluation methods like passing tests fail to guarantee correctness, especially outside an operator's domain expertise. The core insight is that agents often produce plausible but incorrect outputs because there's no reliable oracle to verify against. Orzechowski proposes a 'field guide' with three strategies: 'Verify' for deterministic checks on the answer (not just tool calls) within a robust harness, 'Abstain' when verification is impossible, prompting the agent to flag uncertainty for human review, and 'Amplify' for subjective tasks where novelty is desired, requiring human judgment to push beyond average outputs. The approach emphasizes shifting decision-making from human oversight of every agent action to strategic intervention points based on answer verifiability and task nature.

## Key Takeaways & Recommendations

- Implement robust, external oracles within the agent harness to verify answers, not just tool call success, ensuring the agent cannot manipulate these checks.
- Design agents to 'abstain' and escalate unverified or uncertain outputs to human experts, providing a clear channel for these questions.
- For creative or subjective tasks, explicitly 'amplify' novel outputs by involving human judgment, rather than letting agents converge to average solutions.
- Protect the 'main' branch or critical paths with gates that the agent cannot directly influence, ensuring all changes are validated by independent mechanisms or domain-specific oracles.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[evaluation]]
- [[orchestration]]
- [[security]]
- [[mcp]]
