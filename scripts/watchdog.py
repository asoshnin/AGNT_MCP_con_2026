#!/usr/bin/env python3
"""Autonomous Host Health Watchdog & Out-of-Band Telegram Alerting for AGNTCon Hub.

Monitors CPU, RAM, Disk, Systemd services (agntcon-hub, cloudflared), and zombie processes.
Maintains a rolling 7-day snapshot history in SQLite and sends debounced alerts via ToyProjectsBot.
"""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(HUB_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "infra_history.sqlite")
STATE_PATH = os.path.join(DATA_DIR, "watchdog_state.json")
ENV_PATH = os.path.join(HUB_DIR, ".env")


def load_env() -> dict[str, str]:
    env_vars: dict[str, str] = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip("'").strip('"')
    return env_vars


def init_db(db_path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode = WAL;")
    cur.execute("PRAGMA busy_timeout = 5000;")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        cpu_load_1m REAL NOT NULL,
        cpu_load_5m REAL NOT NULL,
        cpu_load_15m REAL NOT NULL,
        ram_used_mb INTEGER NOT NULL,
        ram_total_mb INTEGER NOT NULL,
        ram_pct REAL NOT NULL,
        disk_used_gb REAL NOT NULL,
        disk_total_gb REAL NOT NULL,
        disk_pct REAL NOT NULL,
        hub_ok INTEGER NOT NULL DEFAULT 1,
        tunnel_ok INTEGER NOT NULL DEFAULT 1,
        zombies_count INTEGER NOT NULL DEFAULT 0,
        alert_triggered TEXT
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_ts ON snapshots(timestamp);")
    conn.commit()
    conn.close()


def get_mem_info() -> tuple[int, int, float]:
    """Returns (used_mb, total_mb, pct) using /proc/meminfo."""
    total_kb = 0
    avail_kb = 0
    if os.path.exists("/proc/meminfo"):
        try:
            with open("/proc/meminfo", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total_kb = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        avail_kb = int(line.split()[1])
        except Exception:
            pass

    if total_kb == 0:
        total_kb = 6 * 1024 * 1024  # Default 6 GB fallback

    used_kb = max(0, total_kb - avail_kb)
    total_mb = total_kb // 1024
    used_mb = used_kb // 1024
    pct = round((used_kb / total_kb) * 100, 1) if total_kb > 0 else 0.0
    return used_mb, total_mb, pct


def get_disk_info(path: str = "/") -> tuple[float, float, float]:
    """Returns (used_gb, total_gb, pct) using shutil.disk_usage."""
    try:
        total, used, free = shutil.disk_usage(path)
        total_gb = round(total / (1024**3), 1)
        used_gb = round(used / (1024**3), 1)
        pct = round((used / total) * 100, 1) if total > 0 else 0.0
        return used_gb, total_gb, pct
    except Exception:
        return 0.0, 0.0, 0.0


def get_cpu_load() -> tuple[float, float, float]:
    """Returns 1m, 5m, 15m load average."""
    try:
        return os.getloadavg()
    except Exception:
        return 0.0, 0.0, 0.0


def check_hub_alive(port: int = 8088) -> bool:
    """Performs a local HTTP ping to /api/health."""
    url = f"http://127.0.0.1:{port}/api/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WatchdogLocalPing/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def check_service_active(service_name: str) -> bool:
    """Checks whether a systemd unit is active."""
    try:
        res = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=2.0
        )
        return res.stdout.strip() == "active"
    except Exception:
        # Fallback: check /proc process listing for process name
        try:
            res = subprocess.run(
                ["pgrep", "-f", service_name],
                capture_output=True,
                text=True,
                timeout=2.0
            )
            return len(res.stdout.strip()) > 0
        except Exception:
            return True  # Avoid false alarms if systemctl is unavailable


def count_zombie_processes() -> int:
    """Counts zombie processes (state 'Z')."""
    try:
        res = subprocess.run(
            ["ps", "-eo", "stat"],
            capture_output=True,
            text=True,
            timeout=2.0
        )
        stats = res.stdout.splitlines()
        return sum(1 for s in stats if s.strip().startswith("Z"))
    except Exception:
        return 0


def get_top_processes(limit: int = 7) -> list[dict[str, Any]]:
    """Inspects top processes by CPU and RAM with command sanitization."""
    procs: list[dict[str, Any]] = []
    try:
        res = subprocess.run(
            ["ps", "-eo", "pid,user,%cpu,%mem,stat,comm", "--sort=-%cpu"],
            capture_output=True,
            text=True,
            timeout=2.0
        )
        lines = res.stdout.strip().splitlines()
        for line in lines[1:limit + 1]:
            parts = line.split(None, 5)
            if len(parts) >= 6:
                comm = parts[5].strip()
                # Sanitize arguments/tokens
                comm = comm.split("?")[0]
                procs.append({
                    "pid": int(parts[0]),
                    "user": parts[1],
                    "cpu": float(parts[2]),
                    "mem": float(parts[3]),
                    "stat": parts[4],
                    "comm": comm[:60]
                })
    except Exception:
        pass
    return procs


def load_state() -> dict[str, Any]:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"active_incidents": {}, "last_check": None}


def save_state(state: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(STATE_PATH)), exist_ok=True)
    temp_path = STATE_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(temp_path, STATE_PATH)


def send_telegram_alert(message: str, env_vars: dict[str, str] | None = None) -> bool:
    """Dispatches a Markdown alert to Telegram via ToyProjectsBot."""
    env = env_vars or load_env()
    token = env.get("TOY_PROJECTS_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TOY_PROJECTS_CHAT_ID") or env.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id or token.startswith("YOUR_") or chat_id.startswith("YOUR_"):
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=5.0) as r:
            return r.status == 200
    except Exception as e:
        sys.stderr.write(f"[Watchdog] Telegram delivery failed: {e}\n")
        return False


def collect_snapshot(port: int = 8088) -> dict[str, Any]:
    """Collects current metrics snapshot."""
    cpu_1m, cpu_5m, cpu_15m = get_cpu_load()
    ram_used, ram_total, ram_pct = get_mem_info()
    disk_used, disk_total, disk_pct = get_disk_info()
    hub_ok = 1 if check_hub_alive(port) else 0
    tunnel_ok = 1 if check_service_active("cloudflared") else 0
    zombies = count_zombie_processes()

    return {
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_load_1m": round(cpu_1m, 2),
        "cpu_load_5m": round(cpu_5m, 2),
        "cpu_load_15m": round(cpu_15m, 2),
        "ram_used_mb": ram_used,
        "ram_total_mb": ram_total,
        "ram_pct": ram_pct,
        "disk_used_gb": disk_used,
        "disk_total_gb": disk_total,
        "disk_pct": disk_pct,
        "hub_ok": hub_ok,
        "tunnel_ok": tunnel_ok,
        "zombies_count": zombies,
        "alert_triggered": None
    }


def record_snapshot(snap: dict[str, Any], db_path: str = DB_PATH) -> None:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO snapshots (
            timestamp, cpu_load_1m, cpu_load_5m, cpu_load_15m,
            ram_used_mb, ram_total_mb, ram_pct,
            disk_used_gb, disk_total_gb, disk_pct,
            hub_ok, tunnel_ok, zombies_count, alert_triggered
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            snap["timestamp"], snap["cpu_load_1m"], snap["cpu_load_5m"], snap["cpu_load_15m"],
            snap["ram_used_mb"], snap["ram_total_mb"], snap["ram_pct"],
            snap["disk_used_gb"], snap["disk_total_gb"], snap["disk_pct"],
            snap["hub_ok"], snap["tunnel_ok"], snap["zombies_count"], snap["alert_triggered"]
        )
    )
    # Prune records older than 7 days
    cutoff = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("DELETE FROM snapshots WHERE timestamp < ?;", (cutoff,))
    conn.commit()
    conn.close()


def run_watchdog_cycle(dry_run: bool = False, test_alert: bool = False) -> dict[str, Any]:
    env = load_env()
    snap = collect_snapshot()
    state = load_state()
    now_ts = time.time()
    now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    if test_alert:
        msg = (
            "🤖 *[AGNTCon Hub]* · 🔔 *Watchdog Alert Test*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Timestamp:* `{now_str}`\n"
            f"• *Host:* `agntcon-hub-prod` (Oracle A1 Amsterdam)\n"
            f"• *CPU Load:* `{snap['cpu_load_1m']}` (1m), `{snap['cpu_load_5m']}` (5m)\n"
            f"• *RAM:* `{snap['ram_pct']}%` ({snap['ram_used_mb']} / {snap['ram_total_mb']} MB)\n"
            f"• *Disk:* `{snap['disk_pct']}%` ({snap['disk_used_gb']} / {snap['disk_total_gb']} GB)\n"
            f"• *Web Hub:* {'🟢 Online' if snap['hub_ok'] else '🔴 Down'}\n"
            f"• *Cloudflare Tunnel:* {'🟢 Active' if snap['tunnel_ok'] else '🔴 Inactive'}\n\n"
            "_All telemetry signals nominal._"
        )
        delivered = send_telegram_alert(msg, env)
        return {"status": "ok", "test_alert_delivered": delivered, "snapshot": snap}

    # Evaluate Incidents
    incidents: list[tuple[str, str, str, int]] = []  # (key, title, severity, cooldown_sec)
    if snap["hub_ok"] == 0:
        incidents.append(("hub_down", "Web Hub Service Unreachable (HTTP Ping Failed)", "🚨 CRITICAL (P0)", 1800))
    if snap["tunnel_ok"] == 0:
        incidents.append(("tunnel_down", "Cloudflare Edge Tunnel Disconnected", "🚨 CRITICAL (P0)", 1800))
    if snap["disk_pct"] >= 85.0:
        incidents.append(("disk_high", f"Storage Warning: Disk at {snap['disk_pct']}%", "⚠️ WARNING (P1)", 3600))
    if snap["ram_pct"] >= 90.0:
        incidents.append(("ram_high", f"Memory Warning: RAM at {snap['ram_pct']}%", "⚠️ WARNING (P1)", 3600))
    if snap["zombies_count"] > 0:
        incidents.append(("zombies", f"Hanging / Zombie Processes Detected ({snap['zombies_count']})", "🧟 WARNING (P2)", 3600))

    active_incidents = state.get("active_incidents", {})
    alert_triggered_keys = []

    # Process Current Incidents
    for key, desc, sev, cooldown in incidents:
        alert_triggered_keys.append(key)
        incident_info = active_incidents.get(key)
        should_send = False

        if not incident_info:
            # New incident!
            should_send = True
            active_incidents[key] = {"first_seen": now_str, "last_alert_ts": now_ts}
        else:
            # Existing incident: check cooldown
            last_ts = incident_info.get("last_alert_ts", 0)
            if (now_ts - last_ts) >= cooldown:
                should_send = True
                incident_info["last_alert_ts"] = now_ts

        if should_send and not dry_run:
            msg = (
                f"{sev.split()[0]} *[AGNTCon Hub]* · *System Incident Alert*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Severity:* {sev}\n"
                f"• *Condition:* {desc}\n"
                f"• *Timestamp:* `{now_str}`\n"
                f"• *Metrics:* CPU `{snap['cpu_load_1m']}`, RAM `{snap['ram_pct']}%`, Disk `{snap['disk_pct']}%`\n\n"
                "🔗 *Inspect Admin:* https://agntcon-demo.vwoosh.com/admin"
            )
            send_telegram_alert(msg, env)

    # Process Resolved Incidents (Recovery notifications)
    resolved_keys = [k for k in list(active_incidents.keys()) if k not in alert_triggered_keys]
    for r_key in resolved_keys:
        if not dry_run:
            rec_msg = (
                "🟢 *[AGNTCon Hub]* · *Incident Resolved*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Issue:* `{r_key}` has returned to nominal operating thresholds.\n"
                f"• *Resolved At:* `{now_str}`\n\n"
                "_System state verified healthy._"
            )
            send_telegram_alert(rec_msg, env)
        del active_incidents[r_key]

    state["active_incidents"] = active_incidents
    state["last_check"] = now_str
    snap["alert_triggered"] = ",".join(alert_triggered_keys) if alert_triggered_keys else None

    if not dry_run:
        save_state(state)
        record_snapshot(snap)

    return snap


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    is_test = "--test-alert" in sys.argv
    res = run_watchdog_cycle(dry_run=is_dry, test_alert=is_test)
    print(json.dumps(res, indent=2))
