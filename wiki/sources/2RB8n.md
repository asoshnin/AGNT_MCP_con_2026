---
id: "2RB8n"
title: "We Built AI Agents To Fix Security Findings in Production — Here's What Developers Actually Merged"
speakers: ["Amine Boudraa", "Ruchita Kshirsagar", "Nihit Gupta", "Gianfranco Romani"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8n/we-built-ai-agents-to-fix-security-findings-in-production-heres-what-developers-actually-merged-amine-boudraa-ruchita-kshirsagar-nihit-gupta-gianfranco-romani-thomson-reuters"
concepts: ["mcp", "security", "orchestration", "evaluation", "tool-use"]
relevance_score: 0.98
relevance_rationale: "Directly addresses the practical application and challenges of building and deploying AI agents for security remediation in a production enterprise environment, including architectural considerations for trust and scale."
resources:
---

# We Built AI Agents To Fix Security Findings in Production — Here's What Developers Actually Merged

**Canonical Presentation on Sched:** [We Built AI Agents To Fix Security Findings in Production — Here's What Developers Actually Merged](https://agntconmcpconeu26.sched.com/event/2RB8n/we-built-ai-agents-to-fix-security-findings-in-production-heres-what-developers-actually-merged-amine-boudraa-ruchita-kshirsagar-nihit-gupta-gianfranco-romani-thomson-reuters)  
**Speakers:** Amine Boudraa (Senior Product Security Engineer, Thomson Reuters), Ruchita Kshirsagar (Senior Product Security Engineer, Thomson Reuters), Nihit Gupta (Senior Product Security Engineer, Thomson Reuters), Gianfranco Romani (Senior ML Engineer, Thomson Reuters)  
**Relevance Score:** `0.98`

## Essence

Thomson Reuters developed and deployed specialized AI agents to autonomously remediate security vulnerabilities (SAST and SCA findings) in production codebases, addressing the growing 'remediation gap' where vulnerability discovery outpaces manual fixes. Unlike general-purpose AI assistants, these agents are integrated into a comprehensive remediation system that manages the entire lifecycle of a fix, from creating optimized pull requests to tracking their status, repairing breaking changes, and re-verifying until merged. The core insight is that achieving developer trust and high merge rates at enterprise scale requires deep specialization, enabling agents to understand application context, trace data flows, and perform deterministic operations to ensure fix reliability and prevent risky changes. This approach emphasizes 'merged, not closed' as the true measure of success, focusing on practical engineering challenges like building and testing applications within the agent's workflow.

## Key Takeaways & Recommendations

- Specialize AI agents for specific remediation tasks (e.g., SAST, SCA) rather than relying on general-purpose assistants for enterprise-scale fixes.
- Build a comprehensive remediation system around agents to manage the full lifecycle of pull requests, including tracking, repairing, and re-verifying until merged.
- Prioritize deterministic operations within agent logic to enhance reliability and build developer trust.
- Focus on 'merged, not closed' as the key metric for success, ensuring agents can navigate the complexities of real-world development workflows to get changes accepted.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[security]]
- [[orchestration]]
- [[evaluation]]
- [[tool-use]]
