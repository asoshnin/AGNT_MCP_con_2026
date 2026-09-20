---
id: "2RB8V"
title: "When NOT To Use an Agent: Choosing Between Workflows, Services, and Agent Systems"
speakers: ["Jigyasa Grover", "Rishabh Misra"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8V/when-not-to-use-an-agent-choosing-between-workflows-services-and-agent-systems-jigyasa-grover-uber-rishabh-misra-atlassian"
concepts: ["mcp", "security", "evaluation", "orchestration", "observability"]
relevance_score: 0.95
relevance_rationale: "Directly addresses the core theme of AGNTCon by providing a critical, nuanced perspective on agentic systems, focusing on when *not* to use them and the architectural trade-offs involved, which is central to robust MCP design."
resources:
---

# When NOT To Use an Agent: Choosing Between Workflows, Services, and Agent Systems

**Canonical Presentation on Sched:** [When NOT To Use an Agent: Choosing Between Workflows, Services, and Agent Systems](https://agntconmcpconeu26.sched.com/event/2RB8V/when-not-to-use-an-agent-choosing-between-workflows-services-and-agent-systems-jigyasa-grover-uber-rishabh-misra-atlassian)  
**Speakers:** Jigyasa Grover (ML Tech Lead @ Uber  • Google Developer Advisory Board Member • LinkedIn [in]structor • Book Author • Startup Advisor • 12 time AI + Open Source Award Winner • Featured @ Forbes, UN, Google I/O, and more!, Uber), Rishabh Misra (Principal ML Engineer, Atlassian)  
**Relevance Score:** `0.95`

## Essence

This talk challenges the prevailing notion that LLM-powered agents are a universal solution, instead framing them as a significant architectural trade-off. It dissects three primary LLM integration patterns: deterministic workflows, service-oriented architectures with LLM augmentation, and fully agentic systems with dynamic tool use. The core insight is to evaluate these patterns not by features, but by critical engineering constraints like failure isolation, latency predictability, observability, security boundaries, and evaluation complexity. The speakers advocate for a practical decision framework, urging engineers to consider simpler, more predictable architectures unless the unique benefits of agents demonstrably outweigh their inherent non-determinism and operational overhead.

## Key Takeaways & Recommendations

- Do not default to agents; view them as a trade-off introducing non-determinism and complexity.
- Evaluate LLM architectures against engineering constraints like failure isolation, latency, observability, and security, rather than just features.
- Prioritize simpler, more predictable architectures unless the specific problem unequivocally demands agentic capabilities.
- Develop a mental model and checklist to systematically justify the use of an agent over deterministic workflows or augmented services.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[security]]
- [[evaluation]]
- [[orchestration]]
- [[observability]]
