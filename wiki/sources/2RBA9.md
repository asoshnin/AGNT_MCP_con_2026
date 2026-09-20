---
id: "2RBA9"
title: "ID-JAG: Solving OAuth Sprawl for Enterprise AI Agents"
speakers: ["Paul Carleton", "Joey Orlando", "Aaron Parecki"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBA9/id-jag-solving-oauth-sprawl-for-enterprise-ai-agents-joey-orlando-archestraai-aaron-parecki-okta-paul-carleton-anthropic"
concepts: ["mcp", "security", "identity", "orchestration"]
relevance_score: 0.98
relevance_rationale: "The talk directly addresses a core challenge in enterprise AI agent deployment: scalable and secure authorization for tool-use, proposing ID-JAG as a specific architectural solution within the MCP ecosystem. It covers the problem, solution, and implementation details, making it highly relevant to AGNTCon and MCPCon themes."
resources:
  - url: "https://datatracker.ietf.org/doc/html/draft-ietf-oauth-identity-assertion-authz-grant"
    label: "ID-JAG draft"
  - url: "https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization"
    label: "MCP Enterprise-Managed Authorization extension"
  - url: "https://pcarleton.github.io/draft-carleton-workload-authz-grant/draft-carleton-workload-authz-grant.html"
    label: "Workload Authorization Grant (WAG) draft"
  - url: "https://discord.com/channels/1358869848138059966/1360835991749001368"
    label: "#auth-ig Discord channel"
---

# ID-JAG: Solving OAuth Sprawl for Enterprise AI Agents

**Canonical Presentation on Sched:** [ID-JAG: Solving OAuth Sprawl for Enterprise AI Agents](https://agntconmcpconeu26.sched.com/event/2RBA9/id-jag-solving-oauth-sprawl-for-enterprise-ai-agents-joey-orlando-archestraai-aaron-parecki-okta-paul-carleton-anthropic)  
**Speakers:** Paul Carleton (Member of Technical Staff, Anthropic), Joey Orlando (Co-Founder, Archestra.AI), Aaron Parecki (Director of Identity Standards, Okta)  
**Relevance Score:** `0.98`

## Essence

The ID-JAG (Identity Assertion JWT Authorization Grant) pattern addresses the critical challenge of OAuth sprawl in enterprise AI agent deployments. Traditional per-user, per-service OAuth consent models fail to scale for thousands of employees interacting with numerous SaaS applications via AI agents. ID-JAG leverages an existing Single Sign-On (SSO) login to enable centrally governed, auditable access to approved Model Context Protocol (MCP) servers, eliminating repetitive OAuth prompts. This mechanism allows an identity provider (IdP) to issue a JWT that asserts a user's identity and authorized scope, which the MCP server then exchanges for a scoped access token to interact with tools on the user's behalf. This streamlines the security review process, enhances auditability, and provides a scalable authorization model for production-grade AI agents.

## Key Takeaways & Recommendations

- Implement ID-JAG to leverage existing SSO for centralized, auditable access to MCP servers, reducing OAuth sprawl.
- Ensure identity providers support the ID-JAG flow to enable seamless agent access to approved business systems without manual credential management.
- Consider the Workload Authorization Grant (WAG) for agent-to-agent or agent-to-tool authorization scenarios where human interaction is not involved.
- Integrate MCP-native access tokens for fine-grained, scoped access to tools, improving security posture and auditability.

## Discovered Resources

- [ID-JAG draft](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-identity-assertion-authz-grant)
- [MCP Enterprise-Managed Authorization extension](https://modelcontextprotocol.io/extensions/auth/enterprise-managed-authorization)
- [Workload Authorization Grant (WAG) draft](https://pcarleton.github.io/draft-carleton-workload-authz-grant/draft-carleton-workload-authz-grant.html)
- [#auth-ig Discord channel](https://discord.com/channels/1358869848138059966/1360835991749001368)

## Related Concepts

- [[mcp]]
- [[security]]
- [[identity]]
- [[orchestration]]
