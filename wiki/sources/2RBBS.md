---
id: "2RBBS"
title: "Shipping a Production App in 10 Days: A Real Measurement of AI-Assisted Development"
speakers: ["Julien Dubois"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBBS/shipping-a-production-app-in-10-days-a-real-measurement-of-ai-assisted-development-julien-dubois-github"
concepts: ["orchestration", "evaluation", "mcp"]
relevance_score: 0.95
relevance_rationale: "Directly discusses the practical application and measurement of AI agent-assisted development, including architectural practices for managing agent output and the integration of runtime diagnostics (MCP) to enhance agent intelligence."
resources:
  - url: "https://github.com/jdubois/boot-ui"
    label: "BootUI GitHub Repository"
  - url: "https://github.com/jdubois/boot-ui/actions"
    label: "BootUI GitHub Actions"
  - url: "https://github.com/jdubois/boot-ui/pulls"
    label: "BootUI Pull Requests"
  - url: "https://docs.github.com/en/code-security"
    label: "GitHub Code Security Documentation"
  - url: "https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing"
    label: "GitHub Copilot Models and Pricing"
  - url: "https://developers.openai.com/api/docs/guides/prompt-caching"
    label: "OpenAI Prompt Caching Guide"
  - url: "https://platform.claude.com/docs/en/build-with-claude/prompt-caching"
    label: "Claude Prompt Caching Documentation"
  - url: "https://docs.github.com/en/copilot/concepts/models/auto-model-selection"
    label: "GitHub Copilot Auto Model Selection"
  - url: "https://github.blog/changelog/2026-07-01-copilot-cli-auto-model-selection-routes-based-on-task/"
    label: "Copilot CLI Auto Model Selection Changelog"
  - url: "https://github.blog/ai-and-ml/github-copilot/project-hydrafusion-frontier-quality-via-multi-model-orchestration/"
    label: "Project HydraFusion: Frontier Quality via Multi-Model Orchestration"
  - url: "https://github.com/features/ai/github-app"
    label: "GitHub Copilot App"
---

# Shipping a Production App in 10 Days: A Real Measurement of AI-Assisted Development

**Canonical Presentation on Sched:** [Shipping a Production App in 10 Days: A Real Measurement of AI-Assisted Development](https://agntconmcpconeu26.sched.com/event/2RBBS/shipping-a-production-app-in-10-days-a-real-measurement-of-ai-assisted-development-julien-dubois-github)  
**Speakers:** Julien Dubois (Principal Manager, Developer Relations, GitHub)  
**Relevance Score:** `0.95`

## Essence

This talk presents a compelling case study of AI-assisted development, detailing the creation of BootUI, a complex Spring Boot developer console, in just 11 days by a single developer leveraging GitHub Copilot. The core insight is that AI agents provide 10x-plus leverage for repetitive, well-defined tasks like scaffolding, panel creation, and test generation, allowing the human to focus on architecture, review, and steering. By managing a 'fleet of agents' through a high-throughput PR workflow, the project achieved a scope estimated to take 6.5-8.5 months manually, demonstrating a new paradigm for rapid, production-grade software delivery. The speaker emphasizes the importance of human judgment in architecting and reviewing the agent-generated code, effectively turning the developer into an orchestrator of AI-driven development. The BootUI project itself also integrates an opt-in MCP server to make agents smarter by providing runtime diagnostics.

## Key Takeaways & Recommendations

- Drive a 'fleet of agents' by day for repetitive tasks, focusing on deep architectural plans by night.
- Embrace a high-throughput pull request (PR) workflow, merging wins continuously.
- Focus human effort on architecting, reviewing, and steering the AI agents, rather than writing boilerplate code.
- Write clear specifications and comprehensive tests to guide agents and validate their output.

## Discovered Resources

- [BootUI GitHub Repository](https://github.com/jdubois/boot-ui)
- [BootUI GitHub Actions](https://github.com/jdubois/boot-ui/actions)
- [BootUI Pull Requests](https://github.com/jdubois/boot-ui/pulls)
- [GitHub Code Security Documentation](https://docs.github.com/en/code-security)
- [GitHub Copilot Models and Pricing](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing)
- [OpenAI Prompt Caching Guide](https://developers.openai.com/api/docs/guides/prompt-caching)
- [Claude Prompt Caching Documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [GitHub Copilot Auto Model Selection](https://docs.github.com/en/copilot/concepts/models/auto-model-selection)
- [Copilot CLI Auto Model Selection Changelog](https://github.blog/changelog/2026-07-01-copilot-cli-auto-model-selection-routes-based-on-task/)
- [Project HydraFusion: Frontier Quality via Multi-Model Orchestration](https://github.blog/ai-and-ml/github-copilot/project-hydrafusion-frontier-quality-via-multi-model-orchestration/)
- [GitHub Copilot App](https://github.com/features/ai/github-app)

## Related Concepts

- [[orchestration]]
- [[evaluation]]
- [[mcp]]
