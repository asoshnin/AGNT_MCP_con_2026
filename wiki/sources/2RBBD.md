---
id: "2RBBD"
title: "Giving Your Agentic Coding AI a Security Brain"
speakers: ["Liran Tal"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBBD/giving-your-agentic-coding-ai-a-security-brain-liran-tal-snyk"
concepts: ["mcp", "security", "sandboxing", "orchestration", "evaluation"]
relevance_score: 0.98
relevance_rationale: "Directly addresses the security challenges and solutions for agentic coding AI, focusing on architectural patterns like MCPs and hooks for robust security integration."
resources:
---

# Giving Your Agentic Coding AI a Security Brain

**Canonical Presentation on Sched:** [Giving Your Agentic Coding AI a Security Brain](https://agntconmcpconeu26.sched.com/event/2RBBD/giving-your-agentic-coding-ai-a-security-brain-liran-tal-snyk)  
**Speakers:** Liran Tal (Director of Developer Relations, Snyk)  
**Relevance Score:** `0.98`

## Essence

This talk addresses the critical security vulnerabilities introduced by agentic coding AI, which can rapidly generate and deploy insecure code, including SSRF, RCE, and path traversal flaws. Traditional security prompts are insufficient due to their cost, brittleness, and non-deterministic nature. The core insight is to integrate security directly into the agent's workflow using Model Context Protocols (MCPs) and hooks. This architecture enables just-in-time package health checks and deterministic code reviews via pluggable AI components, providing agents with a 'security brain' to prevent the introduction of vulnerabilities and vet hallucinated dependencies. The approach aims to achieve both speed and security in AI-driven code generation.

## Key Takeaways & Recommendations

- Integrate just-in-time package health checks into agentic workflows.
- Implement deterministic code reviews using pluggable AI components.
- Utilize Model Context Protocols (MCPs) and hooks to embed security directly into agent operations.
- Avoid running agents with `--dangerously-skip-permissions`.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[security]]
- [[sandboxing]]
- [[orchestration]]
- [[evaluation]]
