---
id: "2RB8h"
title: "From Opaque To Observable: Tracing Multi-Agent OpenClaw Workflows With OpenTelemetry"
speakers: ["Jordan Aug\u00e9"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8h/from-opaque-to-observable-tracing-multi-agent-openclaw-workflows-with-opentelemetry-jordan-auge-cisco-systems"
concepts: ["mcp", "security", "agent-gateway", "observability", "orchestration"]
relevance_score: 0.92
relevance_rationale: "This session directly addresses the critical gap between OpenClaw's basic OpenTelemetry diagnostics and the operational needs of multi-agent workflows requiring cross-agent traceability, context continuity, and semantic-compliant telemetry. The proposed plugin bridges the observability gap with concrete architectural patterns (typed lifecycle hooks, fork/join span linking, derived metrics) and ties into established standards (OTel GenAI semconv), making it immediately applicable to production deployments seeking observable, auditable agent systems."
resources:
  - url: "https://github.com/outshift-open/insight-module-for-agentic-systems"
    label: "Official Implementation"
  - url: "https://qrfy.io/6G2i5Karuv"
    label: "Supplementary Material"
---

# From Opaque To Observable: Tracing Multi-Agent OpenClaw Workflows With OpenTelemetry

**Canonical Presentation on Sched:** [From Opaque To Observable: Tracing Multi-Agent OpenClaw Workflows With OpenTelemetry](https://agntconmcpconeu26.sched.com/event/2RB8h/from-opaque-to-observable-tracing-multi-agent-openclaw-workflows-with-opentelemetry-jordan-auge-cisco-systems)  
**Speakers:** Jordan Augé (Tech Lead, Outshift@Cisco - Chair of Accuracy and Reliabiity WG, Cisco Systems)  
**Relevance Score:** `0.92`

## Essence

This session presents an open observability extension for OpenClaw (InsightClaw) that transforms opaque multi-agent workflows into connected telemetry stories using OpenTelemetry. The core problem is that OpenClaw's built-in diagnostics-otel exporter provides only local runtime diagnostics—agent logs, tool calls, session state—and lacks cross-agent, lifecycle-level visibility needed for 'agent forensics' such as agent-to-agent interactions, sub-agent trees, memory changes, and end-to-end correlation across workflows. The proposed solution introduces a new plugin that unifies four signal paths: typed lifecycle hooks spanning request, agent, tool, and response flows; diagnostics events covering model usage, cost, queue depth, webhook status, and stuck-session detection; and optional provider SDK auto-instrumentation for GenAI calls. This produces connected traces, operational metrics, and cross-session lineage for handoffs, spawned subagents, and parallel branches.

The architectural design addresses four specific blind spots identified in OpenClaw's current telemetry: (1) context assembly and sharing across prompts, agent state, memory, and tool outputs; (2) routing and delegation decisions—why one agent is chosen over another and why a particular sub-agent is invoked; (3) memory lifecycle tracking—when memories are written, retrieved, and how they influence decisions; and (4) decision checkpoints—private reasoning points, alternative paths considered, confidence levels, and skipped validations. The resulting feature set includes connected request lifecycles (single trace per inbound message through agent turns, tool calls, and outbound responses), workflow session semantics with explicit start/end spans, delegation topologies with fork/join annotations and child-session lineage, and derived coordination metrics (parallelisation, repetition, novelty, and memory-fragmentation scores) computed directly from trace data.

Architecturally, the plugin aligns with OTel GenAI semantic conventions (gen_ai.operation.name, gen_ai.workflow.name, gen_ai.provider.name) while proposing missing pieces like fork/join semantics and child-session lineage under ioa_observe.* attributes. It integrates with existing OpenClaw diagnostic infrastructure and exposes ~46 metrics across core request flow, gateway diagnostics, memory events, context assembly, and routing/delegation domains.

## Key Takeaways & Recommendations

- Enforce strict session boundary contracts with idempotent tracing: every inbound message must generate a root span, and all subsequent agent turns must link back via deterministic session keys to prevent orphaned traces.
- Implement fork/join span linking for delegation topology: use explicit child-session lineage and parent-child span relationships to capture spawn and handoff semantics, ensuring sub-agent execution remains correlated with the original request.
- Adopt OTel GenAI semantic conventions early—map gen_ai.operation.name to invoke_workflow, gen_ai.workflow.name to workflow spans, and gen_ai.provider.name to provider spans—to guarantee downstream analytics pipelines interpret telemetry correctly.
- Compute derived coordination metrics (parallelisation_score, novelty_score, memory_fragmentation) directly from trace attributes rather than post-hoc heuristics, reducing false positives in operational dashboards.
- Sandbox instrumentation to prevent leakage: ensure all auto-instrumented GenAI provider SDKs run within isolated contexts and never expose raw prompt contents or sensitive memory states in telemetry exports.

## Production Gotchas & Failure Modes

- Silent delegation failures occur when task selection or sub-agent routing errors propagate without clear error signaling, causing stalled workflows and undetected deadlock conditions in multi-agent chains.
- Long-pause context truncation leads to memory fragmentation and lost decision provenance because the memory lifecycle tracking relies on continuous event emission that degrades under extended idle periods.
- Semantic convention gaps between OTel GenAI standards and actual agent workflows cause misaligned telemetry interpretation, leading to incorrect derived metrics (e.g., novelty_score, parallelisation_score) that reflect proxy rather than true coordination quality.

## Discovered Resources

- [Official Implementation](https://github.com/outshift-open/insight-module-for-agentic-systems)
- [Supplementary Material](https://qrfy.io/6G2i5Karuv)

## Related Concepts

- [[mcp]]
- [[security]]
- [[agent-gateway]]
- [[observability]]
- [[orchestration]]
