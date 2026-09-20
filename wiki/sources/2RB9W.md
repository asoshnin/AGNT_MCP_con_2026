---
id: "2RB9W"
title: "Skills Need SemVer Too"
speakers: ["Pedro Rodrigues"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9W/skills-need-semver-too-pedro-rodrigues-supabase"
concepts: ["mcp", "orchestration", "evaluation"]
relevance_score: 0.92
relevance_rationale: "Directly addresses a fundamental challenge in the agent ecosystem: managing the lifecycle and dependencies of agent skills, which is crucial for robust MCP implementations and agent orchestration."
resources:
  - url: "https://supabase.com/.well-known/agent-skills/index.json"
    label: "Example Skill Discovery Index"
---

# Skills Need SemVer Too

**Canonical Presentation on Sched:** [Skills Need SemVer Too](https://agntconmcpconeu26.sched.com/event/2RB9W/skills-need-semver-too-pedro-rodrigues-supabase)  
**Speakers:** Pedro Rodrigues (AI Tooling Engineer, Supabase)  
**Relevance Score:** `0.92`

## Essence

The talk addresses the critical need for robust versioning and dependency management for AI agent skills, moving beyond mere discovery. As agent skills become integral to production workflows, their evolution—through instruction changes, best practice improvements, and capability growth—necessitates a standardized approach to prevent reliance on outdated or incompatible knowledge. The speaker proposes integrating Semantic Versioning (SemVer) into skill distribution, leveraging emerging standards like the `.well-known` discovery mechanism to provide artifact identity, change detection, and integrity. This framework aims to enable reproducible skill environments while allowing for easy access to the latest versions, drawing parallels to established package ecosystems.

## Key Takeaways & Recommendations

- Adopt a standardized publisher-origin discovery mechanism (e.g., `.well-known`) for agent skills.
- Implement Semantic Versioning (MAJOR.MINOR.PATCH) for agent skills to manage breaking changes, backward-compatible additions, and fixes.
- Ensure that skill distribution metadata includes versioning information and cryptographic digests (e.g., SHA256) for artifact identity and integrity checks.
- Prioritize making the 'latest' skill version easily accessible while also enabling reproducible historical comparisons through explicit versioning.

## Discovered Resources

- [Example Skill Discovery Index](https://supabase.com/.well-known/agent-skills/index.json)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[evaluation]]
