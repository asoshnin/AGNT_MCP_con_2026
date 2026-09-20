# Turnkey Production Security Guide: Cloudflare Tunnel & Turnstile

This guide explains how to publish the **AGNTCon + MCPCon EU 2026 Archive** to the public internet for **$0.00** while keeping it completely immune to DDoS, IP scanning, prompt-injection bots, and quota-draining attacks.

---

## 1. Zero-IP Exposure: Cloudflare Tunnel (`cloudflared`)

Never open ports `80` or `443` on your router or VPS. A Cloudflare Tunnel creates an encrypted outbound-only tunnel to Cloudflare’s global edge network.

### Step 1: Install `cloudflared`
- **Linux:** `sudo apt install cloudflared` (or download from Cloudflare)
- **Windows / macOS:** `brew install cloudflared` or `winget install Cloudflare.cloudflared`

### Step 2: Authenticate & Create Tunnel
```bash
cloudflared tunnel login
cloudflared tunnel create agntcon-hub
```

### Step 3: Configure Route (`~/.cloudflared/config.yml`)
```yaml
tunnel: <YOUR-TUNNEL-UUID>
credentials-file: /path/to/<YOUR-TUNNEL-UUID>.json

ingress:
  - hostname: agntcon2026.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

### Step 4: Start the Tunnel
```bash
cloudflared tunnel run agntcon-hub
```
*Your site is now live on `https://agntcon2026.yourdomain.com` with full enterprise DDoS protection, automatic SSL, and zero public IP exposure.*

---

## 2. Bot & Abuse Protection: Cloudflare Turnstile (Free)

To prevent bots from calling `/api/chat` and draining your free API quotas:

1. In Cloudflare Dashboard, go to **Turnstile** ➔ **Add Site**.
2. Select **Managed** or **Non-Interactive** (invisible to real humans).
3. Set your environment variables:
   ```bash
   export CF_TURNSTILE_SITE_KEY="your_site_key"
   export CF_TURNSTILE_SECRET_KEY="your_secret_key"
   ```
4. In `config.yaml`, set `security.cloudflare.turnstile_enabled: true`.

The web chat will now automatically verify that every question is sent by a real human browser before forwarding to the AI model.

---

## 3. Edge Rate Limiting Rules (Cloudflare Dashboard)

1. In Cloudflare Dashboard ➔ **Security** ➔ **WAF** ➔ **Rate Limiting Rules**.
2. Create Rule:
   - **URI Path** equals `/api/chat`
   - **Rate**: 5 requests per 1 minute per IP.
   - **Action**: Block for 1 hour or Challenge.

---

## 4. Built-in Application Hardening (Automatic)

Even without Cloudflare, `serve.py` automatically enforces:
- **Max 500 characters** per query (HTTP 400 rejection for longer inputs).
- **SQLite Read-Only (`mode=ro`)**: Engine-level write protection against SQL injection.
- **Strict Path Containment**: Traversal attempts (`../`) return HTTP 403.
- **Axiomatic Anti-Jailbreak Guardrails**: The model refuses non-conference questions and never leaks system instructions.
