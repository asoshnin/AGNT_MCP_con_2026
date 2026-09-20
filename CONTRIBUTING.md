# Contributing to AGNTCon + MCPCon Europe 2026 Intelligence Hub

Thank you for your interest in contributing! We welcome community contributions, including:
- Correction or enhancement of talk essences, speaker names, and GitHub repository links.
- New cross-talk architectural concept pages (`wiki/concepts/*.md`).
- Client integrations for additional IDEs and autonomous coding agents.
- Bug reports and performance enhancements.

---

## 🧭 Core Principles & Invariants

1. **Strict Zero Financial Cost**: Never add dependencies, scripts, or configurations that trigger paid model API calls. All cloud demo features must use verified free endpoints or local offline models.
2. **Transformative Fair Use & Zero Slide Hosting**: Do not upload, mirror, or commit raw speaker slides or copyrighted video assets. Store only original conceptual summaries and link to canonical Sched pages.
3. **Privacy First (Zero-Server PII)**: User profiles, personalized filters, and custom API keys must remain strictly in client `localStorage` and never be transmitted to or stored on our servers.
4. **Code Quality**: All contributions must pass `ruff check .` and 100% of automated tests via `pytest`.

---

## 🛠️ Development Workflow

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/<your-username>/AGNT_MCP_con_2026.git
   cd AGNT_MCP_con_2026
   ```

2. **Create a Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install pytest ruff
   ```

3. **Run Quality Gates Before Submitting**:
   ```bash
   # 1. Run all unit and integration tests
   pytest tests/ -v

   # 2. Run Ruff linter
   ruff check .

   # 3. Verify zero secrets or tokens are exposed
   python ../scripts/audit_secrets.py
   ```

4. **Submit a Pull Request**:
   - Write clear, concise commit messages.
   - Describe the changes made and refer to relevant session IDs (e.g. `[2RBBJ]`).
