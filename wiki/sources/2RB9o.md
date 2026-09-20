---
id: "2RB9o"
title: "The Unix Philosophy for AI Agents: Filesystems as the Context Primitive"
speakers: ["Cannis Chan", "Daniel Temesgen"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9o/the-unix-philosophy-for-ai-agents-filesystems-as-the-context-primitive-cannis-chan-daniel-temesgen-bloomberg"
concepts: ["mcp", "orchestration", "sandboxing", "tool-use", "security"]
relevance_score: 0.98
relevance_rationale: "Directly addresses core challenges in multi-agent context management and interoperability, proposing a concrete architectural solution relevant to both AGNTCon and MCPCon themes, particularly regarding tool-use, orchestration, and security within agentic systems."
resources:
  - url: "https://qrfy.io/lwtGFvD-t6"
    label: "Filesystems WG Charter"
  - url: "https://qrfy.io/-v4JQ7zzQG"
    label: "Discord: filesystem-wg"
  - url: "https://www.bloomberg.com/company/values/tech-at-bloomberg/artificial-intelligence-ai/"
    label: "Tech at Bloomberg: AI"
  - url: "https://www.linkedin.com/in/chancanniscwt/"
    label: "Cannis Chan LinkedIn"
  - url: "https://www.linkedin.com/in/dtemesgen/"
    label: "Daniel Temesgen LinkedIn"
---

# The Unix Philosophy for AI Agents: Filesystems as the Context Primitive

**Canonical Presentation on Sched:** [The Unix Philosophy for AI Agents: Filesystems as the Context Primitive](https://agntconmcpconeu26.sched.com/event/2RB9o/the-unix-philosophy-for-ai-agents-filesystems-as-the-context-primitive-cannis-chan-daniel-temesgen-bloomberg)  
**Speakers:** Cannis Chan (Technical Product Manager, Bloomberg), Daniel Temesgen (Senior Software Engineer, Bloomberg)  
**Relevance Score:** `0.98`

## Essence

This talk proposes a novel architecture for AI agent context management, leveraging the Unix philosophy of 'everything is a file' to address the M x N context crisis in multi-agent systems. By modeling agent context as scoped virtual filesystems, the system provides a unified interface for agents to interact with diverse data sources and shared state using standard filesystem operations (read, write, list). This approach enforces scope, lifecycle, and access control per mount, preventing state leakage and simplifying inter-agent communication. It transforms opaque retrieval mechanisms into navigable directory trees, making external data more discoverable and composable, and advocates for filesystem operations as a first-class interoperability primitive within the MCP specification.

## Key Takeaways & Recommendations

- Model agent context as scoped virtual filesystems to provide a unified interface for diverse data sources and shared state.
- Utilize standard filesystem operations (read, write, list) for agent interactions, enforcing scope and access control per mount.
- Treat external data sources as mountpoints, enabling navigable directory trees with `ls`/`cd`/`cat` semantics for retrieval.
- Join the MCP working group to standardize filesystem abstractions for resources, promoting a common contract for discovery, search, inspection, and safe change across agent platforms.

## Discovered Resources

- [Filesystems WG Charter](https://qrfy.io/lwtGFvD-t6)
- [Discord: filesystem-wg](https://qrfy.io/-v4JQ7zzQG)
- [Tech at Bloomberg: AI](https://www.bloomberg.com/company/values/tech-at-bloomberg/artificial-intelligence-ai/)
- [Cannis Chan LinkedIn](https://www.linkedin.com/in/chancanniscwt/)
- [Daniel Temesgen LinkedIn](https://www.linkedin.com/in/dtemesgen/)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[sandboxing]]
- [[tool-use]]
- [[security]]
