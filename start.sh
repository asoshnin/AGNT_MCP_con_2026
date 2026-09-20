#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8088}"

if fuser "${PORT}/tcp" >/dev/null 2>&1; then
  echo "[!] Port ${PORT} is already in use. Stopping existing process..."
  fuser -k "${PORT}/tcp" >/dev/null 2>&1
  sleep 1
fi

echo "[+] Starting AGNTCon Hub on http://127.0.0.1:${PORT}..."
# SEC-02 Invariant: Scrub ambient development keys from shell environment
nohup env -u NVIDIA_API_KEY -u OPENROUTER_API_KEY -u KILOCODE_API_KEY PYTHONUNBUFFERED=1 "${SCRIPT_DIR}/serve.py" --host 127.0.0.1 --port "${PORT}" > /tmp/agntcon_hub.log 2>&1 &
sleep 1

if curl -s "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
  echo "[✓] Server is online and healthy at http://127.0.0.1:${PORT}"
  echo "    Logs: tail -f /tmp/agntcon_hub.log"
else
  echo "[✗] Failed to verify health endpoint. Check /tmp/agntcon_hub.log"
fi
