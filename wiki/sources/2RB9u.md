---
id: "2RB9u"
title: "CHAP, an Open Protocol for Auditable Human-Agent Collaboration"
speakers: ["Dr Arsalan Shahid"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9u/chap-an-open-protocol-for-auditable-human-agent-collaboration-dr-arsalan-shahid-brightbeam-ai"
concepts: ["mcp", "orchestration", "security", "observability", "identity"]
relevance_score: 0.98
relevance_rationale: "Directly addresses the problem of auditable human-agent collaboration, a core concern for AGNTCon and MCPCon, by proposing a new protocol that integrates with existing agent and tool communication standards."
resources:
  - url: "https://arxiv.org/abs/2606.09751"
    label: "CHAP Paper"
  - url: "https://github.com/BrightbeamAI/chap"
    label: "CHAP GitHub Repo"
---

# CHAP, an Open Protocol for Auditable Human-Agent Collaboration

**Canonical Presentation on Sched:** [CHAP, an Open Protocol for Auditable Human-Agent Collaboration](https://agntconmcpconeu26.sched.com/event/2RB9u/chap-an-open-protocol-for-auditable-human-agent-collaboration-dr-arsalan-shahid-brightbeam-ai)  
**Speakers:** Dr Arsalan Shahid (Principal Solutions Director, Brightbeam AI)  
**Relevance Score:** `0.98`

## Essence

CHAP (Collaborative Human-Agent Protocol) addresses the critical gap in auditable human-agent collaboration, moving beyond simple human supervision of single models to multi-human, multi-agent workflows across trust boundaries. It provides a protocol layer for shared workspaces, capturing decisive human actions like approvals, edits, and overrides as structured, replayable, and auditable evidence, rather than letting them dissipate into unstructured logs. The core primitives include workspaces, participants, tasks, artifacts, and an append-only evidence log, with composable profiles for specific interactions. CHAP complements existing protocols like MCP (for agent-tool interaction) and A2A (for agent-agent communication) by focusing specifically on accountable human-agent co-work, ensuring transparency and traceability in complex AI systems.

## Key Takeaways & Recommendations

- Implement CHAP to capture human approvals, edits, overrides, and handoffs as structured, auditable evidence.
- Integrate CHAP with existing MCP and A2A protocols to create a comprehensive framework for agent-tool, agent-agent, and human-agent collaboration.
- Utilize the append-only evidence log within CHAP for immutable record-keeping of all human-agent interactions.
- Leverage CHAP's composable profiles for specific interaction types (e.g., review, structured override, identity) to tailor auditability to different use cases.

## Discovered Resources

- [CHAP Paper](https://arxiv.org/abs/2606.09751)
- [CHAP GitHub Repo](https://github.com/BrightbeamAI/chap)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[security]]
- [[observability]]
- [[identity]]
