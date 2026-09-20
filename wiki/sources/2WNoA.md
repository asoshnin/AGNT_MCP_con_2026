---
id: "2WNoA"
title: "Evaluating Agents at Scale: From 50 Examples to a Production Flywheel"
speakers: ["Bauke Brenninkmeijer"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2WNoA/evaluating-agents-at-scale-from-50-examples-to-a-production-flywheel-bauke-brenninkmeijer-orqai"
concepts: ["evaluation", "orchestration", "tool-use"]
relevance_score: 0.95
relevance_rationale: "Directly addresses the core problem of evaluating LLM agents, a central theme for AGNTCon, and provides a scalable, rigorous framework for doing so, which is critical for production deployments."
resources:
---

# Evaluating Agents at Scale: From 50 Examples to a Production Flywheel

**Canonical Presentation on Sched:** [Evaluating Agents at Scale: From 50 Examples to a Production Flywheel](https://agntconmcpconeu26.sched.com/event/2WNoA/evaluating-agents-at-scale-from-50-examples-to-a-production-flywheel-bauke-brenninkmeijer-orqai)  
**Speakers:** Bauke Brenninkmeijer (AI Research Engineer, Orq.ai)  
**Relevance Score:** `0.95`

## Essence

The talk addresses the critical challenge of evaluating LLM agents at scale, moving beyond superficial single-shot LLM evaluations to a robust, continuous production flywheel. It emphasizes grading agents across three crucial dimensions: the final response, the execution trajectory (including tool calls), and any state changes, to catch subtle failures like fabricated tool use. The proposed lifecycle begins with bootstrapping evaluation from a small set of hand-reviewed examples, then rigorously aligning LLM-as-a-judge models to human judgment using statistical methods like Cohen's kappa. This process scales to continuous online evaluation, integrating with CI/CD pipelines for error analysis and prompt optimization driven by natural language feedback, ensuring agents perform reliably in production.

## Key Takeaways & Recommendations

- Evaluate agents across three dimensions: final response, trajectory, and state changes, not just the final output.
- Bootstrap evaluation with a small set (e.g., 50) of hand-reviewed examples when labels are scarce.
- Rigorously align LLM-as-a-judge models to human judgment using dev/test splits, inter-rater agreement, and Cohen's kappa.
- Integrate continuous online evaluation into CI pipelines for ongoing error analysis and prompt optimization.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[evaluation]]
- [[orchestration]]
- [[tool-use]]
