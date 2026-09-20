---
id: "2RB9c"
title: "We Built an Agent, We Shipped a Compiler. Here's Why"
speakers: ["Joel Verezhak"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9c/we-built-an-agent-we-shipped-a-compiler-heres-why-joel-verezhak-grafana-labs"
concepts: ["orchestration", "evaluation", "tool-use", "mcp"]
relevance_score: 0.95
relevance_rationale: "Directly addresses the architectural challenges and solutions for building reliable LLM-driven systems, moving from 'agentic' to 'compiler' paradigms, which is central to AGNTCon and MCPCon themes."
resources:
---

# We Built an Agent, We Shipped a Compiler. Here's Why

**Canonical Presentation on Sched:** [We Built an Agent, We Shipped a Compiler. Here's Why](https://agntconmcpconeu26.sched.com/event/2RB9c/we-built-an-agent-we-shipped-a-compiler-heres-why-joel-verezhak-grafana-labs)  
**Speakers:** Joel Verezhak (Observability Architect, Grafana Labs)  
**Relevance Score:** `0.95`

## Essence

Grafana Labs' journey to automate customer success plans revealed that true reliability in LLM-driven systems often necessitates a shift from 'agentic' thinking to a 'compiler' architecture. Initial attempts with large, single-skill agents failed due to lack of quality enforcement and determinism. Introducing structured sub-agents and scripted prompts improved control but still struggled with contextual drift and consistent output. The breakthrough came from embracing a compiler-like approach, where LLMs are treated as specialized functions within a tightly controlled, multi-stage pipeline, allowing for explicit data flow, progressive disclosure of information, and human-reviewable, replayable outputs. This framework ensures that LLMs perform specific, bounded tasks, rather than attempting broad, unconstrained 'agentic' reasoning, ultimately delivering trustworthy results.

## Key Takeaways & Recommendations

- Shift from a 'big skill' agent to a 'compiler' architecture, treating LLMs as functions within a structured, multi-stage pipeline.
- Implement progressive disclosure of information, allowing the system to 'be curious' and understand context before applying templates or generating outputs.
- Design for human review and replayability, ensuring outputs are auditable and failures are diagnosable.
- Distinguish clearly between pipeline work (deterministic, structured) and agent work (exploratory, LLM-driven) to manage expectations and system design.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[orchestration]]
- [[evaluation]]
- [[tool-use]]
- [[mcp]]
