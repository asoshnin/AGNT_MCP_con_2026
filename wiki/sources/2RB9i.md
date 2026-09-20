---
id: "2RB9i"
title: "MAS-Lab: An Open Framework for Spec-Driven, Interoperable Multi-Agent Systems"
speakers: ["Jordan Aug\u00e9"]
sched_url: "https://agntconmcpconeu26.sched.com/event/2RB9i/mas-lab-an-open-framework-for-spec-driven-interoperable-multi-agent-systems-jordan-auge-cisco-systems"
concepts: ["mcp", "orchestration", "evaluation", "observability"]
relevance_score: 0.98
relevance_rationale: "The talk directly addresses the core challenges of building and validating multi-agent systems, which is central to AGNTCon. It introduces a framework (MAS-Lab) that leverages declarative specifications and systematic evaluation, aligning with themes of orchestration, reliability, and observability in agentic architectures."
resources:
  - url: "https://outshift.cisco.com/"
    label: "Outshift@Cisco"
  - url: "https://agntcy.org/"
    label: "Internet of Agents (AGNTCY)"
  - url: "https://arxiv.org/abs/2604.18233"
    label: "Aether: Network Validation Using Agentic AI and Digital Twin"
  - url: "https://outshift-headless-cms-s3.s3.us-east-2.amazonaws.com/Swisscom%20Whitepaper.pdf"
    label: "Driving autonomous network operations - Swisscom Whitepaper"
  - url: "https://outshift-open.github.io/mas-lab/tutorials/"
    label: "MAS-Lab Tutorials"
  - url: "https://outshift.cisco.com/blog/ai-ml/cognitive-challenges-in-multi-agent-systems"
    label: "Blog: Cognitive Challenges in Multi-Agent Systems"
  - url: "https://arxiv.org/abs/2606.30546"
    label: "MAS-Lab Initial Release Paper"
  - url: "https://github.com/outshift-open/mas-lab"
    label: "MAS-Lab GitHub Repository"
---

# MAS-Lab: An Open Framework for Spec-Driven, Interoperable Multi-Agent Systems

**Canonical Presentation on Sched:** [MAS-Lab: An Open Framework for Spec-Driven, Interoperable Multi-Agent Systems](https://agntconmcpconeu26.sched.com/event/2RB9i/mas-lab-an-open-framework-for-spec-driven-interoperable-multi-agent-systems-jordan-auge-cisco-systems)  
**Speakers:** Jordan Augé (Tech Lead, Outshift@Cisco - Chair of Accuracy and Reliabiity WG, Cisco Systems)  
**Relevance Score:** `0.98`

## Essence

MAS-Lab is an open, spec-driven framework designed to bring systematic composition, validation, and observability to multi-agent systems (MAS). It addresses the current challenges of hand-wired integrations, unsystematic validation, and late observability by introducing declarative YAML specifications for all MAS components, including agents, tools, models, memory, and coordination. This approach decouples runtime logic, control, and infrastructure, enabling robust governance, reproducible experimentation, and reliable behavior. The framework comprises three core elements: SPECS for declarative system definition, a modular RUNTIME for executing these specifications with built-in observability, and LABS for controlled validation and exploration of design alternatives, ensuring agent systems behave predictably and align with intent in production.

## Key Takeaways & Recommendations

- Adopt declarative specifications (YAML) for all MAS components to ensure systematic integration and versioning.
- Decouple agent runtime logic, control, and infrastructure through a plugin-based architecture for modularity and safety.
- Integrate observability and governance as first-class citizens from the outset, rather than adding them late in the development cycle.
- Utilize 'Labs' for systematic validation and experimentation, allowing for reproducible testing and exploration of design variations.

## Discovered Resources

- [Outshift@Cisco](https://outshift.cisco.com/)
- [Internet of Agents (AGNTCY)](https://agntcy.org/)
- [Aether: Network Validation Using Agentic AI and Digital Twin](https://arxiv.org/abs/2604.18233)
- [Driving autonomous network operations - Swisscom Whitepaper](https://outshift-headless-cms-s3.s3.us-east-2.amazonaws.com/Swisscom%20Whitepaper.pdf)
- [MAS-Lab Tutorials](https://outshift-open.github.io/mas-lab/tutorials/)
- [Blog: Cognitive Challenges in Multi-Agent Systems](https://outshift.cisco.com/blog/ai-ml/cognitive-challenges-in-multi-agent-systems)
- [MAS-Lab Initial Release Paper](https://arxiv.org/abs/2606.30546)
- [MAS-Lab GitHub Repository](https://github.com/outshift-open/mas-lab)

## Related Concepts

- [[mcp]]
- [[orchestration]]
- [[evaluation]]
- [[observability]]
