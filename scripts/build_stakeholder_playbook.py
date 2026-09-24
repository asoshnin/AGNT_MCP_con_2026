import json
from pathlib import Path

HUB_DIR = Path("02_public_hub")
with open(HUB_DIR / "data" / "contacts.json") as f:
    contacts = json.load(f)

template = (
    "Hi {first_name}, built an open-source MCP server & knowledge hub for AGNTCon EU so AI agents "
    "can query session takeaways: https://agntcon-demo.vwoosh.com\n"
    "Search your name to see your talk! Would love your feedback (and feel free to drop your slides if not yet uploaded)."
)

playbook_lines = [
    "# 🎯 AGNTCon + MCPCon Europe 2026 — Stakeholder Communications Playbook",
    "",
    "> **Status:** Staged for Human In-The-Loop (HITL) Review & Execution  ",
    "> **Maintainer:** Alexey Soshnin (`alex@vwoosh.com`)  ",
    "> **Repository:** https://github.com/asoshnin/AGNT_MCP_con_2026  ",
    "> **Community Hub:** https://agntcon-demo.vwoosh.com  ",
    "> **Guardrail:** Strictly zero autonomous sends. All messages are dispatched manually by the operator.",
    "",
    "---",
    "",
    "## 📑 Table of Contents",
    "1. [Strategic Principles & Channel Rules](#1-strategic-principles--channel-rules)",
    "2. [Tier 1: Leadership & Key Decision-Makers](#2-tier-1-leadership--key-decision-makers)",
    "   - 2.1 [Angie Jones (Agentic AI Foundation Event Lead)](#21-angie-jones)",
    "   - 2.2 [Mazin Gilbert (The Linux Foundation VP)](#22-mazin-gilbert)",
    "   - 2.3 [David Soria Parra (Anthropic MCP Co-Creator)](#23-david-soria-parra)",
    "   - 2.4 [Paul Carleton & Shaun Smith (MCP Working Group Maintainers)](#24-mcp-working-group-maintainers)",
    "3. [Tier 2: The Organizing Committee (events@aaif.io)](#3-tier-2-the-organizing-committee)",
    "4. [Tier 3: Speaker Sniper Campaign (45 Verified LinkedIn Profiles)](#4-tier-3-speaker-sniper-campaign)",
    "5. [Tier 4: Public Community Announcement (LinkedIn & X)](#5-tier-4-public-community-announcement)",
    "",
    "---",
    "",
    "## 1. Strategic Principles & Channel Rules",
    "",
    "- **Preserve InMail Quota:** Never burn paid InMail credits for speakers who accept connection requests. Use LinkedIn **Connect ➔ Add a note** (free, ~100–150/week, max 300 chars).",
    "- **Clean, Transparent URLs (No Tracking Tokens):** Direct attendees to the main portal `https://agntcon-demo.vwoosh.com` with zero suspicious query parameters. This builds trust and invites them to experience the full platform and search engine.",
    "- **Universal AI Agents Framing:** Speak to the broad agentic ecosystem (general reasoning, automation, tools), rather than narrowing to coding assistants.",
    "- **Concierge Open-Source Positioning:** Position as a passionate remote attendee and open-source builder, never a corporate agency or consulting vendor.",
    "- **Direct Inbound Routing:** All replies automatically route to `alex@vwoosh.com` and Telegram bot via platform headers.",
    "",
    "---",
    "",
    "## 2. Tier 1: Leadership & Key Decision-Makers",
    "",
    "### 2.1 Angie Jones",
    "**Role:** VP Developer Experience, Agentic AI Foundation / AGNTCon EU & NA Host  ",
    "**LinkedIn:** https://www.linkedin.com/in/angiejones  ",
    "**Email:** `angie@aaif.io` / `events@aaif.io`  ",
    "**Channel Strategy:** Send the full email first (see Section 3), followed by a free connection request on LinkedIn.",
    "",
    "#### LinkedIn Note (254 chars):",
    "```text",
    "Hi Angie, congrats on a fantastic AGNTCon EU! Just sent an email to you & the committee regarding an open-source MCP companion & search hub I built for the community (agntcon-demo.vwoosh.com). Would love to connect here on LinkedIn! - Alexey",
    "```",
    "",
    "---",
    "",
    "### 2.2 Mazin Gilbert",
    "**Role:** VP of Advanced Technology, The Linux Foundation / Keynote Speaker  ",
    "**LinkedIn:** https://www.linkedin.com/in/mazin-gilbert-mba-ph-d-28b426  ",
    "**Channel:** LinkedIn Connect ➔ Add a note (or InMail if Connect is restricted).",
    "",
    "#### LinkedIn Note (254 chars):",
    "```text",
    "Hi Mazin, inspired by your AGNTCon EU keynote! Built an open-source MCP server & community hub (agntcon-demo.vwoosh.com) enabling AI agents to query conference architectures directly. Would love your perspective and to connect! - Alexey",
    "```",
    "",
    "---",
    "",
    "### 2.3 David Soria Parra",
    "**Role:** Member of Technical Staff at Anthropic / Co-Creator of Model Context Protocol  ",
    "**LinkedIn:** https://www.linkedin.com/in/david-soria-parra-4a78b3a/  ",
    "**Channel:** LinkedIn Connect ➔ Add a note.",
    "",
    "#### LinkedIn Note (217 chars):",
    "```text",
    "Hi David, huge fan of MCP! Built an open-source community companion indexing AGNTCon EU talks for AI agents (agntcon-demo.vwoosh.com). Would love your thoughts on our MCP tool schemas and to connect! - Alexey",
    "```",
    "",
    "---",
    "",
    "### 2.4 MCP Working Group Maintainers",
    "",
    "#### Paul Carleton (MTS Anthropic, Core MCP Maintainer)",
    "**LinkedIn:** https://www.linkedin.com/in/paulcarletonjr  ",
    "**GitHub:** https://github.com/pcarleton | **Email:** `paulc@anthropic.com`  ",
    "```text",
    "Hi Paul, as an MCP enthusiast, built an open-source MCP server for AGNTCon EU (agntcon-demo.vwoosh.com) exposing talks to AI agents. Would love your feedback on the server tool design! - Alexey",
    "```",
    "",
    "#### Shaun Smith (Transport WG Maintainer, Hugging Face)",
    "**LinkedIn:** https://www.linkedin.com/in/shaunsmith  ",
    "**Twitter/X:** `@shaunsmith`  ",
    "```text",
    "Hi Shaun, loved your MCP transport work! Built an open-source AGNTCon companion with native MCP tools for AI agents (agntcon-demo.vwoosh.com). Would love to connect and hear your feedback! - Alexey",
    "```",
    "",
    "---",
    "",
    "## 3. Tier 2: The Organizing Committee",
    "",
    "**To:** `events@aaif.io`, `angie@aaif.io`  ",
    "**From:** `Alexey Soshnin <alex@vwoosh.com>`  ",
    "**Reply-To:** `alex@vwoosh.com`  ",
    "**Subject:** Thank you for AGNTCon EU! Built an open-source MCP companion for the community",
    "",
    "```text",
    "Hi Angie and the AGNTCon Organizing Committee,",
    "",
    "First off, congratulations on a fantastic AGNTCon + MCPCon Europe in Amsterdam!",
    "",
    "I couldn't attend in person, but I followed the livestream and conference schedule closely and learned a tremendous amount from the sessions.",
    "",
    "As someone building with autonomous agents and the Model Context Protocol, I realized it would be amazing if AI agents could query the conference schedule, session abstracts, and takeaways directly via native MCP tools, rather than us having to browse web tables by hand.",
    "",
    "Over the weekend, I built a lightweight, open-source community companion:",
    "• Native MCP Server: Exposes the 80+ talks and architectures directly to agents as tools.",
    "• Zero-Cost Search Hub: Fast sub-second search and session explorer (https://agntcon-demo.vwoosh.com).",
    "",
    "Every event organizer knows the post-conference challenge of collecting slides from busy speakers. To help with this, we built a crowdsourced contribution workflow: presenters can submit missing decks directly (with automated AI safety checks), giving the committee a simple 1-click verification queue. And once the official session recordings are up on YouTube, we'd love to link them directly to each talk for the community.",
    "",
    "If your team would like to link this community companion directly from the official Sched portal for attendees, or explore integrating native MCP tools for AGNTCon North America in San Jose (Oct 22–23), the entire codebase is open-source (MIT) and I'd be delighted to help make necessary adaptations and connect it for free.",
    "",
    "🔗 Repository: https://github.com/asoshnin/AGNT_MCP_con_2026",
    "🌐 Community Hub: https://agntcon-demo.vwoosh.com",
    "",
    "No reply or action needed — just wanted to say thank you for organizing such an inspiring event!",
    "",
    "Warm regards,",
    "Alexey Soshnin",
    "alex@vwoosh.com | github.com/asoshnin",
    "```",
    "",
    "---",
    "",
    "## 4. Tier 3: Speaker Sniper Campaign (Actionable Dispatch Table)",
    "",
    "Below is the actionable list of all 45 speakers with verified LinkedIn URLs, their conference sessions, and clean ready-to-paste messages with no tracking tokens.",
    "",
    "| # | Speaker | Company | Session ID | LinkedIn Profile | Ready-to-Paste Message |",
    "| :--- | :--- | :--- | :--- | :--- | :--- |"
]

counter = 1
for s in contacts["speakers"]:
    li = s.get("linkedin_url")
    if not li:
        continue
    name = s["name"]
    first_name = name.split()[0]
    comp = s.get("company") or "Independent"
    sess_id = s.get("sessions", [{}])[0].get("session_id", "")
    
    msg = template.format(first_name=first_name)
    escaped_msg = msg.replace("\n", "<br>")
    playbook_lines.append(f"| {counter} | **{name}** | {comp} | `{sess_id}` | [Profile ↗]({li}) | {escaped_msg} |")
    counter += 1

playbook_lines.extend([
    "",
    "---",
    "",
    "## 5. Tier 4: Public Community Announcement",
    "",
    "### LinkedIn Post (Community Launch)",
    "```text",
    "Why didn't MCPCon have an MCP Server? 🤔",
    "",
    "Last week, 1,000+ AI engineers gathered in Amsterdam for AGNTCon + MCPCon Europe 2026. The technical talks on agent sandboxes, eBPF telemetry, and protocol standards were incredible.",
    "",
    "As someone building with autonomous agents, I noticed a curious irony: the world's premier conference on the Model Context Protocol didn't expose its own schedule as native MCP tools. We were all still browsing static web tables by hand.",
    "",
    "Over the weekend, I built an open-source companion for the developer community:",
    "⚡ Native MCP Server (mcp_server.py): Query 80+ session takeaways, architectures, and tools directly through AI agents.",
    "🔍 Sub-second hybrid search hub: https://agntcon-demo.vwoosh.com",
    "📦 1-click Obsidian second-brain markdown exporter.",
    "",
    "Around 30 sessions are still missing their slide decks on the official schedule — if you spoke at AGNTCon EU, you can find your talk and attach your slides directly via the hub in 1 click!",
    "",
    "The entire project is 100% open-source (MIT) and runs on free-tier inference and zero-server PII storage.",
    "",
    "🔗 Code: https://github.com/asoshnin/AGNT_MCP_con_2026",
    "🌐 Hub: https://agntcon-demo.vwoosh.com",
    "",
    "#AGNTCon #MCPCon #ModelContextProtocol #AgenticAI #OpenSource #AIAgents",
    "```",
    "",
    "### Twitter / X Launch Thread",
    "```text",
    "Why didn't MCPCon have an MCP Server? 🤖",
    "",
    "Built an open-source companion for AGNTCon + MCPCon Europe 2026 so AI agents can query 80+ technical talks directly via native MCP tools:",
    "👉 https://agntcon-demo.vwoosh.com",
    "",
    "1/3 Search 80+ talks across MCP, LangChain, and eBPF in <10ms.",
    "2/3 Native MCP tools for agents (stdio JSON-RPC).",
    "3/3 Missing slides? Speakers can upload their deck directly with AI verification.",
    "",
    "GitHub: https://github.com/asoshnin/AGNT_MCP_con_2026",
    "```"
])

out_path = HUB_DIR / "out" / "STAKEHOLDER_COMMUNICATIONS_PLAYBOOK.md"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(playbook_lines))

print(f"Successfully generated clean {out_path} with {counter - 1} verified speaker messages.")
