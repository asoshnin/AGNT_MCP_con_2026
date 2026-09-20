---
id: "2RBAX"
title: "Testing Agents and Their Tools: Offline Evaluation, Synthetic Tasks, and A/B Experiments"
speakers: ["Ksenia Bobrova", "I'm currently focusing on building AI agents and tooling around it."]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBAX/testing-agents-and-their-tools-offline-evaluation-synthetic-tasks-and-ab-experiments-ksenia-bobrova-github"
concepts: ["mcp", "evaluation", "orchestration", "tool-use"]
relevance_score: 0.95
relevance_rationale: "Directly addresses the critical challenge of testing and evaluating AI agents and their tool-use capabilities, including multi-tool orchestration and A/B experimentation in production, which is central to AGNTCon and MCPCon themes."
resources:
  - url: "https://gh.io/AA13jm01"
    label: "GitHub Resource 1"
  - url: "https://gh.io/AA13hgua"
    label: "GitHub Resource 2"
---

# Testing Agents and Their Tools: Offline Evaluation, Synthetic Tasks, and A/B Experiments

**Canonical Presentation on Sched:** [Testing Agents and Their Tools: Offline Evaluation, Synthetic Tasks, and A/B Experiments](https://agntconmcpconeu26.sched.com/event/2RBAX/testing-agents-and-their-tools-offline-evaluation-synthetic-tasks-and-ab-experiments-ksenia-bobrova-github)  
**Speakers:** Ksenia Bobrova (Senior Software Engineer, GitHub), I'm currently focusing on building AI agents and tooling around it.  
**Relevance Score:** `0.95`

## Essence

This talk presents a robust, three-layered evaluation strategy for AI agents and their tools, crucial for operating across diverse LLM providers and runtimes. The methodology begins with offline evaluation, focusing on designing benchmark suites with curated requests to assess tool selection precision, recall, F1 scores, and argument hallucination rates. This is complemented by end-to-end benchmarks that test multi-tool flows, catching integration regressions missed by single-tool evaluations. Finally, the strategy incorporates production A/B experiments, detailing challenges like caching bugs and data skew, and providing a framework for deciding on staged rollouts. This comprehensive approach forms a testing pyramid, ensuring safe and reliable deployment of changes to MCP servers and agents across various model providers.

## Key Takeaways & Recommendations

- Implement a three-layered evaluation strategy: offline evaluation, end-to-end benchmarks, and production A/B experiments.
- Design offline benchmark suites with curated requests, expected tool selections, and arguments to compute precision, recall, F1 scores, and argument hallucination rates.
- Utilize end-to-end benchmarks to test multi-tool flows and catch integration regressions that single-tool evaluations might miss.
- Employ triggered analysis in online A/B experiments to reduce signal dilution, while being mindful of potential sample size reduction and data exclusion.

## Discovered Resources

- [GitHub Resource 1](https://gh.io/AA13jm01)
- [GitHub Resource 2](https://gh.io/AA13hgua)

## Related Concepts

- [[mcp]]
- [[evaluation]]
- [[orchestration]]
- [[tool-use]]
