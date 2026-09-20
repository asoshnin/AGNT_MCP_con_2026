---
id: "2VEfm"
title: "Exploring WebMCP: What Happens When AI Agents Start Using Websites?"
speakers: ["Sylwia Laskowska"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2VEfm/exploring-webmcp-what-happens-when-ai-agents-start-using-websites-sylwia-laskowska-atos"
concepts: ["mcp", "tool-use", "security", "orchestration"]
relevance_score: 0.95
relevance_rationale: "Directly discusses a novel approach (WebMCP) for AI agent interaction with web interfaces, focusing on explicit tool exposure and security considerations, which is central to MCP and agent orchestration."
resources:
  - url: "https://github.com/sylwia-lask/ai-ceo-webMCP"
    label: "AI CEO WebMCP Demo Repo"
  - url: "https://agntconmcpconeu26.sched.com/user/25824676"
    label: "Sylwia Laskowska Speaker Profile"
---

# Exploring WebMCP: What Happens When AI Agents Start Using Websites?

**Canonical Presentation on Sched:** [Exploring WebMCP: What Happens When AI Agents Start Using Websites?](https://agntconmcpconeu26.sched.com/event/2VEfm/exploring-webmcp-what-happens-when-ai-agents-start-using-websites-sylwia-laskowska-atos)  
**Speakers:** Sylwia Laskowska (Senior Software Engineer, Atos)  
**Relevance Score:** `0.95`

## Essence

WebMCP addresses the fundamental mismatch between the human-centric design of the modern web and the needs of AI agents. Currently, agents must infer actions from DOM structures, accessibility trees, or visual cues, leading to brittle and inefficient interactions. WebMCP proposes an experimental browser API that allows websites to explicitly expose structured 'tools' or actions, providing agents with a direct, machine-readable contract for interaction. This approach aims to reduce the reliance on complex browser automation and 'guessing,' enabling more robust and secure agent-website interoperability. While still experimental, WebMCP represents a potential paradigm shift towards building an 'agent-ready' web, where websites can communicate their capabilities directly to AI clients.

## Key Takeaways & Recommendations

- Design agent tools with minimum capability, granting narrow permissions.
- Validate all agent output, treating it as untrusted input.
- Implement human-in-the-loop confirmation for significant agent actions.
- Enforce strict authorization, ensuring agents do not gain extra privileges beyond their assigned capabilities.

## Discovered Resources

- [AI CEO WebMCP Demo Repo](https://github.com/sylwia-lask/ai-ceo-webMCP)
- [Sylwia Laskowska Speaker Profile](https://agntconmcpconeu26.sched.com/user/25824676)

## Related Concepts

- [[mcp]]
- [[tool-use]]
- [[security]]
- [[orchestration]]
