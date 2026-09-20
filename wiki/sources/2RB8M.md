---
id: "2RB8M"
title: "An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers"
speakers: ["Muhammad Ahsan Ayaz"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8M/an-orchestra-of-agents-what-i-learned-running-a-multi-agent-system-for-5000+-developers-muhammad-ahsan-ayaz-scania"
concepts: ["orchestration", "tool-use", "rag", "observability", "mcp"]
relevance_score: 0.98
relevance_rationale: "The talk directly addresses the challenges and architectural patterns for running multi-agent systems in production, covering orchestration, tool-use (MCP), and critical operational concerns like observability and data handling, which are central to AGNTCon and MCPCon themes."
resources:
  - url: "https://twitter.com/codewith_ahsan"
    label: "Muhammad Ahsan Ayaz's Twitter"
  - url: "https://github.com/AhsanAyaz/code-with-ahsan"
    label: "Code from the session"
  - url: "https://bio.link/codewithahsan"
    label: "Muhammad Ahsan Ayaz's Bio Link"
---

# An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers

**Canonical Presentation on Sched:** [An Orchestra of Agents: What I Learned Running a Multi-Agent System for 5,000+ Developers](https://agntconmcpconeu26.sched.com/event/2RB8M/an-orchestra-of-agents-what-i-learned-running-a-multi-agent-system-for-5000+-developers-muhammad-ahsan-ayaz-scania)  
**Speakers:** Muhammad Ahsan Ayaz (Software Architect, Scania)  
**Relevance Score:** `0.98`

## Essence

This talk dissects the journey of building and operating a multi-agent system for 5,000+ developers, moving beyond single-LLM agents to a robust 'orchestra' of 12 specialist agents. The core insight is the necessity of sophisticated orchestration primitives, including sequential pipelines, parallel fan-out, and LLM-driven dynamic routing, to handle real-world complexity and scale. Each agent is equipped with MCP tools, enabling them to interact with external systems like GitHub and StackOverflow. The speaker highlights critical production challenges such as drain-loop bugs, recency drift in RAG, and the essential, often overlooked, callback layers for PII sanitization, caching, and observability, emphasizing that production systems demand deterministic design where possible, reserving LLMs for dynamic routing and complex decision-making.

## Key Takeaways & Recommendations

- Implement determinism wherever possible in agent workflows, using LLMs only where dynamic routing or complex reasoning is strictly necessary.
- Design robust orchestration primitives for sequential, parallel, and dynamically routed agent interactions.
- Build essential callback layers for PII sanitization, caching, and comprehensive observability, as these are critical for production stability and compliance.
- Ensure proper stream draining mechanisms to prevent issues like agents cancelling mid-flight or resource leaks.

## Discovered Resources

- [Muhammad Ahsan Ayaz's Twitter](https://twitter.com/codewith_ahsan)
- [Code from the session](https://github.com/AhsanAyaz/code-with-ahsan)
- [Muhammad Ahsan Ayaz's Bio Link](https://bio.link/codewithahsan)

## Related Concepts

- [[orchestration]]
- [[tool-use]]
- [[rag]]
- [[observability]]
- [[mcp]]
