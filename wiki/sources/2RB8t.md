---
id: "2RB8t"
title: "MCP Doesn't Have a Context Problem"
speakers: ["Sam Morrow"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8t/mcp-doesnt-have-a-context-problem-sam-morrow-github"
concepts: ["mcp", "orchestration", "tool-use"]
relevance_score: 0.98
relevance_rationale: "Directly addresses a critical challenge in MCP (context management for tool-use) and proposes concrete architectural solutions for agent harnesses."
resources:
---

# MCP Doesn't Have a Context Problem

**Canonical Presentation on Sched:** [MCP Doesn't Have a Context Problem](https://agntconmcpconeu26.sched.com/event/2RB8t/mcp-doesnt-have-a-context-problem-sam-morrow-github)  
**Speakers:** Sam Morrow (Staff Software Engineer, GitHub)  
**Relevance Score:** `0.98`

## Essence

This talk refutes the common misconception that the Multi-tool Co-Pilot Protocol (MCP) inherently suffers from a 'context problem' due to excessive token usage for tool descriptions. Instead, it posits that the issue lies in a lack of sophisticated context engineering within MCP implementations. The speaker introduces `mcpi`, a custom agent harness, to demonstrate three progressive tool discovery strategies. The core insight is 'skills over MCP,' where high-level skill descriptions are initially provided, and specific tools are only enabled and described in detail upon skill invocation, significantly reducing context window burden. This approach, complemented by MCP CLIs and 'Code Mode,' allows for efficient and composable agentic workflows by dynamically managing tool visibility and context.

## Key Takeaways & Recommendations

- Implement 'skills over MCP' where high-level skill descriptions are provided, and specific tools are only enabled and described upon skill invocation.
- Utilize MCP CLIs for specific, well-defined interactions to complement skill-based discovery.
- Integrate 'Code Mode' approaches to leverage different strengths in tool interaction and context management.
- Apply serious context engineering to MCP implementations to optimize token usage and improve composability.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[tool-use]]
