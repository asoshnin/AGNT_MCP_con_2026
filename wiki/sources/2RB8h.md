---
id: "2RB8h"
title: "From Opaque To Observable: Tracing Multi-Agent OpenClaw Workflows With OpenTelemetry"
speakers: ["Jordan Aug\u00e9"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB8h/from-opaque-to-observable-tracing-multi-agent-openclaw-workflows-with-opentelemetry-jordan-auge-cisco-systems"
concepts: ["observability", "orchestration", "evaluation", "mcp"]
relevance_score: 0.95
relevance_rationale: "Directly addresses critical observability challenges in multi-agent systems (MCP) and provides a concrete OpenTelemetry-based architectural solution for tracing complex agent workflows, which is central to AGNTCon and MCPCon themes."
resources:
  - url: "https://github.com/outshift-open/insight-module-for-agentic-systems"
    label: "Insight Module for Agentic Systems GitHub Repo"
  - url: "https://qrfy.io/6G2i5Karuv"
    label: "QR Code Link"
---

# From Opaque To Observable: Tracing Multi-Agent OpenClaw Workflows With OpenTelemetry

**Canonical Presentation on Sched:** [From Opaque To Observable: Tracing Multi-Agent OpenClaw Workflows With OpenTelemetry](https://agntconmcpconeu26.sched.com/event/2RB8h/from-opaque-to-observable-tracing-multi-agent-openclaw-workflows-with-opentelemetry-jordan-auge-cisco-systems)  
**Speakers:** Jordan Augé (Tech Lead, Outshift@Cisco - Chair of Accuracy and Reliabiity WG, Cisco Systems)  
**Relevance Score:** `0.95`

## Essence

The talk introduces InsightClaw, an OpenTelemetry-based observability plugin for OpenClaw multi-agent systems, addressing the inherent opaqueness of complex agentic workflows. It tackles critical blind spots like context assembly, routing, memory lifecycle, and decision checkpoints by providing a unified telemetry story. InsightClaw achieves this through typed lifecycle hooks, diagnostic events for model usage and costs, and optional provider SDK auto-instrumentation, generating connected traces, operational metrics, and cross-session lineage. This enables comprehensive 'agent forensics' by correlating control-plane events with agent execution, offering deep visibility into multi-turn, multi-agent interactions and delegation topologies.

## Key Takeaways & Recommendations

- Implement explicit session boundaries with start and end spans to track multi-turn, multi-agent workflows.
- Utilize span links for spawn and handoff events, along with fork/join annotations, to visualize delegation topology and child-session lineage.
- Leverage OpenTelemetry's OTLP-based telemetry pipeline for consistent instrumentation across different agent platforms like NemoClaw and DefenseClaw.
- Contribute to open-source observability extensions for agent harnesses and other multi-agent systems to improve community-wide visibility.

## Discovered Resources

- [Insight Module for Agentic Systems GitHub Repo](https://github.com/outshift-open/insight-module-for-agentic-systems)
- [QR Code Link](https://qrfy.io/6G2i5Karuv)

## Related Concepts

- [[observability]]
- [[orchestration]]
- [[evaluation]]
- [[mcp]]
