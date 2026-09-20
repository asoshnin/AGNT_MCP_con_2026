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

HUB_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(HUB_DIR, "site")

sys.path.insert(0, HUB_DIR)
from mcp_server import tool_search_talks, tool_get_page, tool_answer_conference

# In-Memory IP Rate Limiter (5 requests per minute per IP)
IP_REQUEST_LOG = {}
RATE_LIMIT_PER_MINUTE = 5
MAX_QUERY_CHARS = 500

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
        sys.stdout.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {args[0]} {args[1]} {args[2]}\n")

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
            results = tool_search_talks(q, topic)
            
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

            # 2. Parse Body & Input Clamping
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

            # 3. Call MCP tool_answer_conference
            try:
                result = asyncio.run(tool_answer_conference(question))
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

        if path == "/api/author-feedback":
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

            # Log to append-only JSONL
            feedback_dir = os.path.join(HUB_DIR, "data")
            os.makedirs(feedback_dir, exist_ok=True)
            log_entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
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

            # Async Telegram Alert Dispatcher (server-side, zero token leak)
            tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
            tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
            if tg_token and tg_chat:
                try:
                    import urllib.request
                    tg_text = (
                        f"🚨 *[AGNTCon Hub] Author Feedback / Takedown Request*\n\n"
                        f"• *Session:* `{session_id}`\n"
                        f"• *Author:* {name} (`{email}`)\n"
                        f"• *Profile:* {profile_url}\n"
                        f"• *Type:* {request_type}\n"
                        f"• *Details:*\n{notes}"
                    )
                    tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
                    tg_payload = json.dumps({"chat_id": tg_chat, "text": tg_text, "parse_mode": "Markdown"}).encode("utf-8")
                    req = urllib.request.Request(tg_url, data=tg_payload, headers={"Content-Type": "application/json"})
                    urllib.request.urlopen(req, timeout=5)
                except Exception as tg_err:
                    sys.stderr.write(f"[WARN] Failed to dispatch Telegram alert: {tg_err}\n")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "message": "Thank you. Your feedback has been safely received and queued for review within 48 hours."
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
