---
id: "2RBSY"
title: "Sponsored Workshop: The Buzz-Word Is Collaboration"
speakers: ["Bradley Axen", "Wes Billman", "Morgan Martin", "Tyler Longwell"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBSY/sponsored-workshop-the-buzz-word-is-collaboration-morgan-martin-tyler-longwell-wes-billman-bradley-axen-block"
concepts: ["mcp", "security", "sandboxing", "orchestration", "governance"]
relevance_score: 0.94
relevance_rationale: "This workshop represents a critical production case study in modern LLM agent ecosystems—demonstrating how to move from fragmented API-based agent interactions to integrated, collaborative workspaces. It provides concrete architectural patterns (portable identity, scoped capabilities, signed work) and measurable outcomes (shared Git repository, real-time multi-agent coordination) that directly address the scalability and security challenges of large-scale agent deployments."
resources:
  - url: "https://agntcon.communities.buzz.xyz/invite/v2.C68HdCXSeGZiSSzH0CCO8uWWmlWwOomUVKhCLTliuII"
    label: "Official Invitation & Session Details"
  - url: "https://docs.google.com/file/d/1H2cKoeVFFXiosxD4N1zRswonXGLyhzD1/preview"
    label: "Workshop Slides"
  - url: "https://buzz.xyz/Speakers"
    label: "Buzz Project Speaker List"
---

# Sponsored Workshop: The Buzz-Word Is Collaboration

**Canonical Presentation on Sched:** [Sponsored Workshop: The Buzz-Word Is Collaboration](https://agntconmcpconeu26.sched.com/event/2RBSY/sponsored-workshop-the-buzz-word-is-collaboration-morgan-martin-tyler-longwell-wes-billman-bradley-axen-block)  
**Speakers:** Bradley Axen (Creator & Maintainer of Goose; Tech Lead, Block), Wes Billman (Engineer, Block), Morgan Martin (Design Lead, Block), Tyler Longwell (Engineer, Block)  
**Relevance Score:** `0.94`

## Essence

The 'The Buzz-Word Is Collaboration' workshop demonstrates a paradigm shift from treating agents as isolated APIs between humans and systems to embedding them directly into shared workspaces. At its core, the challenge is solving the friction of distributed agent coordination—where each agent must communicate, review, and contribute to a common project without manual handoffs. Buzz, Block's open-source channel-driven workspace, addresses this by providing a persistent, shared environment where people and AI agents co-exist in the same channels, repositories, and review cycles.

The architectural pattern centers on three pillars: portable identity, scoped capabilities, and signed work. Portable identity allows agents to authenticate and authorize within Buzz without being tied to a single runtime or model, enabling seamless collaboration across different agent implementations. Scoped capabilities define what each agent may do within the workspace, preventing over-privilege while maximizing utility. Signed work introduces cryptographic provenance to actions taken within the shared space, ensuring auditability and trust when multiple agents modify the same artifacts.

Production-scale implementation involves integrating Buzz as the central orchestrator alongside Block's goose agent framework. The workflow begins with a live project scenario involving multiple participants and a swarm of agents operating across shared channels and code repositories. Attendees join a Buzz community, delegate tasks through structured channels, and participate in real-time code reviews and asset contributions. The key innovation is making the room itself part of the workflow—the entire team sees, steers, and uses agents collectively rather than through isolated API calls.

Key technical details include Buzz's Rust-based relay and event protocol for low-latency inter-agent communication, a channel-first architecture that supports both human and agent participation, and a Git-integrated workflow where the shared Buzz-hosted repository serves as the single source of truth. The system handles cross-runtime coordination (different agent models and runtimes) through standardized message formats and capability contracts.

## Key Takeaways & Recommendations

- Implement strict capability bounding: every agent should receive only the minimal permissions required for its specific task within the Buzz workspace, and these bounds must be validated at runtime via signed work tokens.
- Enforce sandboxed execution for cross-runtime agent interactions—run agents in isolated containers with restricted file system and network access to prevent lateral movement if an agent is compromised.
- Establish explicit delegation and steering protocols within Buzz channels, defining clear ownership and approval workflows so that human oversight remains visible even in highly automated settings.

## Production Gotchas & Failure Modes

- Improper identity boundary enforcement can allow compromised agents to escalate privileges beyond their scoped capabilities, leading to unauthorized modifications in the shared workspace.
- Cross-runtime agent coordination failures may arise when agents operate under incompatible execution environments, causing deadlocks or inconsistent state when collaborating on the same artifact.

## Discovered Resources

- [Official Invitation & Session Details](https://agntcon.communities.buzz.xyz/invite/v2.C68HdCXSeGZiSSzH0CCO8uWWmlWwOomUVKhCLTliuII)
- [Workshop Slides](https://docs.google.com/file/d/1H2cKoeVFFXiosxD4N1zRswonXGLyhzD1/preview)
- [Buzz Project Speaker List](https://buzz.xyz/Speakers)

## Related Concepts

- [[mcp]]
- [[security]]
- [[sandboxing]]
- [[orchestration]]
- [[governance]]
