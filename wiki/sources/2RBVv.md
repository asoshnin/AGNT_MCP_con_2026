---
id: "2RBVv"
title: "Keynote: Three Doors to One Tool: MCP vs WebMCP vs CLI"
speakers: ["Fr\u00e9d\u00e9ric Barthelet", "Dominic Farolino", "I work on agentic web platform APIs in Chrome!"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBVv/keynote-three-doors-to-one-tool-mcp-vs-webmcp-vs-cli-frederic-barthelet-cto-co-founder-alpic-dominic-farolino-editor-of-the-webmcp-specification-software-engineer-google"
concepts: ["mcp", "orchestration", "security", "sandboxing"]
relevance_score: 0.98
relevance_rationale: "Directly addresses the core architectural decisions and trade-offs for integrating tools with AI agents, covering MCP, WebMCP, and CLI, which are central to AGNTCon and MCPCon themes."
resources:
---

# Keynote: Three Doors to One Tool: MCP vs WebMCP vs CLI

**Canonical Presentation on Sched:** [Keynote: Three Doors to One Tool: MCP vs WebMCP vs CLI](https://agntconmcpconeu26.sched.com/event/2RBVv/keynote-three-doors-to-one-tool-mcp-vs-webmcp-vs-cli-frederic-barthelet-cto-co-founder-alpic-dominic-farolino-editor-of-the-webmcp-specification-software-engineer-google)  
**Speakers:** Frédéric Barthelet (CTO & Co-founder, Alpic), Dominic Farolino (Software Engineer, Google), I work on agentic web platform APIs in Chrome!  
**Relevance Score:** `0.98`

## Essence

This keynote dissects the fundamental architectural choices for exposing tools to AI agents: traditional MCP servers, browser-based WebMCP, and command-line interfaces (CLI). The core insight is that each 'door' offers distinct trade-offs across critical axes like execution environment (backend, browser, model context, shell), state and authentication management, latency, and trust boundaries. The speakers provide a practical decision framework, emphasizing that the optimal choice depends heavily on the specific use case, sometimes even advocating for hybrid approaches where two surfaces are intentionally stacked. Understanding these distinctions is crucial for avoiding anti-patterns and building robust, secure agentic systems.

## Key Takeaways & Recommendations

- Map tool surfaces along axes like code execution location, state/auth management, latency, and trust boundaries.
- Utilize a decision framework to select the appropriate tool exposure surface (MCP, WebMCP, CLI) per use case.
- Consider stacking two different tool surfaces together for specific scenarios where their strengths complement each other.
- Actively identify and avoid anti-patterns that arise from misaligning the tool surface with the use case requirements.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[security]]
- [[sandboxing]]
