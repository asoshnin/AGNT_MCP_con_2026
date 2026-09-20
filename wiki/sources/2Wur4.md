---
id: "2Wur4"
title: "Delegated Authorization for AI Agents: How to Build an Agent with Fine-Grained Permissions"
speakers: ["Sohan Maheshwar"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2Wur4/delegated-authorization-for-ai-agents-how-to-build-an-agent-with-fine-grained-permissions-sohan-maheshwar-authzed"
concepts: ["security", "mcp", "orchestration", "identity"]
relevance_score: 0.95
relevance_rationale: "Directly addresses a core security and management challenge for AI agents within the AGNTCon + MCPCon scope, focusing on fine-grained authorization and architectural patterns like ReBAC."
resources:
  - url: "https://github.com/authzed/spicedb"
    label: "SpiceDB GitHub Repository"
  - url: "https://github.com/sohanmaheshwar/goose-spicedb-delegation"
    label: "Goose & SpiceDB Delegation Demo"
  - url: "https://www.linkedin.com/in/sohanmaheshwar"
    label: "Sohan Maheshwar's LinkedIn"
---

# Delegated Authorization for AI Agents: How to Build an Agent with Fine-Grained Permissions

**Canonical Presentation on Sched:** [Delegated Authorization for AI Agents: How to Build an Agent with Fine-Grained Permissions](https://agntconmcpconeu26.sched.com/event/2Wur4/delegated-authorization-for-ai-agents-how-to-build-an-agent-with-fine-grained-permissions-sohan-maheshwar-authzed)  
**Speakers:** Sohan Maheshwar (Lead Developer Advocate, AuthZed)  
**Relevance Score:** `0.95`

## Essence

The talk addresses the critical security challenge of fine-grained authorization for AI agents, which often operate with overly permissive credentials, leading to potential production incidents. It advocates for Relationship-Based Access Control (ReBAC), inspired by Google Zanzibar, as a superior model to traditional RBAC for managing agent permissions at scale. ReBAC effectively handles complex, evolving relationships between users, agents, and resources, enabling capabilities like scoped delegation, expiring grants, instant revocation, and hierarchical permissions. This approach ensures agents only perform authorized actions by evaluating live relationships, preventing the over-granting and stale permissions common with token-based or role-based systems.

## Key Takeaways & Recommendations

- Adopt Relationship-Based Access Control (ReBAC) for managing AI agent permissions, moving beyond traditional RBAC.
- Implement server-side, self-cleaning expiring grants for agent permissions to avoid stale access windows.
- Utilize live lookup authorization checks for instant revocation of agent access, rather than relying on potentially valid but revoked tokens.
- Design hierarchical permission structures where agent access can be contingent on other relationships or roles.

## Discovered Resources

- [SpiceDB GitHub Repository](https://github.com/authzed/spicedb)
- [Goose & SpiceDB Delegation Demo](https://github.com/sohanmaheshwar/goose-spicedb-delegation)
- [Sohan Maheshwar's LinkedIn](https://www.linkedin.com/in/sohanmaheshwar)

## Related Concepts

- [[security]]
- [[mcp]]
- [[orchestration]]
- [[identity]]
