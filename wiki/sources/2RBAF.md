---
id: "2RBAF"
title: "I Was the Bottleneck, Not the Agent"
speakers: ["Vincent Ysmal"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBAF/i-was-the-bottleneck-not-the-agent-vincent-ysmal-datadog"
concepts: ["orchestration", "evaluation", "tool-use"]
relevance_score: 0.92
relevance_rationale: "Directly addresses the challenges and architectural solutions for scaling agentic workflows, focusing on human-agent interaction and validation, which is central to AGNTCon themes."
resources:
  - url: "https://sfeedback.com/Jv5gnu"
    label: "Talk Feedback Link"
---

# I Was the Bottleneck, Not the Agent

**Canonical Presentation on Sched:** [I Was the Bottleneck, Not the Agent](https://agntconmcpconeu26.sched.com/event/2RBAF/i-was-the-bottleneck-not-the-agent-vincent-ysmal-datadog)  
**Speakers:** Vincent Ysmal (Senior Software Engineer, Datadog)  
**Relevance Score:** `0.92`

## Essence

This talk addresses the critical bottleneck human developers become when orchestrating multiple AI agents in parallel coding sessions. The core problem is the human's inability to keep pace with agent output, leading to context switching overhead, manual testing, and extensive code reviews. The proposed solution redefines the workflow around the principle that agents must prove their own work. This involves agents autonomously deploying, running test suites, monitoring CI, and generating pull requests with sufficient evidence for confident human approval, shifting the human role from 'finishing the work' to 'believing the work'. The architecture emphasizes agent self-validation to scale agentic development effectively.

## Key Takeaways & Recommendations

- Design agents to autonomously deploy their changes.
- Equip agents to run their own comprehensive test suites.
- Integrate agents with CI/CD pipelines to monitor and fix failures.
- Structure agent-generated PRs with clear evidence to facilitate human review without line-by-line inspection.

## Discovered Resources

- [Talk Feedback Link](https://sfeedback.com/Jv5gnu)

## Related Concepts

- [[orchestration]]
- [[evaluation]]
- [[tool-use]]
