---
id: "2RBB1"
title: "From Vibes To Data: Evaluating Agents on Your Real Work"
speakers: ["Ville Hellman"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBB1/from-vibes-to-data-evaluating-agents-on-your-real-work-ville-hellman-datadog"
concepts: ["evaluation", "orchestration", "mcp"]
relevance_score: 0.92
relevance_rationale: "Directly addresses the critical challenge of evaluating agent performance in real-world, enterprise-specific contexts, moving beyond generic benchmarks. It touches on MCP relevance through 'Which MCP/Plugin/CLI works best here?'"
resources:
---

# From Vibes To Data: Evaluating Agents on Your Real Work

**Canonical Presentation on Sched:** [From Vibes To Data: Evaluating Agents on Your Real Work](https://agntconmcpconeu26.sched.com/event/2RBB1/from-vibes-to-data-evaluating-agents-on-your-real-work-ville-hellman-datadog)  
**Speakers:** Ville Hellman (Staff Engineer, Datadog)  
**Relevance Score:** `0.92`

## Essence

Datadog developed an internal evaluation platform to move beyond public benchmarks like SWE-Bench, which failed to capture the nuances of their specific codebase, conventions, and internal libraries. The core insight is that agent performance is highly context-dependent, varying significantly across different repositories and organizational best practices. Their platform allows teams to encode these best practices as evaluation criteria, providing concrete data on how changes to skills, steering documentation, agent harnesses, and MCP servers impact real-world agent performance and token cost. This enables a data-driven approach to model selection, optimizing for the necessary performance while managing token expenditure, and fostering an organizational learning loop for continuous improvement.

## Key Takeaways & Recommendations

- Build internal evaluation platforms tailored to your specific codebase and organizational conventions, as public benchmarks are insufficient.
- Encode organizational best practices and internal library usage into your evaluation suite to accurately measure agent effectiveness.
- Treat context provision as an optimization problem, balancing higher intelligence and token usage against missing context.
- Develop a relatively small, stable evaluation suite that provides consistent signal for continuous agent improvement.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[evaluation]]
- [[orchestration]]
- [[mcp]]
