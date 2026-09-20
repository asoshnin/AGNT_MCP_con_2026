#!/usr/bin/env python3
"""Test Telegram alerting for ToyProjectsBot using credentials in .env."""

import json
import os
import sys
import urllib.request

HUB_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(HUB_DIR, ".env")
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'").strip('"')

token = os.environ.get("TOY_PROJECTS_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TOY_PROJECTS_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
project_name = os.environ.get("PROJECT_NAME", "AGNTCon EU 2026")

if not token or token.startswith("YOUR_") or not chat_id or chat_id.startswith("YOUR_"):
    print("❌ Error: TOY_PROJECTS_BOT_TOKEN or TOY_PROJECTS_CHAT_ID is missing in 02_public_hub/.env")
    print("Please open 02_public_hub/.env and enter your bot token and chat ID.")
    sys.exit(1)

text = (
    f"🤖 *[{project_name}]* · 🚀 *Telegram Alert Test*\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "• *Status:* Connected & Verified ✅\n"
    "• *Bot Identity:* ToyProjectsBot\n\n"
    "_If you see this message, your Telegram alerts for incoming leads, speaker disputes, and client replies are 100% active!_\n\n"
    f"🔗 *Admin Thread:* {os.environ.get('PUBLIC_URL', 'http://127.0.0.1:8088')}/admin"
)

url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req, timeout=5.0) as r:
        print(f"[✓] Success! Test alert delivered to your Telegram (HTTP {r.status}). Check your Telegram app!")
except Exception as e:
    print(f"❌ Telegram API delivery failed: {e}")
