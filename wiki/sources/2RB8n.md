---
id: "2RB8n"
title: "We Built AI Agents To Fix Security Findings in Production — Here's What Developers Actually Merged"
speakers: ["Amine Boudraa", "Ruchita Kshirsagar", "Nihit Gupta", "Gianfranco Romani"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8n/we-built-ai-agents-to-fix-security-findings-in-production-heres-what-developers-actually-merged-amine-boudraa-ruchita-kshirsagar-nihit-gupta-gianfranco-romani-thomson-reuters"
concepts: ["mcp", "security", "sandboxing", "orchestration", "agent-gateway"]
relevance_score: 0.93
relevance_rationale: "High-relevance production case study on MCP‑based automated remediation agents operating at enterprise scale with measurable PR throughput and token efficiency."
resources:
---

# We Built AI Agents To Fix Security Findings in Production — Here's What Developers Actually Merged

**Canonical Presentation on Sched:** [We Built AI Agents To Fix Security Findings in Production — Here's What Developers Actually Merged](https://agntconmcpconeu26.sched.com/event/2RB8n/we-built-ai-agents-to-fix-security-findings-in-production-heres-what-developers-actually-merged-amine-boudraa-ruchita-kshirsagar-nihit-gupta-gianfranco-romani-thomson-reuters)  
**Speakers:** Amine Boudraa (Senior Product Security Engineer, Thomson Reuters), Ruchita Kshirsagar (Senior Product Security Engineer, Thomson Reuters), Nihit Gupta (Senior Product Security Engineer, Thomson Reuters), Gianfranco Romani (Senior ML Engineer, Thomson Reuters)  
**Relevance Score:** `0.93`

## Essence

The session described a production‑grade remediation system that deploys two specialized AI agents—one for SAST findings in first‑party code and another for SCA findings in third‑party libraries—to autonomously raise and manage pull requests across hundreds of repositories. The core problem addressed is the widening gap between vulnerability discovery (driven by AI‑assisted scanners) and manual remediation, where CVE submissions grew 263% from 2020 to 2025 while remediation improved only 19% year‑over‑year. To bridge this gap, the team built a remediation loop that combines deterministic, model‑outside preprocessing with a lightweight LLM reasoning step. For SAST, the agent performs taint analysis to trace the path from untrusted input to a dangerous operation, then identifies the minimal set of code locations where a fix can be applied, often a shared helper that mitigates multiple paths. For SCA, the agent uses an MCP‑based resolver that computes the smallest set of version bumps that clear all reported CVEs across a dependency tree, leveraging OpenRewrite recipes to perform the bulk of dependency upgrades outside the model’s context. This reduces the token load from ~40k raw dependency files to ~560 tokens per fix, dramatically lowering inference cost and latency. The remediation system orchestrates ephemeral micro‑VMs per job, each containing an agent loop, a security scanner (Snyk via MCP), git/worktree tooling, and a hosted Bedrock model isolated to the team’s AWS account. A GitHub App mediates PR interactions, while a central state store tracks each job through queued, running, PR‑open, and merged stages, enabling automatic repair of failed CI checks. At the time of the talk, the system was running 18 concurrent jobs, with 126 open PRs across 40 repositories, demonstrating enterprise‑scale automation. The speakers emphasized that trust is earned through rigorous pre‑ and post‑conditions: build/test playbooks, data‑flow tracing to reject risky fixes, and deterministic OpenRewrite steps that ensure reproducible, auditable changes.

## Key Takeaways & Recommendations

- Always perform taint or data‑flow analysis outside the LLM to define the exact set of safe fix locations before invoking the model; this limits the model’s reasoning to the minimal necessary context.
- Use deterministic dependency tree, then delegate the actual file rewrites to OpenRewrite or similar AST‑based tools to keep token usage low and ensure reproducible upgrades.
- Run each remediation job in an isolated, short‑lived micro‑VM with no persistent storage, and inject only least‑privilege credentials needed for git operations and model access.
- Gate every agent‑generated PR behind mandatory CI checks (build, test, security scan) and enable automatic repair only when the CI failure is classified as a transient or fixable issue by a deterministic heuristic.
- Maintain a centralized state store that records PR lifecycle events and enables the system to replay, audit, or rollback any agent action, providing traceability for compliance and debugging.

## Production Gotchas & Failure Modes

- Relying solely on the LLM to decide fix locations without taint analysis can produce patches that appear correct but leave dangerous data flows unmitigated, leading to false‑positive remediations.
- Applying naive version bumps (e.g., major upgrades) without evaluating transitive impacts can introduce breaking changes that cause build or test failures, eroding developer trust in the agent.
- Failing to isolate agent runs in ephemeral environments risks leakage of credentials or persistent state that could be exploited if the model is prompted to execute unintended commands.
- Not enforcing CI gating before allowing an agent to re‑attempt a fix can result in a loop of repeatedly broken PRs that clutter the backlog and waste reviewer time.

## Discovered Resources

*No outbound code repositories or whitepapers cited in this session.*  

## Related Concepts

- [[mcp]]
- [[security]]
- [[sandboxing]]
- [[orchestration]]
- [[agent-gateway]]
