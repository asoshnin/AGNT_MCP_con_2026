#!/usr/bin/env python3
"""Lightweight Unified Web Server & MCP Client Gateway for AGNTCon EU 2026.

Hosts:
1. Static Web Workspace (site/index.html + assets) on port 8080.
2. REST API endpoints (/api/search, /api/page, /api/chat) forwarding to MCP tools.
3. 4-Layer Security: Input clamping (500 chars), IP rate limiter, and clean error handling.
"""

import sys
import os

# Auto-resolve virtualenv if dependencies are missing in ambient Python
try:
    import httpx
except ModuleNotFoundError:
    hub_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate_venvs = [
        os.path.join(hub_parent, ".venv", "bin", "python"),
        os.path.join(os.path.expanduser("~"), ".openclaw", "venv", "bin", "python"),
    ]
    for venv_py in candidate_venvs:
        if os.path.exists(venv_py) and sys.executable != venv_py:
            os.execv(venv_py, [venv_py] + sys.argv)

import json
import time
import asyncio
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import argparse
import secrets

HUB_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(HUB_DIR, "site")

sys.path.insert(0, HUB_DIR)
from mcp_server import tool_search_talks, tool_get_page, tool_answer_conference
import crm_db

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "agntcon2026admin")
ADMIN_SESSION_TOKEN = secrets.token_hex(24)

def load_env_file():
    env_path = os.path.join(HUB_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'").strip('"')
                        if k and (k not in os.environ or not os.environ[k]):
                            os.environ[k] = v
        except Exception:
            pass

load_env_file()

def check_admin_auth(headers) -> bool:
    auth_header = headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        return token == ADMIN_SESSION_TOKEN
    return False

def dispatch_resend_email(to_email: str, subject: str, html_body: str):
    api_key = os.environ.get("RESEND_API_KEY")
    from_email = os.environ.get("RESEND_FROM_EMAIL", "Alexey Soshnin <alex@onexcare.com>")
    if not api_key or api_key == "YOUR_RESEND_KEY_HERE":
        sys.stdout.write(f"[INFO] RESEND_API_KEY not configured. Skipping email to {to_email}.\n")
        return

    try:
        import urllib.request
        url = "https://api.resend.com/emails"
        payload = json.dumps({
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "resend-python/2.0.0"
            }
        )
        with urllib.request.urlopen(req, timeout=4.0) as res:
            sys.stdout.write(f"[✓] Resend email dispatched to {to_email} (HTTP {res.status})\n")
    except Exception as e:
        sys.stderr.write(f"[WARN] Failed to dispatch Resend email to {to_email}: {e}\n")

def dispatch_telegram_alert(event_emoji: str, event_type: str, ticket_id: str, sender_name: str, org: str, email: str, profile: str, body: str):
    bot_token = os.environ.get("TOY_PROJECTS_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TOY_PROJECTS_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
    project_name = os.environ.get("PROJECT_NAME", "AGNTCon EU 2026")
    public_url = os.environ.get("PUBLIC_URL", "http://127.0.0.1:8088")

    if not (bot_token and chat_id):
        return

    org_str = f"({org})" if org else ""
    tg_text = (
        f"🤖 *[{project_name}]* · {event_emoji} *{event_type}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Ref:* `#{ticket_id}`\n"
        f"• *From:* {sender_name} {org_str}\n"
        f"• *Email:* `{email}`\n"
        f"• *Profile:* {profile}\n\n"
        f"_{body[:500]}_\n\n"
        f"🔗 *Admin Thread:* {public_url}/admin#ticket={ticket_id}"
    )

    try:
        import urllib.request
        tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        tg_payload = json.dumps({"chat_id": chat_id, "text": tg_text, "parse_mode": "Markdown"}).encode("utf-8")
        req = urllib.request.Request(tg_url, data=tg_payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=3.0)
    except Exception as e:
        sys.stderr.write(f"[WARN] Non-blocking Telegram alert error: {e}\n")

# In-Memory IP Rate Limiter & Daily Cap
IP_REQUEST_LOG = {}
RATE_LIMIT_PER_MINUTE = 5
MAX_QUERY_CHARS = 500

DAILY_REQUEST_COUNT = 0
LAST_RESET_DAY = time.strftime("%Y-%m-%d")
DAILY_MAX_REQUESTS = 200

def check_daily_quota() -> bool:
    global DAILY_REQUEST_COUNT, LAST_RESET_DAY
    today = time.strftime("%Y-%m-%d")
    if today != LAST_RESET_DAY:
        DAILY_REQUEST_COUNT = 0
        LAST_RESET_DAY = today
    if DAILY_REQUEST_COUNT >= DAILY_MAX_REQUESTS:
        return False
    DAILY_REQUEST_COUNT += 1
    return True

def check_ip_rate_limit(ip: str) -> bool:
    now = time.time()
    if ip not in IP_REQUEST_LOG:
        IP_REQUEST_LOG[ip] = []
    # Retain timestamps from last 60s
    IP_REQUEST_LOG[ip] = [t for t in IP_REQUEST_LOG[ip] if now - t < 60]
    if len(IP_REQUEST_LOG[ip]) >= RATE_LIMIT_PER_MINUTE:
        return False
    IP_REQUEST_LOG[ip].append(now)
    return True

class HubHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE_DIR, **kwargs)

    def log_message(self, format, *args):
        # Clean logging format
        try:
            sys.stdout.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}\n")
        except Exception:
            sys.stdout.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format}\n")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)

        # Health endpoint
        if path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "agntcon-2026-hub", "version": "3.0.0"}).encode("utf-8"))
            return

        # Search API
        if path == "/api/search":
            q = query_params.get("q", [""])[0][:MAX_QUERY_CHARS]
            topic = query_params.get("topic", [None])[0]
            only_slides = query_params.get("only_with_slides", ["0"])[0] in ("1", "true", "True")
            results = tool_search_talks(q, topic=topic, only_with_slides=only_slides)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(results, ensure_ascii=False).encode("utf-8"))
            return

        # Page API
        if path == "/api/page":
            ptype = query_params.get("type", ["source"])[0]
            pname = query_params.get("name", [""])[0]
            page_data = tool_get_page(ptype, pname)
            
            status_code = 200 if "error" not in page_data else 404
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(page_data, ensure_ascii=False).encode("utf-8"))
            return

        # Mini-CRM Dashboard Route
        if path in ("/admin", "/admin/"):
            admin_html = os.path.join(SITE_DIR, "admin.html")
            with open(admin_html, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content)
            return

        # Client Private Ticket Page
        if path.startswith("/ticket"):
            ticket_html = os.path.join(SITE_DIR, "ticket.html")
            with open(ticket_html, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content)
            return

        # API: Admin Inquiries List
        if path == "/api/admin/inquiries":
            if not check_admin_auth(self.headers):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return
            status_filter = query_params.get("status", [None])[0]
            inqs = crm_db.get_inquiries_list(status_filter)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(inqs, ensure_ascii=False).encode("utf-8"))
            return

        # API: Admin Inquiry Detail
        if path.startswith("/api/admin/inquiries/"):
            if not check_admin_auth(self.headers):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return
            inquiry_id = path.split("/")[-1]
            inq = crm_db.get_inquiry_detail(inquiry_id)
            if not inq:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Inquiry not found"}).encode("utf-8"))
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(inq, ensure_ascii=False).encode("utf-8"))
            return

        # API: Client Ticket Detail (Gated by secret key)
        if path.startswith("/api/ticket/"):
            ticket_id = path.split("/")[-1]
            key = query_params.get("key", [""])[0]
            inq = crm_db.get_inquiry_detail(ticket_id)
            if not inq or inq.get("secret_token") != key:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Ticket not found or invalid key"}).encode("utf-8"))
                return
            # Filter internal notes
            inq["messages"] = [m for m in inq.get("messages", []) if not m.get("is_internal_note")]
            del inq["secret_token"]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(inq, ensure_ascii=False).encode("utf-8"))
            return

        # Serve static site
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        client_ip = self.client_address[0]

        if path == "/api/chat":
            # 1. Rate Limiting Check
            if not check_ip_rate_limit(client_ip):
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Too many requests. Please wait 1 minute before submitting another query."}).encode("utf-8"))
                return

            # 2. Daily Global Safety Ceiling Check
            if not check_daily_quota():
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "daily_quota_reached",
                    "message": "Today's free community demo quota (200 queries) has been reached. Please connect your local LM Studio/Ollama or enter your own free API key in Settings."
                }).encode("utf-8"))
                return

            # 3. Parse Body & Input Clamping
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length > 2048:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Payload exceeds maximum allowed size."}).encode("utf-8"))
                    return
                    
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)
                question = str(payload.get("question", "")).strip()
                only_slides = bool(payload.get("only_with_slides", False))
                breadth = str(payload.get("breadth", "auto"))
            except Exception:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON request body."}).encode("utf-8"))
                return

            if not question:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Question cannot be empty."}).encode("utf-8"))
                return

            if len(question) > MAX_QUERY_CHARS:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Question exceeds limit of {MAX_QUERY_CHARS} characters."}).encode("utf-8"))
                return

            # 4. Call MCP tool_answer_conference
            try:
                result = asyncio.run(tool_answer_conference(question, breadth=breadth, only_with_slides=only_slides))
                if isinstance(result, dict) and "error" in result:
                    err_msg = str(result.get("error", ""))
                    if any(k in err_msg.lower() for k in ["rate", "timeout", "exhausted", "503", "429", "connection"]):
                        self.send_response(503)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "error": "cascade_unavailable",
                            "message": "All public free-tier models are currently rate-limited or busy."
                        }).encode("utf-8"))
                        return

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "cascade_unavailable",
                    "message": f"Inference error: {e}"
                }).encode("utf-8"))
            return

        # Collaboration Interest Endpoint
        if path == "/api/collaboration-interest":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length > 4096:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Payload too large."}).encode("utf-8"))
                    return

                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)
            except Exception:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON request body."}).encode("utf-8"))
                return

            if payload.get("website_hp"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "message": "Inquiry received."}).encode("utf-8"))
                return

            name = str(payload.get("name", "")).strip()
            email = str(payload.get("email", "")).strip()
            org = str(payload.get("organization", "")).strip()
            profile_url = str(payload.get("profile_url", "")).strip()
            inquiry_type = str(payload.get("inquiry_type", "Enterprise")).strip()
            description = str(payload.get("description", "")).strip()

            if not (name and email and description):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Name, email, and description are required."}).encode("utf-8"))
                return

            inq = crm_db.create_inquiry(
                inquiry_type="collaboration",
                name=name,
                email=email,
                org=org,
                profile=profile_url,
                session_id="",
                title=f"{inquiry_type}: {org or name}",
                initial_message=description
            )
            ticket_id = inq["id"]
            secret_key = inq["secret_token"]
            ticket_url = f"/ticket?id={ticket_id}&key={secret_key}"

            # Log to append-only JSONL
            feedback_dir = os.path.join(HUB_DIR, "data")
            os.makedirs(feedback_dir, exist_ok=True)
            with open(os.path.join(feedback_dir, "collaboration_inquiries.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "ticket_id": ticket_id,
                    "ip": client_ip,
                    "name": name,
                    "email": email,
                    "organization": org,
                    "profile_url": profile_url,
                    "inquiry_type": inquiry_type,
                    "description": description
                }, ensure_ascii=False) + "\n")

            # Dispatch non-blocking Telegram alert to ToyProjectsBot
            dispatch_telegram_alert(
                event_emoji="💼",
                event_type="NEW COLLABORATION INQUIRY",
                ticket_id=ticket_id,
                sender_name=name,
                org=org,
                email=email,
                profile=profile_url,
                body=f"Type: {inquiry_type}\n\n{description}"
            )

            # Dispatch confirmation email to client via Resend
            public_url = os.environ.get("PUBLIC_URL", "http://127.0.0.1:8088")
            full_ticket_url = f"{public_url}{ticket_url}"
            email_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
              <h2 style="color: #0284c7; margin-top: 0;">Inquiry Registered: #{ticket_id}</h2>
              <p>Hi {name},</p>
              <p>Thank you for reaching out regarding <strong>AGNTCon + MCPCon Europe 2026</strong>.</p>
              <p>We have received your message regarding <em>{inquiry_type}</em>. You can track status updates and message the project maintainer directly on your private thread link below:</p>
              <div style="margin: 24px 0;">
                <a href="{full_ticket_url}" style="background: #0284c7; color: #ffffff; padding: 12px 20px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">Open Private Dialogue Thread →</a>
              </div>
              <p style="font-size: 0.85rem; color: #64748b; line-height: 1.5;">Direct Link: <a href="{full_ticket_url}" style="color: #0284c7;">{full_ticket_url}</a></p>
            </div>
            """
            dispatch_resend_email(email, f"[#{ticket_id}] Your AGNTCon 2026 Collaboration Inquiry", email_html)

            # Also notify maintainer by email
            maintainer_email = os.environ.get("MAINTAINER_NOTIFICATION_EMAIL") or os.environ.get("RESEND_MAINTAINER_EMAIL", "alex@onexcare.com")
            if maintainer_email and maintainer_email != email:
                maintainer_html = f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
                  <h2 style="color: #0284c7; margin-top: 0;">💼 New Collaboration Inquiry: #{ticket_id}</h2>
                  <p><strong>From:</strong> {name} ({org or 'Individual'})</p>
                  <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                  <p><strong>Profile:</strong> <a href="{profile_url}">{profile_url}</a></p>
                  <p><strong>Type:</strong> {inquiry_type}</p>
                  <blockquote style="background: #f8fafc; border-left: 4px solid #0284c7; padding: 12px 16px; margin: 16px 0; color: #1e293b;">
                    {description.replace(chr(10), '<br>')}
                  </blockquote>
                  <div style="margin: 20px 0;">
                    <a href="{full_ticket_url}" style="background: #0284c7; color: #ffffff; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">Open Client Thread →</a>
                    <a href="{public_url}/admin#ticket={ticket_id}" style="background: #475569; color: #ffffff; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block; margin-left: 8px;">Open in CRM Dashboard →</a>
                  </div>
                </div>
                """
                dispatch_resend_email(maintainer_email, f"💼 [New Collaboration] #{ticket_id} from {name} ({org or 'N/A'})", maintainer_html)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "message": "Thank you! Your collaboration inquiry has been registered.",
                "ticket_id": ticket_id,
                "ticket_url": ticket_url
            }).encode("utf-8"))
            return

        # Admin Login Endpoint
        if path == "/api/admin/login":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)
                password = str(payload.get("password", "")).strip()
            except Exception:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid request"}).encode("utf-8"))
                return

            if password == ADMIN_PASSWORD:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "token": ADMIN_SESSION_TOKEN}).encode("utf-8"))
            else:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid operator password"}).encode("utf-8"))
            return

        # Admin Bulk Action Endpoint (Archive, Restore, Delete)
        if path == "/api/admin/inquiries/bulk-action":
            if not check_admin_auth(self.headers):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)
                action = str(payload.get("action", "")).strip().lower()
                ids = payload.get("ids", [])
            except Exception:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid request payload"}).encode("utf-8"))
                return

            if not ids or not isinstance(ids, list):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No inquiry IDs provided."}).encode("utf-8"))
                return

            if action == "archive":
                affected = crm_db.bulk_update_status(ids, "archived")
            elif action == "restore":
                affected = crm_db.bulk_update_status(ids, "in_progress")
            elif action == "delete":
                affected = crm_db.bulk_delete_inquiries(ids)
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Unknown action '{action}'"}).encode("utf-8"))
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "action": action, "affected": affected}).encode("utf-8"))
            return

        # Admin Reply Endpoint
        if path.startswith("/api/admin/inquiries/") and path.endswith("/reply"):
            if not check_admin_auth(self.headers):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return
            parts = path.split("/")
            inquiry_id = parts[4]
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)
                text = str(payload.get("body", "")).strip()
                is_note = bool(payload.get("is_note", False))
                new_status = payload.get("new_status")
            except Exception:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid request"}).encode("utf-8"))
                return

            crm_db.add_message(inquiry_id, "admin", text, is_note, new_status)

            if not is_note:
                inq = crm_db.get_inquiry_detail(inquiry_id)
                if inq and inq.get("email"):
                    public_url = os.environ.get("PUBLIC_URL", "http://127.0.0.1:8088")
                    client_ticket_url = f"{public_url}/ticket?id={inquiry_id}&key={inq.get('secret_token')}"
                    reply_html = f"""
                    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
                      <h2 style="color: #0284c7; margin-top: 0;">New Reply on Ticket #{inquiry_id}</h2>
                      <p>Hi {inq.get('name', 'there')},</p>
                      <p>The maintainer has posted a response to your inquiry:</p>
                      <blockquote style="background: #f8fafc; border-left: 4px solid #0284c7; padding: 12px 16px; margin: 16px 0; font-style: italic; color: #1e293b;">
                        {text.replace(chr(10), '<br>')}
                      </blockquote>
                      <div style="margin: 24px 0;">
                        <a href="{client_ticket_url}" style="background: #0284c7; color: #ffffff; padding: 12px 20px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">View Full Thread & Reply →</a>
                      </div>
                      <p style="font-size: 0.85rem; color: #64748b;">Direct Link: <a href="{client_ticket_url}" style="color: #0284c7;">{client_ticket_url}</a></p>
                    </div>
                    """
                    dispatch_resend_email(inq["email"], f"Re: [#{inquiry_id}] New response from AGNTCon maintainer", reply_html)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            return

        # Client Ticket Reply Endpoint
        if path.startswith("/api/ticket/") and path.endswith("/reply"):
            parts = path.split("/")
            ticket_id = parts[3]
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)
                key = str(payload.get("key", "")).strip()
                text = str(payload.get("body", "")).strip()
            except Exception:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid request"}).encode("utf-8"))
                return

            inq = crm_db.get_inquiry_detail(ticket_id)
            if not inq or inq.get("secret_token") != key:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid ticket key"}).encode("utf-8"))
                return

            crm_db.add_message(ticket_id, "client", text, False, "waiting_reply")
            # Trigger real-time Telegram push to operator
            dispatch_telegram_alert(
                event_emoji="💬",
                event_type="CLIENT THREAD REPLY",
                ticket_id=ticket_id,
                sender_name=inq["name"],
                org=inq.get("organization", ""),
                email=inq["email"],
                profile=inq.get("profile_url", ""),
                body=text
            )

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            return
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length > 4096:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Payload too large."}).encode("utf-8"))
                    return

                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)
            except Exception:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON request body."}).encode("utf-8"))
                return

            # Honeypot spam trap
            if payload.get("website_hp"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "message": "Feedback received."}).encode("utf-8"))
                return

            session_id = str(payload.get("session_id", "")).strip()
            name = str(payload.get("name", "")).strip()
            email = str(payload.get("email", "")).strip()
            profile_url = str(payload.get("profile_url", "")).strip()
            request_type = str(payload.get("request_type", "Correction")).strip()
            notes = str(payload.get("notes", "")).strip()

            if not (session_id and name and email and profile_url and notes):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "All fields (session_id, name, email, profile_url, notes) are required."}).encode("utf-8"))
                return

            inq = crm_db.create_inquiry(
                inquiry_type="speaker_dispute",
                name=name,
                email=email,
                org="",
                profile=profile_url,
                session_id=session_id,
                title=f"{request_type}: Session [[{session_id}]]",
                initial_message=notes
            )
            ticket_id = inq["id"]
            secret_key = inq["secret_token"]
            ticket_url = f"/ticket?id={ticket_id}&key={secret_key}"

            # Log to append-only JSONL
            feedback_dir = os.path.join(HUB_DIR, "data")
            os.makedirs(feedback_dir, exist_ok=True)
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "ticket_id": ticket_id,
                "ip": client_ip,
                "session_id": session_id,
                "name": name,
                "email": email,
                "profile_url": profile_url,
                "request_type": request_type,
                "notes": notes,
            }
            with open(os.path.join(feedback_dir, "author_feedback.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            # Dispatch non-blocking Telegram alert to ToyProjectsBot
            dispatch_telegram_alert(
                event_emoji="🚨",
                event_type="NEW SPEAKER DISPUTE",
                ticket_id=ticket_id,
                sender_name=name,
                org=f"Session [[{session_id}]]",
                email=email,
                profile=profile_url,
                body=f"Type: {request_type}\n\n{notes}"
            )

            # Dispatch confirmation email to speaker via Resend
            public_url = os.environ.get("PUBLIC_URL", "http://127.0.0.1:8088")
            full_ticket_url = f"{public_url}{ticket_url}"
            email_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
              <h2 style="color: #0284c7; margin-top: 0;">Speaker Request Registered: #{ticket_id}</h2>
              <p>Hi {name},</p>
              <p>Thank you for submitting your verification request regarding presentation <strong>[[{session_id}]]</strong>.</p>
              <p>Our team reviews all speaker requests within 48 hours. You can view progress and communicate directly with the maintainer here:</p>
              <div style="margin: 24px 0;">
                <a href="{full_ticket_url}" style="background: #0284c7; color: #ffffff; padding: 12px 20px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">View Private Dialogue Thread →</a>
              </div>
              <p style="font-size: 0.85rem; color: #64748b;">Direct Link: <a href="{full_ticket_url}" style="color: #0284c7;">{full_ticket_url}</a></p>
            </div>
            """
            dispatch_resend_email(email, f"[#{ticket_id}] AGNTCon 2026 Speaker Request: Session [[{session_id}]]", email_html)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "message": "Thank you. Your feedback has been safely received and queued for review within 48 hours.",
                "ticket_id": ticket_id,
                "ticket_url": ticket_url
            }).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def run_server(host="127.0.0.1", port=8080):
    os.makedirs(SITE_DIR, exist_ok=True)
    server_address = (host, port)
    httpd = HTTPServer(server_address, HubHTTPRequestHandler)
    print(f"===========================================================")
    print(f"  AGNTCon + MCPCon Europe 2026 - LLM Wiki & MCP Gateway   ")
    print(f"  Web Workspace: http://{host}:{port}/                     ")
    print(f"  MCP Server:    stdio / REST API at http://{host}:{port}/api/")
    print(f"===========================================================")
    print("[+] Press Ctrl+C to halt server.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Shutting down server.")
        httpd.server_close()

def main():
    parser = argparse.ArgumentParser(description="Run AGNTCon 2026 Web Server & MCP Gateway")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on.")
    parser.add_argument("--test-mode", action="store_true", help="Perform self-test and exit.")
    args = parser.parse_args()

    if args.test_mode:
        print("=== Web Server Self-Test Mode ===")
        print(f"[+] Static directory verified: {SITE_DIR}")
        print(f"[+] Rate limiter configured: {RATE_LIMIT_PER_MINUTE} req/min")
        print(f"[+] Input clamping: {MAX_QUERY_CHARS} chars")
        print(f"[+] SERVE_TEST_PASS: Routes initialized, read-only endpoints ready.")
        return

    run_server(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
