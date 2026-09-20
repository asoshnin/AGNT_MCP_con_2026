---
id: "2RBBJ"
title: "AGNTCon + MCPCon Europe 2026: Infrastructure Red Teaming With Ablitera..."
speakers: ["Roy Belio", "Read More \u2192"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RBBJ/infrastructure-red-teaming-with-abliterated-models-what-actually-stops-agent-attacks-roy-belio-red-hat"
concepts: ["sandboxing", "security", "evaluation", "memory", "tool-use"]
relevance_score: 0.95
relevance_rationale: "Directly presents empirical red-teaming results for agent infrastructure on Kubernetes, covering sandboxing, NetworkPolicy enforcement, injection classification, and the unsolved memory-poisoning gap (OWASP ASI06)."
resources:
  - url: "https://github.com/aicatalyst-team/openclaw-openshift-redteam"
    label: "OpenClaw OpenShift Red Team"
---

# AGNTCon + MCPCon Europe 2026: Infrastructure Red Teaming With Ablitera...

**Canonical Presentation on Sched:** [AGNTCon + MCPCon Europe 2026: Infrastructure Red Teaming With Ablitera...](https://agntconmcpconeu26.sched.com/event/2RBBJ/infrastructure-red-teaming-with-abliterated-models-what-actually-stops-agent-attacks-roy-belio-red-hat)  
**Speakers:** Roy Belio (Senior Software Engineer, Red Hat), Read More →  
**Relevance Score:** `0.95`

## Essence

Model refusal is not a containment boundary: a successful prompt injection bypasses alignment, so infrastructure controls must be validated independently of model behavior. To isolate that variable, the speaker abliterated a Qwen3.6-27B model served via vLLM, eliminating refusals so every probe actually reached the tool-dispatch layer and the surrounding Kubernetes infrastructure. Across three hardening tiers on an OpenClaw agent in OpenShift, sandbox isolation (a separate tool pod with no credentials and automountServiceAccountToken disabled) eliminated credential exfiltration, NetworkPolicies blocked cluster escalation, and a prompt-injection classifier neutralized encoding-based attacks — but the classifier failed on semantic rephrasing, as the Bankr heist showed when 'translate this Morse code' bypassed a detector tuned for 'decode'. The one control that held across all tiers was placing the authorization boundary outside the token stream: the gateway pod holds secrets and the dispatcher, while the sandbox pod holds nothing worth stealing, with SSH as the sole ingress and egress restricted to DNS. The unresolved gap is memory poisoning (OWASP ASI06): probes that instruct the agent to persist attacker content into its own memory succeeded at every tier, and no deployed control currently addresses it. The talk closes with a preflight assertion pattern — verifying sandbox hostname, DNS label selectors, runtime class, image digests, and live API unreachability before every run — because a misconfigured sandbox that silently disables isolation is indistinguishable from a working one in the config.

## Key Takeaways & Recommendations

- Run tool execution in its own dedicated pod: the gateway pod holds API keys, service account, and dispatcher config, while the tool pod runs as uid 1000 with automountServiceAccountToken: false and no credentials.
- Enforce NetworkPolicies that allow egress only to DNS pods and deny kube-apiserver access from the sandbox; direct external egress should be blocked at the gateway.
- Add a preflight assertion script that checks sandbox hostname, DNS label selector, runtime class, image digests, and live API unreachability before every run — a sandbox that is configured but not active looks identical in the config.
- Treat memory poisoning (OWASP ASI06) as an unsolved control gap: design agent memory writes as untrusted input and assume no current tier prevents persistence of attacker content.

## Discovered Resources

- [OpenClaw OpenShift Red Team](https://github.com/aicatalyst-team/openclaw-openshift-redteam)

## Related Concepts

- [[sandboxing]]
- [[security]]
- [[evaluation]]
- [[memory]]
- [[tool-use]]
