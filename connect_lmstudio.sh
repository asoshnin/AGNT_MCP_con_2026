#!/usr/bin/env bash
# Connect LM Studio from Windows PC to Linux local port 1234 via SSH tunnel
set -e

WINDOWS_IP="${1:-192.168.1.11}"
PORT="${2:-1234}"

# Check if port 1234 is already responding locally
if nc -z 127.0.0.1 "$PORT" 2>/dev/null; then
    echo "[✓] Port $PORT is already active on 127.0.0.1."
else
    echo "[+] Establishing background SSH tunnel to Windows PC (alexey@$WINDOWS_IP)..."
    ssh -f -N -L "$PORT:127.0.0.1:$PORT" -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 "alexey@$WINDOWS_IP"
    sleep 1
    echo "[✓] Tunnel established: http://127.0.0.1:$PORT/v1 -> Windows LM Studio ($WINDOWS_IP)."
fi

echo "[*] Testing LM Studio model endpoint..."
MODEL_CHECK=$(curl -s "http://127.0.0.1:$PORT/v1/models" | grep -o "huihui-qwythos-9b-claude-mythos-5-1m-abliterated" || true)
if [ -n "$MODEL_CHECK" ]; then
    echo "[✓] Success! Model '$MODEL_CHECK' is ready on http://127.0.0.1:$PORT/v1"
else
    echo "[!] Connected, but model name 'huihui-qwythos-9b-claude-mythos-5-1m-abliterated' was not found in active model list."
fi
