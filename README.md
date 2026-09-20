# AGNTCon + MCPCon Europe 2026 — Unofficial LLM Wiki & MCP Server

An independent, fair-use research wiki, interactive AI assistant, and Model Context Protocol (MCP) server for **AGNTCon + MCPCon Europe 2026** (17–18 September 2026, RAI Amsterdam).

> **Academic & Community Notice:**  
> This is an unofficial, independent open-source project. Original conference presentations, schedules, and materials are copyright © **The Linux Foundation / Agentic AI Foundation** and the respective speakers. This repository contains original conceptual syntheses, verified open-source tool links, and outbound links to official [Sched presentation pages](https://agntconmcpconeu26.sched.com/). No speaker slides are reproduced or hosted.

---

## 🚀 Quick Start (Run Locally in 10 Seconds)

### 1. Clone & Install
```bash
git clone https://github.com/asoshnin/agntcon-mcpcon-eu-2026.git
cd agntcon-mcpcon-eu-2026
pip install -r requirements.txt
```

### 2. Launch Local Web Workspace & AI Assistant
```bash
python serve.py
```
Open **`http://localhost:8080`** in your browser to:
- Browse and search all conference presentations by keyword, speaker, and topic.
- Read distilled Karpathy-style conceptual essences and verified GitHub links.
- Chat with the AI assistant about presentations with direct citations linking to Sched.

---

## 🤖 Connect to AI Agents via MCP (Model Context Protocol)

This repository includes a native Model Context Protocol (MCP) server allowing **OpenClaw**, **Cursor**, **Claude Code**, or **Windsurf** to query the conference intelligence hub directly.

### Cursor / Claude Desktop Setup
Add this to your MCP configuration (`mcp.json` or Claude Desktop config):

```json
{
  "mcpServers": {
    "agntcon-2026": {
      "command": "python",
      "args": ["/path/to/agntcon-mcpcon-eu-2026/mcp_server.py"]
    }
  }
}
```

### Available MCP Tools:
- **`search_talks(query, topic)`**: Search conference sessions by keywords, speaker, or concept tags.
- **`get_page(page_type, name_or_id)`**: Retrieve an unofficial Karpathy-style source essence or cross-cutting concept page.
- **`answer_conference(question)`**: Ask complex cross-talk questions and get evidence-backed answers with canonical Sched links.

---

## ⚙️ Configuration & Models

The assistant works out of the box with free community endpoints:
- **Default Cloud Gateways:** Automatically uses Kilocode Gateway, NVIDIA NIM, or OpenRouter free tiers.
- **Local Model Support:** If you prefer 100% offline self-hosting, start [Ollama](https://ollama.com/) locally (`ollama run llama3.2`) and configure `config.yaml` to point to `http://localhost:11434/v1`.

---

## 📄 Attribution & Fair-Use Disclaimer
- Conference organized by **[The Linux Foundation / Agentic AI Foundation](https://events.linuxfoundation.org/agntcon-mcpcon-europe/)**.
- Official schedule and slide links: **[Sched Event Directory](https://agntconmcpconeu26.sched.com/)**.
- Official video recordings: **[Agentic AI Foundation YouTube](https://www.youtube.com/@agentic-ai-foundation)**.
- Licensed under **MIT License**.
