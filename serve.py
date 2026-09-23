#!/usr/bin/env python3
"""Lightweight Unified Web Server & MCP Client Gateway for AGNTCon EU 2026.

Hosts:
1. Static Web Workspace (site/index.html + assets) on port 8080.
2. REST API endpoints (/api/search, /api/page, /api/chat) forwarding to MCP tools.
3. 4-Layer Security: Input clamping (500 chars), IP rate limiter, and clean error handling.
"""

import os
import sys

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
            os.execv(venv_py, [venv_py, *sys.argv])

import argparse
import asyncio
import concurrent.futures
import csv
import hashlib
import html
import io
import json
import re
import secrets
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

try:
    from http.server import ThreadingHTTPServer
except ImportError:
    ThreadingHTTPServer = HTTPServer

HUB_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(HUB_DIR, "site")

sys.path.insert(0, HUB_DIR)
import analytics_db
import crm_db
import hub_incremental
from cloudflare_analytics import fetch_cloudflare_edge_analytics
from mcp_server import tool_answer_conference, tool_get_page, tool_search_talks
from scripts.generate_speaker_tokens import verify_token
from scripts.rescan_sched_slides import rescan_sched
from submissions_db import SubmissionsDB

SESSION_ID_REGEX = re.compile(r"^[0-9A-Za-z]{5}$")
CONTRIBUTE_RATE_LIMIT = {}

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "agntcon2026admin")
ADMIN_SESSION_TOKEN = secrets.token_hex(24)

PENDING_SUBMISSIONS_DIR = os.environ.get(
    "PENDING_SUBMISSIONS_DIR", os.path.join(HUB_DIR, "data", "submissions", "pending")
)
CANONICAL_SLIDES_DIR = os.environ.get(
    "CANONICAL_SLIDES_DIR", os.path.join(SITE_DIR, "assets", "slides")
)

def get_pending_submissions_dir() -> Path:
    return Path(os.environ.get("PENDING_SUBMISSIONS_DIR", os.path.join(HUB_DIR, "data", "submissions", "pending"))).resolve()

def get_canonical_slides_dir() -> Path:
    return Path(os.environ.get("CANONICAL_SLIDES_DIR", os.path.join(SITE_DIR, "assets", "slides"))).resolve()

def is_safe_slide_path(file_path: str) -> bool:
    if not file_path:
        return False
    try:
        target = Path(file_path).resolve()
        pending = get_pending_submissions_dir()
        canonical = get_canonical_slides_dir()
        return target.is_relative_to(pending) or target.is_relative_to(canonical)
    except Exception:
        return False

def load_env_file():
    env_path = os.path.join(HUB_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, encoding="utf-8") as f:
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


def sanitize_csv_cell(value: Any) -> str:
    """Fortified CSV formula injection defense (Sprint 19: SEC-01).

    Prepend single quote if stripped cell begins with =, +, -, @, \\t, \\r, or \\n.
    """
    s = str(value if value is not None else "")
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r", "\n"):
        return f"'{s}"
    stripped_spaces = s.lstrip(" ")
    if stripped_spaces and stripped_spaces[0] in ("=", "+", "-", "@", "\t", "\r", "\n"):
        return f"'{s}"
    return s


def check_admin_auth(headers, query_params: dict | None = None) -> bool:
    auth_header = headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token == ADMIN_SESSION_TOKEN:
            return True
    if query_params:
        query_token = query_params.get("token", [""])[0].strip()
        if query_token and query_token == ADMIN_SESSION_TOKEN:
            return True
    return False

def get_canonical_session_metadata(session_id: str) -> dict[str, Any]:
    """Retrieves official Sched metadata for a session from sessions.json or archive/wiki fallbacks."""
    candidate_paths = [
        os.environ.get("SESSIONS_JSON_PATH"),
        os.path.join(HUB_DIR, "data", "sessions.json"),
        os.path.join(HUB_DIR, "sessions.json"),
        os.path.join(HUB_DIR, "..", "01_harvester_pipeline", "data", "sessions.json"),
    ]
    for p in candidate_paths:
        if p and os.path.exists(p):
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and session_id in data:
                    item = data[session_id]
                    speakers_val = item.get("session_speakers") or item.get("speakers", [])
                    if isinstance(speakers_val, str):
                        speakers_list = [speakers_val]
                    else:
                        speakers_list = [
                            s.get("name") if isinstance(s, dict) else str(s)
                            for s in speakers_val
                        ]
                    return {
                        "session_title": item.get("session_title") or item.get("title", ""),
                        "session_speakers": speakers_list,
                        "session_company": item.get("session_company") or item.get("company", ""),
                        "session_abstract": item.get("session_abstract") or item.get("abstract", ""),
                        "sched_url": item.get("sched_url", ""),
                    }
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("id") == session_id:
                            speakers_val = item.get("session_speakers") or item.get("speakers", [])
                            if isinstance(speakers_val, str):
                                speakers_list = [speakers_val]
                            else:
                                speakers_list = [
                                    s.get("name") if isinstance(s, dict) else str(s)
                                    for s in speakers_val
                                ]
                            return {
                                "session_title": item.get("session_title") or item.get("title", ""),
                                "session_speakers": speakers_list,
                                "session_company": item.get("session_company") or item.get("company", ""),
                                "session_abstract": item.get("session_abstract") or item.get("abstract", ""),
                                "sched_url": item.get("sched_url", ""),
                            }
            except Exception:
                pass

    # Fallback: 01_harvester_pipeline/archive/talks/{session_id}.json
    talk_path = os.path.join(HUB_DIR, "..", "01_harvester_pipeline", "archive", "talks", f"{session_id}.json")
    if os.path.exists(talk_path):
        try:
            with open(talk_path, encoding="utf-8") as f:
                talk = json.load(f)
            spk_raw = talk.get("speakers", [])
            spk_names = []
            orgs = []
            for s in spk_raw:
                if isinstance(s, dict):
                    if s.get("name"):
                        spk_names.append(s["name"])
                    if s.get("org"):
                        orgs.append(s["org"])
                elif isinstance(s, str):
                    spk_names.append(s)
            return {
                "session_title": talk.get("title", ""),
                "session_speakers": spk_names,
                "session_company": ", ".join(orgs) if orgs else "",
                "session_abstract": talk.get("abstract", ""),
                "sched_url": talk.get("sched_url", ""),
            }
        except Exception:
            pass

    # Fallback: wiki/index.json
    index_path = os.path.join(HUB_DIR, "wiki", "index.json")
    if os.path.exists(index_path):
        try:
            with open(index_path, encoding="utf-8") as f:
                catalog = json.load(f)
            for item in catalog:
                if item.get("id") == session_id:
                    return {
                        "session_title": item.get("title", ""),
                        "session_speakers": item.get("speakers", []),
                        "session_company": "",
                        "session_abstract": item.get("relevance_rationale", "") or item.get("one_paragraph", ""),
                        "sched_url": item.get("sched_url", ""),
                    }
        except Exception:
            pass

    return {
        "session_title": "",
        "session_speakers": [],
        "session_company": "",
        "session_abstract": "",
        "sched_url": "",
    }

def enrich_submission(sub: dict[str, Any]) -> dict[str, Any]:
    sess_meta = get_canonical_session_metadata(sub.get("session_id", ""))
    sub["session_title"] = sess_meta.get("session_title", "")
    sub["session_speakers"] = sess_meta.get("session_speakers", [])
    sub["session_company"] = sess_meta.get("session_company", "")
    sub["session_abstract"] = sess_meta.get("session_abstract", "")
    sub["sched_url"] = sess_meta.get("sched_url", "")

    # Domain match heuristic
    email = sub.get("submitter_email", "")
    sub["domain_matched"] = False
    if "@" in email:
        domain = email.split("@")[-1].lower()
        combined_text = (
            sub["session_title"] + " " + " ".join(sub["session_speakers"]) + " " + sub["session_company"]
        ).lower()
        domain_name = domain.split(".")[0]
        if len(domain_name) > 2 and domain_name in combined_text:
            sub["domain_matched"] = True
    return sub

def compute_heuristic_relevance(title: str, abstract: str, slide_text: str) -> tuple[int, str, str]:
    combined_ref = f"{title} {abstract}".lower()
    stopwords = {
        "the", "and", "for", "that", "this", "with", "from", "are", "have", "you",
        "your", "all", "can", "will", "our", "about", "how", "what", "when", "why",
        "into", "more", "then", "them", "some", "such", "than", "were", "been", "being",
        "not", "they", "their", "there", "which", "would", "could", "should", "also"
    }
    ref_words = {w for w in re.findall(r"[a-z0-9_\-]{3,}", combined_ref) if w not in stopwords}
    slide_words = {w for w in re.findall(r"[a-z0-9_\-]{3,}", slide_text.lower()) if w not in stopwords}

    if not ref_words or not slide_words:
        return 0, "MISMATCH", "Insufficient text to establish topic correlation."

    intersection = ref_words & slide_words
    recall = len(intersection) / len(ref_words)
    jaccard = len(intersection) / len(ref_words | slide_words)
    combined = (recall * 0.70) + (jaccard * 0.30)
    score = int(min(100, max(0, round(combined * 135))))

    if score >= 80:
        verdict = "MATCH"
        rationale = f"Verified via semantic keyword alignment ({score}% topical overlap) between official abstract and slides."
    elif score >= 50:
        verdict = "AMBIGUOUS"
        rationale = f"Partial semantic alignment ({score}% overlap) between abstract and slide text; manual review recommended."
    else:
        verdict = "MISMATCH"
        rationale = f"Low keyword correlation ({score}% overlap) between abstract and slide text; potential session mismatch."

    return score, verdict, rationale

def verify_submission_authenticity(
    title: str,
    abstract: str,
    slide_text: str,
    speaker: str = "",
) -> tuple[int, str, str]:
    """Evaluates submission relevance/authenticity via free LLM cascade or heuristic fallback."""
    if not slide_text or not slide_text.strip():
        return (
            0,
            "MISMATCH",
            "Extracted presentation slide text is empty or unavailable for verification."
        )

    # 1. Attempt free LLM cascade if zero-cost gateway key is present
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    kilocode_key = os.environ.get("KILOCODE_API_KEY")
    nvidia_key = os.environ.get("NVIDIA_API_KEY")

    gateways = []
    if openrouter_key and openrouter_key != "mock_free_key":
        gateways.append({
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
            },
            "model": "openrouter/free",
        })
    if kilocode_key:
        gateways.append({
            "url": "https://api.kilo.ai/api/gateway/chat/completions",
            "headers": {
                "Authorization": f"Bearer {kilocode_key}",
                "Content-Type": "application/json",
            },
            "model": "kilo-auto/free",
        })
    if nvidia_key:
        gateways.append({
            "url": "https://integrate.api.nvidia.com/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {nvidia_key}",
                "Content-Type": "application/json",
            },
            "model": "nvidia/llama-3.1-nemotron-70b-instruct",
        })

    system_prompt = (
        "You are an objective academic and technical reviewer for AGNTCon EU 2026.\n"
        "Compare the following Official Conference Abstract against the Extracted Presentation Slide Text.\n"
        "Determine:\n"
        "1. Does this uploaded deck authentically belong to this session?\n"
        "2. Relevance score between 0 and 100.\n"
        "3. Verdict: MATCH (>=80), AMBIGUOUS (50-79), or MISMATCH (<50).\n"
        "4. Concise 2-sentence rationale.\n\n"
        "Output strictly valid JSON:\n"
        "{\n"
        '  "relevance_score": 95,\n'
        '  "authenticity_verdict": "MATCH",\n'
        '  "authenticity_rationale": "The slides directly discuss the MCP protocol and context engineering, fully aligning with the abstract."\n'
        "}"
    )
    user_prompt = (
        f"<official_session>\n"
        f"Title: {title}\n"
        f"Speaker: {speaker}\n"
        f"Official Abstract: {abstract[:2000]}\n"
        f"</official_session>\n\n"
        f"<extracted_slide_text>\n"
        f"{slide_text[:3000]}\n"
        f"</extracted_slide_text>"
    )

    for gw in gateways:
        try:
            req_body = json.dumps({
                "model": gw["model"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 400,
            }).encode("utf-8")
            req = urllib.request.Request(gw["url"], data=req_body, headers=gw["headers"])
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"].strip()
                    if "```" in content:
                        content = re.sub(r"```(?:json)?", "", content).replace("```", "").strip()
                    parsed_json = json.loads(content)
                    raw_score = int(parsed_json.get("relevance_score", 0))
                    score = max(0, min(100, raw_score))
                    verdict = str(parsed_json.get("authenticity_verdict", "AMBIGUOUS")).upper()
                    if verdict not in ("MATCH", "AMBIGUOUS", "MISMATCH"):
                        verdict = "MATCH" if score >= 80 else ("AMBIGUOUS" if score >= 50 else "MISMATCH")
                    rationale = str(parsed_json.get("authenticity_rationale", "")).strip()
                    if rationale:
                        return score, verdict, rationale
        except Exception:
            pass

    # Fallback to deterministic keyword overlap heuristic
    return compute_heuristic_relevance(title=title, abstract=abstract, slide_text=slide_text)

def dispatch_resend_email(to_email: str, subject: str, html_body: str):
    api_key = os.environ.get("RESEND_API_KEY")
    from_email = os.environ.get("RESEND_FROM_EMAIL", "Alexey Soshnin <alex@onexcare.com>")
    reply_to = os.environ.get("RESEND_REPLY_TO", "alex@vwoosh.com")
    if not api_key or api_key == "YOUR_RESEND_KEY_HERE":
        sys.stdout.write(f"[INFO] RESEND_API_KEY not configured. Skipping email to {to_email}.\n")
        return

    try:
        import urllib.request
        url = "https://api.resend.com/emails"
        payload_dict = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        if reply_to:
            payload_dict["reply_to"] = reply_to
        payload = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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

# Active FIFO Semaphore Queue Tracking (Sprint P-04e)
MAX_CONCURRENT_CHATS = 2
MAX_WAITING_REQUESTS = 10
ACTIVE_TASKS = 0
WAITING_TASKS = 0
QUEUE_LOCK = threading.Lock()
CHAT_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_CHATS)

ASYNC_LOOP = None

def get_or_create_loop():
    global ASYNC_LOOP
    if ASYNC_LOOP is None:
        ASYNC_LOOP = asyncio.new_event_loop()
        t = threading.Thread(target=ASYNC_LOOP.run_forever, daemon=True, name="AsyncChatWorker")
        t.start()
    return ASYNC_LOOP

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

DAILY_SALT = secrets.token_hex(16)
SALT_CREATION_DAY = time.strftime("%Y-%m-%d")
TELEMETRY_LOG: dict[str, list[float]] = {}
TELEMETRY_RATE_LIMIT_PER_MINUTE = 60

def get_daily_salt() -> str:
    global DAILY_SALT, SALT_CREATION_DAY
    today = time.strftime("%Y-%m-%d")
    if today != SALT_CREATION_DAY:
        DAILY_SALT = secrets.token_hex(16)
        SALT_CREATION_DAY = today
    return DAILY_SALT

def get_session_hash(client_ip: str) -> str:
    salt = get_daily_salt()
    return hashlib.sha256(f"{client_ip}_{salt}".encode()).hexdigest()[:12]

def check_telemetry_rate_limit(session_hash: str) -> bool:
    now = time.time()
    if session_hash not in TELEMETRY_LOG:
        TELEMETRY_LOG[session_hash] = []
    TELEMETRY_LOG[session_hash] = [t for t in TELEMETRY_LOG[session_hash] if now - t < 60]
    if len(TELEMETRY_LOG[session_hash]) >= TELEMETRY_RATE_LIMIT_PER_MINUTE:
        return False
    TELEMETRY_LOG[session_hash].append(now)
    return True


def check_contribute_rate_limit(ip: str) -> bool:
    """Max 5 upload attempts per hour per client IP (FR-1.2)."""
    now = time.time()
    if ip not in CONTRIBUTE_RATE_LIMIT:
        CONTRIBUTE_RATE_LIMIT[ip] = []
    CONTRIBUTE_RATE_LIMIT[ip] = [t for t in CONTRIBUTE_RATE_LIMIT[ip] if now - t < 3600]
    if len(CONTRIBUTE_RATE_LIMIT[ip]) >= 5:
        return False
    CONTRIBUTE_RATE_LIMIT[ip].append(now)
    return True

def get_real_client_ip(headers, client_address) -> str:
    cf_ip = headers.get("CF-Connecting-IP")
    if cf_ip and cf_ip.strip():
        return cf_ip.strip()
    xff = headers.get("X-Forwarded-For")
    if xff and xff.strip():
        return xff.split(",")[0].strip()
    if isinstance(client_address, (list, tuple)) and len(client_address) > 0:
        return str(client_address[0]).strip()
    return str(client_address).strip() if client_address else "127.0.0.1"


def get_effective_client_ip(headers, fallback_ip: str) -> str:
    return get_real_client_ip(headers, (fallback_ip,))

class HubHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

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

        # Short Link Redirection for Speaker Slides Upload (Sprint 19)
        if path == "/c":
            tok = query_params.get("t", [""])[0]
            target_url = f"/contribute?token={tok}" if tok else "/contribute"
            self.send_response(302)
            self.send_header("Location", target_url)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return

        # Contribute Landing Redirect to Index with Token
        if path == "/contribute":
            tok = query_params.get("token", [""])[0]
            target_url = f"/?token={tok}" if tok else "/"
            self.send_response(302)
            self.send_header("Location", target_url)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return

        # Health endpoint
        if path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "agntcon-2026-hub", "version": "3.0.0"}).encode("utf-8"))
            return

        # Queue Status Telemetry (Sprint P-04e)
        if path == "/api/queue-status":
            upstream_queue = os.environ.get("UPSTREAM_QUEUE_URL")
            if upstream_queue:
                try:
                    req = urllib.request.Request(upstream_queue)
                    with urllib.request.urlopen(req, timeout=4.0) as u_res:
                        self.send_response(u_res.status)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.send_header("Cache-Control", "no-store, max-age=0")
                        self.end_headers()
                        self.wfile.write(u_res.read())
                        return
                except Exception:
                    pass

            with QUEUE_LOCK:
                status_str = "busy" if ACTIVE_TASKS >= MAX_CONCURRENT_CHATS else "ready"
                resp_data = {
                    "active_tasks": ACTIVE_TASKS,
                    "waiting_tasks": WAITING_TASKS,
                    "waiting_depth": WAITING_TASKS,
                    "queue_depth": WAITING_TASKS,
                    "max_concurrent": MAX_CONCURRENT_CHATS,
                    "status": status_str
                }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(resp_data).encode("utf-8"))
            return

        # Search API
        if path == "/api/search":
            q = query_params.get("q", [""])[0][:MAX_QUERY_CHARS]
            topic = query_params.get("topic", [None])[0]
            only_slides = query_params.get("only_with_slides", ["0"])[0] in ("1", "true", "True")
            limit_val = int(query_params.get("limit", ["200"])[0])
            results = tool_search_talks(q, topic=topic, only_with_slides=only_slides, limit=limit_val)
            
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
            category_filter = query_params.get("category", [None])[0]
            inqs = crm_db.get_inquiries_list(status_filter, category_filter)
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

        # API: Admin Analytics Summary (Zero-PII Operator Dashboard)
        if path == "/api/admin/analytics-summary":
            if not check_admin_auth(self.headers):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return
            try:
                summary = analytics_db.get_analytics_summary()
                summary["cloudflare"] = fetch_cloudflare_edge_analytics(days=7)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(summary, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to get analytics summary: {e}"}).encode("utf-8"))
            return

        # API: Admin Contacts Summary (Sprint 18)
        if path == "/api/admin/contacts-summary":
            if not check_admin_auth(self.headers, query_params):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return

            summary_path = Path(HUB_DIR) / "data" / "contacts_summary.json"
            if summary_path.exists():
                try:
                    with open(summary_path, encoding="utf-8") as sf:
                        summary_data = json.load(sf)
                except Exception as e:
                    summary_data = {"error": f"Failed to read summary: {e}"}
            else:
                summary_data = {
                    "updated_at": None,
                    "total_speakers": 0,
                    "total_organizers": 0,
                    "cohort_organizers_count": 0,
                    "cohort_missing_slides_count": 0,
                    "cohort_slides_available_count": 0,
                }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(summary_data, ensure_ascii=False).encode("utf-8"))
            return

        # API: Admin Contacts Export (Sprint 19: FR-P46)
        if path == "/api/admin/contacts/export":
            if not check_admin_auth(self.headers, query_params):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return

            cohort_filter = query_params.get("cohort", ["cohort_organizers"])[0]
            export_format = query_params.get("format", ["csv"])[0].lower()

            contacts_path = Path(HUB_DIR) / "data" / "contacts.json"
            all_records = []
            if contacts_path.exists():
                try:
                    with open(contacts_path, encoding="utf-8") as cf:
                        cdata = json.load(cf)

                    raw_orgs = list(cdata.get("organizers", []))
                    raw_orgs.extend(cdata.get("external_organizers", []))

                    for org in raw_orgs:
                        org_cohort = org.get("cohort", "cohort_organizers")
                        if cohort_filter not in ("all", "all_organizers") and org_cohort != cohort_filter:
                            continue

                        v_status = org.get("verification_status")
                        if not v_status and isinstance(org.get("verification"), dict):
                            v_status = org.get("verification", {}).get("status")
                        if not v_status:
                            v_status = "unverified"

                        rec = {
                            "Name": org.get("name", ""),
                            "Role": org.get("role", ""),
                            "Company": org.get("company", ""),
                            "Conference": org.get("conference_name") or org.get("conference", "AGNTCon Europe 2026"),
                            "Social_URL": org.get("linkedin_url") or org.get("twitter_url") or org.get("social_url") or "",
                            "Slide_Status": org.get("slide_status", "N/A"),
                            "Verification_Status": v_status,
                        }
                        all_records.append(rec)
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Failed to export contacts: {e}"}).encode("utf-8"))
                    return

            if export_format == "json":
                out_bytes = json.dumps(all_records, indent=2, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{cohort_filter}.json"')
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(out_bytes)
                return
            else:
                # Default format: csv
                output = io.StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
                fieldnames = ["Name", "Role", "Company", "Conference", "Social_URL", "Slide_Status", "Verification_Status"]
                writer.writerow(fieldnames)
                for rec in all_records:
                    row = [sanitize_csv_cell(rec.get(fn, "")) for fn in fieldnames]
                    writer.writerow(row)

                csv_bytes = output.getvalue().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{cohort_filter}.csv"')
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(csv_bytes)
                return

        # API: Admin Submissions List (FR-4.2)
        if path == "/api/admin/submissions":
            if not check_admin_auth(self.headers, query_params):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return
            status_filter = query_params.get("status", [None])[0]
            db = SubmissionsDB()
            submissions = [enrich_submission(s) for s in db.get_submissions(status_filter)]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(submissions, ensure_ascii=False).encode("utf-8"))
            return

        # API: Admin Submissions Download, Preview & Detail (Sprint 14)
        if path.startswith("/api/admin/submissions/"):
            parts = path.strip("/").split("/")
            # e.g. ["api", "admin", "submissions", sub_id] or ["api", "admin", "submissions", sub_id, "download"]
            if len(parts) >= 4 and parts[0] == "api" and parts[1] == "admin" and parts[2] == "submissions":
                sub_id = parts[3]
                action = parts[4] if len(parts) >= 5 else None

                if not check_admin_auth(self.headers, query_params):
                    self.send_response(401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                    return

                db = SubmissionsDB()
                sub = db.get_submission(sub_id)
                if not sub:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Submission not found"}).encode("utf-8"))
                    return

                if action is None:
                    enriched = enrich_submission(sub)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(enriched, ensure_ascii=False).encode("utf-8"))
                    return

                if action in ("download", "preview"):
                    file_path = sub.get("file_path")
                    if not file_path:
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "No file associated with this submission"}).encode("utf-8"))
                        return

                    # Path containment check (SEC-S14-01)
                    if not is_safe_slide_path(file_path):
                        self.send_response(403)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "Forbidden: Path traversal outside allowed storage directories"}).encode("utf-8"))
                        return

                    if not os.path.isfile(file_path):
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "File not found on disk"}).encode("utf-8"))
                        return

                    file_size = os.path.getsize(file_path)

                    if action == "download":
                        raw_name = sub.get("submitter_name", "submitter").strip()
                        safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", raw_name)
                        filename = f"{sub.get('session_id', 'session')}_{safe_name}.pdf"

                        self.send_response(200)
                        self.send_header("Content-Type", "application/pdf")
                        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                        self.send_header("Content-Length", str(file_size))
                        self.send_header("Cache-Control", "private, no-store")
                        self.send_header("Referrer-Policy", "no-referrer")
                        self.end_headers()
                        with open(file_path, "rb") as f:
                            while chunk := f.read(65536):
                                self.wfile.write(chunk)
                        return

                    elif action == "preview":
                        self.send_response(200)
                        self.send_header("Content-Type", "application/pdf")
                        self.send_header("Content-Disposition", "inline")
                        self.send_header("Content-Length", str(file_size))
                        self.send_header("X-Frame-Options", "SAMEORIGIN")
                        self.send_header("Referrer-Policy", "no-referrer")
                        self.end_headers()
                        with open(file_path, "rb") as f:
                            while chunk := f.read(65536):
                                self.wfile.write(chunk)
                        return

        # API: Contribute Session Info (FR-4.1)
        if path == "/api/contribute/session-info":
            session_id = query_params.get("session_id", [""])[0].strip()
            token = query_params.get("token", [""])[0].strip()

            if token:
                valid, token_sid = verify_token(token)
                if valid and not session_id:
                    session_id = token_sid

            if not session_id or not SESSION_ID_REGEX.match(session_id):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid or missing session_id format (must match ^[0-9A-Za-z]{5}$)"}).encode("utf-8"))
                return

            index_path = os.path.join(HUB_DIR, "wiki", "index.json")
            found_session = None
            if os.path.exists(index_path):
                try:
                    with open(index_path, encoding="utf-8") as f:
                        catalog = json.load(f)
                    for item in catalog:
                        if item.get("id") == session_id:
                            found_session = item
                            break
                except Exception:
                    pass

            if not found_session:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Session [[{session_id}]] not found in conference index."}).encode("utf-8"))
                return

            resp_payload = {
                "id": found_session.get("id"),
                "title": found_session.get("title"),
                "speakers": found_session.get("speakers", []),
                "abstract": found_session.get("one_paragraph", ""),
                "has_slides": bool(found_session.get("has_slides") or found_session.get("file_name")),
                "sched_url": found_session.get("sched_url"),
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload, ensure_ascii=False).encode("utf-8"))
            return

        # Serve static site
        return super().do_GET()

    def do_POST(self):
        global WAITING_TASKS, ACTIVE_TASKS
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)
        client_ip = get_real_client_ip(self.headers, self.client_address)

        if path == "/api/chat":
            upstream_chat = os.environ.get("UPSTREAM_CHAT_URL")
            if upstream_chat:
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length) if content_length > 0 else b""
                    req = urllib.request.Request(
                        upstream_chat,
                        data=body,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": self.headers.get("User-Agent", "ConferenceHubProxy")
                        }
                    )
                    with urllib.request.urlopen(req, timeout=45.0) as u_res:
                        self.send_response(u_res.status)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(u_res.read())
                        return
                except urllib.error.HTTPError as he:
                    self.send_response(he.code)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(he.read())
                    return
                except Exception as e:
                    self.send_response(503)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Upstream proxy failed: {e}"}).encode("utf-8"))
                    return

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
                if content_length > 4096:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Payload exceeds maximum allowed size."}).encode("utf-8"))
                    return
                    
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)
                question = str(payload.get("question", "")).strip()
                only_slides = bool(payload.get("only_with_slides", False))
                breadth = str(payload.get("breadth", "auto"))
                user_profile = payload.get("user_profile")
                user_context = None
                if isinstance(user_profile, dict):
                    role = str(user_profile.get("role", "")).strip()
                    focus = ", ".join(user_profile.get("focus_areas", []))
                    obj = str(user_profile.get("objective", "")).strip()
                    notes = str(user_profile.get("custom_notes", "")).strip()
                    user_context = f"Role: {role} | Focus: {focus} | Objective: {obj}"
                    if notes:
                        user_context += f" | Technical Goals/Questions: {notes}"
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

            # 4. Queue Capacity Gate (Max 10 waiting)
            with QUEUE_LOCK:
                if WAITING_TASKS >= MAX_WAITING_REQUESTS:
                    self.send_response(429)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Retry-After", "15")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": "queue_full",
                        "message": "Chat inference queue is at maximum capacity (10 waiting). Please try again in 15 seconds."
                    }).encode("utf-8"))
                    return
                WAITING_TASKS += 1

            # 5. Call MCP tool_answer_conference via Async Semaphore Queue
            loop = get_or_create_loop()

            async def _execute_chat():
                global ACTIVE_TASKS, WAITING_TASKS
                acquired = False
                try:
                    async with CHAT_SEMAPHORE:
                        acquired = True
                        with QUEUE_LOCK:
                            WAITING_TASKS = max(0, WAITING_TASKS - 1)
                            ACTIVE_TASKS += 1
                        try:
                            return await asyncio.wait_for(
                                tool_answer_conference(
                                    question,
                                    breadth=breadth,
                                    only_with_slides=only_slides,
                                    user_context=user_context
                                ),
                                timeout=45.0
                            )
                        finally:
                            with QUEUE_LOCK:
                                ACTIVE_TASKS = max(0, ACTIVE_TASKS - 1)
                finally:
                    if not acquired:
                        with QUEUE_LOCK:
                            WAITING_TASKS = max(0, WAITING_TASKS - 1)

            try:
                future = asyncio.run_coroutine_threadsafe(
                    asyncio.wait_for(_execute_chat(), timeout=45.0),
                    loop
                )
                result = future.result(timeout=46.0)
            except (concurrent.futures.TimeoutError, TimeoutError):
                self.send_response(504)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "gateway_timeout",
                    "message": "Inference request timed out after 45 seconds in queue/generation."
                }).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "cascade_unavailable",
                    "message": f"Inference execution error: {e}"
                }).encode("utf-8"))
                return

            if isinstance(result, dict) and "error" in result:
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": result.get("error", "cascade_unavailable"),
                    "message": result.get("message", "All public free-tier models are currently rate-limited or busy."),
                    "citations": result.get("citations", [])
                }).encode("utf-8"))
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
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
            maintainer_email = os.environ.get("MAINTAINER_NOTIFICATION_EMAIL") or os.environ.get("RESEND_MAINTAINER_EMAIL", "alex@vwoosh.com")
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

        # Speaker Feedback / Dispute Endpoint
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

            # Also notify maintainer by email
            maintainer_email = os.environ.get("MAINTAINER_NOTIFICATION_EMAIL") or os.environ.get("RESEND_MAINTAINER_EMAIL", "alex@vwoosh.com")
            if maintainer_email and maintainer_email != email:
                maintainer_html = f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
                  <h2 style="color: #ef4444; margin-top: 0;">🚨 New Speaker Dispute: #{ticket_id}</h2>
                  <p><strong>Session:</strong> [[{session_id}]]</p>
                  <p><strong>Author/Speaker:</strong> {name}</p>
                  <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                  <p><strong>Profile:</strong> <a href="{profile_url}">{profile_url}</a></p>
                  <p><strong>Type:</strong> {request_type}</p>
                  <blockquote style="background: #f8fafc; border-left: 4px solid #ef4444; padding: 12px 16px; margin: 16px 0; color: #1e293b;">
                    {notes.replace(chr(10), '<br>')}
                  </blockquote>
                  <div style="margin: 20px 0;">
                    <a href="{full_ticket_url}" style="background: #0284c7; color: #ffffff; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">Open Client Thread →</a>
                    <a href="{public_url}/admin#ticket={ticket_id}" style="background: #475569; color: #ffffff; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block; margin-left: 8px;">Open in CRM Dashboard →</a>
                  </div>
                </div>
                """
                dispatch_resend_email(maintainer_email, f"🚨 [Speaker Dispute] #{ticket_id} for [[{session_id}]] from {name}", maintainer_html)

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

        # Telemetry Ingestion Endpoint (Zero-PII & Abuse Protected)
        if path == "/api/telemetry":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 1024:
                self.send_response(413)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Payload exceeds 1024 bytes ceiling"}).encode("utf-8"))
                return

            try:
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
                payload = json.loads(body) if body else {}
            except Exception:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Malformed JSON payload"}).encode("utf-8"))
                return

            event_type = str(payload.get("event_type", "")).strip()
            if event_type not in analytics_db.ALLOWED_EVENTS:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Invalid event type: '{event_type}'"}).encode("utf-8"))
                return

            real_ip = get_real_client_ip(self.headers, self.client_address)
            ignored_ips_raw = os.environ.get("ANALYTICS_IGNORE_IPS", "")
            ignored_ips = {ip.strip() for ip in ignored_ips_raw.split(",") if ip.strip()}

            is_internal_header = (
                self.headers.get("X-Internal-Test") == "1"
                or self.headers.get("X-Internal-Agent") == "true"
            )
            ua = self.headers.get("User-Agent", "").lower()
            is_bot_tester = any(b in ua for b in ["pytest", "playwright", "openclaw", "curl", "bot"])

            if real_ip in ignored_ips or is_internal_header or is_bot_tester:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ignored", "reason": "internal_traffic"}).encode("utf-8"))
                return

            session_hash = get_session_hash(real_ip)

            if not check_telemetry_rate_limit(session_hash):
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Rate limit exceeded. Max 60 events per minute."}).encode("utf-8"))
                return

            country = self.headers.get("CF-IPCountry", "XX").strip()
            referrer = self.headers.get("Referer", self.headers.get("Referrer", "direct")).strip()
            metadata = payload.get("metadata")

            try:
                analytics_db.record_event(
                    session_hash=session_hash,
                    event_type=event_type,
                    country=country,
                    referrer=referrer,
                    metadata=metadata,
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Internal database error: {e}"}).encode("utf-8"))
            return

        # Admin Analytics Reset Endpoint (Purges test events & resets autoincrement sequence)
        if path == "/api/admin/analytics-reset":
            if not check_admin_auth(self.headers):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return
            try:
                deleted_rows = analytics_db.reset_analytics_events()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "deleted_rows": deleted_rows}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to reset analytics events: {e}"}).encode("utf-8"))
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

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            return

        # Community Contribution Upload Endpoint (FR-1.1 - FR-1.5)
        if path == "/api/contribute/upload":
            if not check_contribute_rate_limit(client_ip):
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Rate limit exceeded: maximum 5 uploads per hour per IP."}).encode("utf-8"))
                return

            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Content-Type must be multipart/form-data"}).encode("utf-8"))
                return

            try:
                content_length = int(self.headers.get("Content-Length", 0))
            except Exception:
                content_length = 0

            max_allowed_bytes = 35 * 1024 * 1024
            if content_length > max_allowed_bytes:
                self.send_response(413)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Payload exceeds 35MB limit."}).encode("utf-8"))
                return

            boundary_str = None
            for p in content_type.split(";"):
                p = p.strip()
                if p.startswith("boundary="):
                    boundary_str = p.split("=", 1)[1].strip("\"'")
                    break

            if not boundary_str:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing boundary in multipart/form-data"}).encode("utf-8"))
                return

            boundary_bytes = boundary_str.encode("latin1")
            raw_body = self.rfile.read(content_length)

            # Parse multipart parts
            parts = raw_body.split(b"--" + boundary_bytes)
            form_fields = {}
            uploaded_filename = None
            uploaded_bytes = None

            for part in parts:
                if not part or part in (b"--\r\n", b"--", b"\r\n"):
                    continue
                if part.startswith(b"\r\n"):
                    part = part[2:]
                if part.endswith(b"\r\n"):
                    part = part[:-2]
                h_blob, _, d_blob = part.partition(b"\r\n\r\n")
                h_text = h_blob.decode("latin1", errors="replace")

                m_name = re.search(r"name=\"([^\"]+)\"", h_text, re.IGNORECASE)
                if not m_name:
                    continue
                fname = m_name.group(1)
                m_file = re.search(r"filename=\"([^\"]*)\"", h_text, re.IGNORECASE)
                if m_file:
                    uploaded_filename = m_file.group(1)
                    uploaded_bytes = d_blob
                else:
                    form_fields[fname] = d_blob.decode("utf-8", errors="replace").strip()

            session_id = form_fields.get("session_id", "").strip()
            token = form_fields.get("token", "").strip()
            if token and not session_id:
                valid, tok_sid = verify_token(token)
                if valid:
                    session_id = tok_sid

            if not session_id or not SESSION_ID_REGEX.match(session_id):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid session_id. Must match ^[0-9A-Za-z]{5}$"}).encode("utf-8"))
                return

            submitter_name = form_fields.get("submitter_name", "").strip()
            submitter_email = form_fields.get("submitter_email", "").strip()
            submitter_role = form_fields.get("submitter_role", "speaker").strip()
            presentation_url = form_fields.get("presentation_url", form_fields.get("source_url", "")).strip()

            if not submitter_name or not submitter_email:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "submitter_name and submitter_email are required"}).encode("utf-8"))
                return

            # Submission ID format: sub_<session_id>_<hex>
            sub_id = f"sub_{session_id}_{secrets.token_hex(4)}"
            pending_dir = os.path.join(HUB_DIR, "data", "submissions", "pending", sub_id)
            os.makedirs(pending_dir, exist_ok=True)

            sub_type = "pdf" if (uploaded_bytes and len(uploaded_bytes) > 0) else "url"
            dest_file_path = None
            file_hash = None
            file_size = 0
            page_count = 0
            text_yield = 0
            ocr_required = False
            risk_score = "clean"
            injection_details = None
            extracted_sample = ""
            status = "pending"

            if sub_type == "pdf":
                dest_file_path = os.path.join(pending_dir, "upload.tmp")
                with open(dest_file_path, "wb") as f_out:
                    f_out.write(uploaded_bytes)

                file_size = len(uploaded_bytes)
                file_hash = hashlib.sha256(uploaded_bytes).hexdigest()

                # Run Sandboxed Subprocess Worker (FR-2)
                worker_script = os.path.join(HUB_DIR, "scripts", "extract_pdf_worker.py")
                cmd = [sys.executable, worker_script, dest_file_path, "120"]
                try:
                    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20.0)
                    if proc.stdout:
                        try:
                            scan_res = json.loads(proc.stdout)
                            page_count = scan_res.get("page_count", 0)
                            text_yield = scan_res.get("text_yield_chars", 0)
                            ocr_required = bool(scan_res.get("ocr_required", False))
                            risk_score = scan_res.get("injection_risk_score", "clean")
                            injection_details = scan_res.get("injection_details")
                            extracted_sample = scan_res.get("sample_text", "")
                            if scan_res.get("status") == "quarantined":
                                status = "quarantined"
                        except Exception:
                            pass
                    if proc.returncode != 0 and status != "quarantined":
                        status = "quarantined"
                except subprocess.TimeoutExpired:
                    status = "quarantined"
                    risk_score = "critical"
                    injection_details = json.dumps(["Worker timeout exceeded 20s"])
                except Exception as e:
                    status = "quarantined"
                    injection_details = json.dumps([str(e)])

            db = SubmissionsDB()
            client_ip_hash = hashlib.sha256(f"{client_ip}_{get_daily_salt()}".encode()).hexdigest()[:12]
            user_agent = self.headers.get("User-Agent", "")[:200]

            db.insert_submission({
                "id": sub_id,
                "session_id": session_id,
                "token": token or None,
                "submitter_name": submitter_name,
                "submitter_email": submitter_email,
                "submitter_role": submitter_role,
                "submission_type": sub_type,
                "source_url": presentation_url or None,
                "file_path": dest_file_path,
                "file_hash": file_hash,
                "file_size_bytes": file_size,
                "page_count": page_count,
                "text_yield_chars": text_yield,
                "ocr_required": ocr_required,
                "injection_risk_score": risk_score,
                "injection_details": injection_details,
                "status": status,
                "client_ip_hash": client_ip_hash,
                "user_agent": user_agent,
                "draft_summary": extracted_sample[:500] if extracted_sample else "",
            })

            # Telegram operator alert
            dispatch_telegram_alert(
                event_emoji="📥",
                event_type="NEW COMMUNITY CONTENT SUBMISSION",
                ticket_id=sub_id,
                sender_name=submitter_name,
                org=f"Session [[{session_id}]] ({submitter_role})",
                email=submitter_email,
                profile=presentation_url or uploaded_filename or "PDF File",
                body=f"Type: {sub_type} | Risk: {risk_score} | Pages: {page_count} | Status: {status}"
            )

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "received",
                "submission_id": sub_id,
                "quarantined": status == "quarantined",
                "message": "Presentation received and queued for admin verification."
            }).encode("utf-8"))
            return

        # Admin Approve Submission Endpoint (FR-4.3)
        if path.startswith("/api/admin/submissions/") and path.endswith("/approve"):
            if not check_admin_auth(self.headers, query_params):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return

            sub_id = path.split("/")[4]
            db = SubmissionsDB()
            sub = db.get_submission(sub_id)
            if not sub:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Submission not found"}).encode("utf-8"))
                return

            sess_id = sub["session_id"]
            # 1. Promote PDF file if present
            target_slide_path = os.path.join(SITE_DIR, "assets", "slides", f"{sess_id}.pdf")
            os.makedirs(os.path.dirname(target_slide_path), exist_ok=True)

            slides_text = sub.get("draft_summary", "")
            if sub.get("file_path") and os.path.exists(sub["file_path"]):
                try:
                    shutil.copy2(sub["file_path"], target_slide_path)
                except Exception as e:
                    sys.stderr.write(f"[WARN] Failed to copy slide to target: {e}\n")

            # 2. Incremental RAG Upsert
            summary_draft = sub.get("draft_summary", "")
            rag_result = hub_incremental.incremental_upsert(
                session_id=sess_id,
                slides_text=slides_text,
                summary=summary_draft,
                hub_dir=HUB_DIR,
            )

            # 3. Update status in submissions.sqlite
            db.update_status(sub_id, "approved")

            # 4. Cleanup pending folder
            if sub.get("file_path"):
                p_dir = os.path.dirname(sub["file_path"])
                if os.path.isdir(p_dir) and "pending" in p_dir:
                    shutil.rmtree(p_dir, ignore_errors=True)

            # 5. Dispatch confirmation email with Instant AI Dossier and Revocation URL
            to_email = sub.get("submitter_email")
            if to_email:
                public_url = os.environ.get("PUBLIC_URL", "https://agntcon.vwoosh.com")
                dossier_html = f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
                  <h2 style="color: #0284c7; margin-top: 0;">Presentation Approved & Live: [[{sess_id}]]</h2>
                  <p>Hi {sub.get('submitter_name')},</p>
                  <p>Your slides for <strong>[[{sess_id}]]</strong> have been reviewed, security-cleared, and indexed into the AGNTCon Intelligence Hub.</p>
                  <h3>Instant AI Dossier</h3>
                  <p>Your session is now actively grounded in the MCP and RAG knowledge base.</p>
                  <div style="margin: 24px 0;">
                    <a href="{public_url}/#session-{sess_id}" style="background: #0284c7; color: #ffffff; padding: 12px 20px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">View Live Session →</a>
                  </div>
                </div>
                """
                dispatch_resend_email(to_email, f"[Approved] AGNTCon EU 2026: Slides live for [[{sess_id}]]", dossier_html)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "approved",
                "session_id": sess_id,
                "submission_id": sub_id,
                "rag_result": rag_result,
            }).encode("utf-8"))
            return

        # Admin Reject Submission Endpoint (FR-4.4)
        if path.startswith("/api/admin/submissions/") and path.endswith("/reject"):
            if not check_admin_auth(self.headers, query_params):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return

            sub_id = path.split("/")[4]
            db = SubmissionsDB()
            sub = db.get_submission(sub_id)
            if not sub:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Submission not found"}).encode("utf-8"))
                return

            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body) if body else {}
                reason = payload.get("reason", "Rejected by administrator")
            except Exception:
                reason = "Rejected by administrator"

            # Unlink pending file
            if sub.get("file_path"):
                p_dir = os.path.dirname(sub["file_path"])
                if os.path.isdir(p_dir) and "pending" in p_dir:
                    shutil.rmtree(p_dir, ignore_errors=True)

            db.update_status(sub_id, "rejected", rejection_reason=reason)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "rejected",
                "submission_id": sub_id,
                "reason": reason,
            }).encode("utf-8"))
            return

        # Admin Verify Submission Relevance (Sprint 14 FR-3)
        if path.startswith("/api/admin/submissions/") and path.endswith("/verify-relevance"):
            if not check_admin_auth(self.headers, query_params):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return

            parts = path.strip("/").split("/")
            if len(parts) < 5:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid URL"}).encode("utf-8"))
                return

            sub_id = parts[3]
            db = SubmissionsDB()
            sub = db.get_submission(sub_id)
            if not sub:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Submission not found"}).encode("utf-8"))
                return

            force = query_params.get("force", ["0"])[0] == "1"
            if not force and sub.get("relevance_score") is not None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "relevance_score": sub["relevance_score"],
                    "authenticity_verdict": sub["authenticity_verdict"],
                    "authenticity_rationale": sub["authenticity_rationale"],
                    "cached": True
                }, ensure_ascii=False).encode("utf-8"))
                return

            sess_meta = get_canonical_session_metadata(sub.get("session_id", ""))
            abstract = sess_meta.get("session_abstract", "")
            title = sess_meta.get("session_title", "")
            slide_text = sub.get("draft_summary", "")

            if not slide_text and sub.get("file_path") and os.path.exists(sub["file_path"]):
                try:
                    txt_path = os.path.join(os.path.dirname(sub["file_path"]), "extracted.txt")
                    if os.path.exists(txt_path):
                        with open(txt_path, encoding="utf-8", errors="ignore") as tf:
                            slide_text = tf.read()
                except Exception:
                    pass

            score, verdict, rationale = verify_submission_authenticity(
                title=title,
                abstract=abstract,
                slide_text=slide_text,
                speaker=sub.get("submitter_name", ""),
            )
            db.update_verification(sub_id, score, verdict, rationale)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "relevance_score": score,
                "authenticity_verdict": verdict,
                "authenticity_rationale": rationale,
                "cached": False
            }, ensure_ascii=False).encode("utf-8"))
            return

        # Admin Reply to Submitter via CRM Bridge (Sprint 14 FR-4)
        if path.startswith("/api/admin/submissions/") and path.endswith("/reply"):
            if not check_admin_auth(self.headers, query_params):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return

            parts = path.strip("/").split("/")
            if len(parts) < 5:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid URL"}).encode("utf-8"))
                return

            sub_id = parts[3]
            db = SubmissionsDB()
            sub = db.get_submission(sub_id)
            if not sub:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Submission not found"}).encode("utf-8"))
                return

            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"
                body_json = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                body_json = {}

            message = body_json.get("message", "").strip()
            if not message:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "message is required"}).encode("utf-8"))
                return

            subject = body_json.get("subject", "").strip()
            if not subject:
                subject = f"Regarding your AGNTCon 2026 presentation submission [[{sub.get('session_id', '')}]]"

            to_email = sub.get("submitter_email", "")
            submitter_name = sub.get("submitter_name", "Submitter")
            email_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
              <h2 style="color: #0284c7; margin-top: 0;">Message from AGNTCon Program Committee</h2>
              <p>Hi {html.escape(submitter_name)},</p>
              <p>Regarding your submission for session <strong>[[{html.escape(sub.get('session_id', ''))}]]</strong>:</p>
              <div style="white-space: pre-wrap; background: #f8fafc; padding: 16px; border-radius: 6px; border-left: 4px solid #0284c7; margin: 16px 0; color: #1e293b;">{html.escape(message)}</div>
              <p style="color: #64748b; font-size: 13px; margin-top: 24px;">AGNTCon &amp; MCPCon Europe 2026 Organizing Committee</p>
            </div>
            """
            dispatch_resend_email(to_email, subject, email_html)

            inq = crm_db.create_inquiry(
                inquiry_type="Submission Review",
                name=submitter_name,
                email=to_email,
                session_id=sub.get("session_id", ""),
                title=subject,
                initial_message=f"Review dialogue for submission {sub_id}",
            )
            crm_db.add_message(inq["id"], sender_type="admin", body=message, is_note=False)

            db.update_crm_inquiry(sub_id, inq["id"])

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "sent",
                "inquiry_id": inq["id"],
                "recipient": to_email,
            }, ensure_ascii=False).encode("utf-8"))
            return

        # Admin Sched Re-Scan Endpoint (Sprint 17)
        if path == "/api/admin/rescan-sched":
            if not check_admin_auth(self.headers, query_params):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return

            try:
                rescan_result = rescan_sched(hub_dir=HUB_DIR, delay_s=0.2)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(rescan_result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to execute Sched re-scan: {e}"}).encode("utf-8"))
            return

        # Admin Refresh Contacts Endpoint (Sprint 18)
        if path == "/api/admin/refresh-contacts":
            if not check_admin_auth(self.headers, query_params):
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return

            try:
                sys.path.insert(0, str(Path(HUB_DIR) / "scripts"))
                try:
                    from extract_contacts import harvest_contacts
                except ImportError:
                    from scripts.extract_contacts import harvest_contacts

                result = harvest_contacts(hub_dir=HUB_DIR, delay_s=0.3)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Failed to refresh contacts: {e}"}).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()

def run_server(host="127.0.0.1", port=8080):
    os.makedirs(SITE_DIR, exist_ok=True)
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, HubHTTPRequestHandler)
    print("===========================================================")
    print("  AGNTCon + MCPCon Europe 2026 - LLM Wiki & MCP Gateway   ")
    print(f"  Web Workspace: http://{host}:{port}/                     ")
    print(f"  MCP Server:    stdio / REST API at http://{host}:{port}/api/")
    print("===========================================================")
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
        print("[+] SERVE_TEST_PASS: Routes initialized, read-only endpoints ready.")
        return

    run_server(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
