---
id: "2RBAa"
title: "Workshop: Harness Engineering: Building the System Around Your AI Coding Agent"
speakers: ["Ji Darwish"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBAa/workshop-harness-engineering-building-the-system-around-your-ai-coding-agent-ji-darwish-xomnia"
concepts: ["orchestration", "security", "evaluation", "observability", "tool-use"]
relevance_score: 0.95
relevance_rationale: "Directly addresses the engineering challenges and architectural considerations for building robust and secure systems around AI coding agents, which is central to AGNTCon and MCPCon themes."
resources:
  - url: "http://agents.md"
    label: "Agents.md"
  - url: "https://testomat.io/blog/mastering-bdd-tips-tricks-and-best-practices-for-setting-up-a-testing-framework/"
    label: "Mastering BDD"
  - url: "https://www.ramotion.com/blog/tdd-vs-bdd/"
    label: "TDD vs BDD"
  - url: "https://github.com/JiDarwish/outer-harness-workshop"
    label: "Outer Harness Workshop GitHub Repo"
---

# Workshop: Harness Engineering: Building the System Around Your AI Coding Agent

**Canonical Presentation on Sched:** [Workshop: Harness Engineering: Building the System Around Your AI Coding Agent](https://agntconmcpconeu26.sched.com/event/2RBAa/workshop-harness-engineering-building-the-system-around-your-ai-coding-agent-ji-darwish-xomnia)  
**Speakers:** Ji Darwish (Data Platform Engineer, Xomnia)  
**Relevance Score:** `0.95`

## Essence

This workshop demystifies AI coding agents by focusing on 'harness engineering' – the critical system built around a simple core loop of message-parse-execute-feedback. It emphasizes that the 'magic' of reliable agents comes from external engineering layers managing context, permissions, observability, and safety, rather than an exotic internal model. Participants learn to construct this outer harness from scratch, enabling agents to adhere to specific architectural rules, manage costs, ensure compliance, and provide auditable evidence for human review. The goal is to develop a mental model for building robust, controlled, and safe AI coding agent systems that integrate with existing tools and company-specific conventions.

## Key Takeaways & Recommendations

- Build a 'harness' around your AI coding agent to enforce company-specific architectural rules and conventions.
- Implement explicit context management and feedback mechanisms to guide agent behavior and improve results.
- Design the harness to manage cost and token budgets, stopping expensive checks or capping repair attempts.
- Incorporate compliance and review mechanisms within the harness to generate auditable evidence for human sign-off.

## Discovered Resources

- [Agents.md](http://agents.md)
- [Mastering BDD](https://testomat.io/blog/mastering-bdd-tips-tricks-and-best-practices-for-setting-up-a-testing-framework/)
- [TDD vs BDD](https://www.ramotion.com/blog/tdd-vs-bdd/)
- [Outer Harness Workshop GitHub Repo](https://github.com/JiDarwish/outer-harness-workshop)

## Related Concepts

- [[orchestration]]
- [[security]]
- [[evaluation]]
- [[observability]]
- [[tool-use]]
