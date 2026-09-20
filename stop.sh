#!/usr/bin/env bash
PORT="${1:-8088}"
echo "[+] Stopping server on port ${PORT}..."
fuser -k "${PORT}/tcp" >/dev/null 2>&1 || pkill -f "serve.py.*${PORT}"
echo "[✓] Port ${PORT} freed."
