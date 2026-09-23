# Security Policy

## 🔒 Supported Versions

The AGNTCon + MCPCon Europe 2026 intelligence hub codebase is actively maintained on the `main` branch.

| Version | Supported          |
| ------- | ------------------ |
| 3.x     | :white_check_mark: |
| < 3.0   | :x:                |

---

## 🛡️ Reporting a Vulnerability

We take security, data privacy, and intellectual property seriously.

If you discover a security vulnerability or potential credential leak:
1. **Do NOT open a public GitHub issue.**
2. Report the vulnerability privately to the project maintainers via email at:
   **`alex@vwoosh.com`** or via private speaker inquiry on the live hub (`/admin#ticket`).
3. Include:
   - Description of the issue (e.g. prompt injection, SSRF, or XSS vector).
   - Steps to reproduce.
   - Potential impact and suggested mitigation.

We will acknowledge receipt of your report within 48 hours and work with you to coordinate a responsible disclosure and patch.

---

## 🔐 Key Security Invariants

- **Zero-SSRF Client Isolation**: All custom endpoint testing and BYOM key executions execute strictly browser-side (`window.fetch()`). The server never proxies arbitrary user-defined URLs.
- **Strict Input Clamping**: Chat prompts are clamped to a maximum of 500 characters and sanitized before execution.
- **In-Memory Rate Limiter & Concurrency Leases**: Protected by IP rate limiting and `asyncio.Semaphore(2)` concurrency queue with 45-second lease timeouts.
