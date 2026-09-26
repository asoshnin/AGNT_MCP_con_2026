#!/usr/bin/env python3
"""Autonomous Oracle Cloud Anti-Reclamation Load Worker for AGNTCon Hub.

Guarantees 7-day 95th-percentile compute metrics remain >= 20% on non-PAYG Free Tier instances.
If OCI_PAYG_PROTECTED=true, the worker immediately yields (100% exempt from reclamation).
"""

import math
import os
import sqlite3
import sys
import time
from datetime import UTC, datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(HUB_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "infra_history.sqlite")
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


def get_seven_day_metrics(db_path: str = DB_PATH) -> tuple[float, float, int]:
    """Calculates (avg_cpu_load, p95_cpu_load, snapshot_count) over the past 7 days."""
    if not os.path.exists(db_path):
        return 0.0, 0.0, 0

    cutoff = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(f"file:{os.path.abspath(db_path)}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute("SELECT cpu_load_1m FROM snapshots WHERE timestamp >= ? ORDER BY cpu_load_1m ASC;", (cutoff,))
    rows = [r[0] for r in cur.fetchall()]
    conn.close()

    if not rows:
        return 0.0, 0.0, 0

    count = len(rows)
    avg_val = round(sum(rows) / count, 2)
    p95_idx = int(0.95 * count)
    p95_val = round(rows[min(p95_idx, count - 1)], 2)
    return avg_val, p95_val, count


def run_gentle_synthetic_load(duration_minutes: int = 30, target_core_pct: float = 0.22) -> None:
    """Executes a low-priority mathematical loop consuming ~22% CPU."""
    # Set nice to 19 (lowest CPU scheduling priority in Linux)
    try:
        os.nice(19)
    except Exception:
        pass

    end_time = time.time() + (duration_minutes * 60)
    cycle_time = 0.1  # 100ms slice
    work_time = cycle_time * target_core_pct
    sleep_time = cycle_time - work_time

    while time.time() < end_time:
        t0 = time.time()
        while (time.time() - t0) < work_time:
            _ = math.sqrt(12345.6789) * math.sin(0.5)
        time.sleep(sleep_time)


def check_and_apply_anti_reclamation(dry_run: bool = False, check_only: bool = False) -> dict:
    env = load_env()
    is_payg = env.get("OCI_PAYG_PROTECTED", "true").lower() in ("true", "1", "yes")

    avg_cpu, p95_cpu, count = get_seven_day_metrics()

    result = {
        "payg_protected": is_payg,
        "seven_day_avg_cpu": avg_cpu,
        "seven_day_p95_cpu": p95_cpu,
        "sample_count": count,
        "action_taken": "none",
        "status": "Protected (PAYG Exemption Active)" if is_payg else "Monitored (Standard Free Tier)"
    }

    if is_payg:
        result["message"] = "Tenancy has PAYG status. 100% exempt from idle reclamation."
        return result

    # For non-PAYG: check if 95th percentile CPU load is < 0.20 (20% of 1 OCPU)
    if p95_cpu < 0.20 and count > 10:
        result["status"] = "Risk Detected (p95 CPU < 20%)"
        if not dry_run and not check_only:
            result["action_taken"] = "running_synthetic_load_30m"
            run_gentle_synthetic_load(duration_minutes=30, target_core_pct=0.22)
        else:
            result["action_taken"] = "synthetic_load_recommended"
    else:
        result["status"] = "Nominal (>= 20% or gathering baseline)"

    return result


if __name__ == "__main__":
    check_flag = "--check-only" in sys.argv
    dry_flag = "--dry-run" in sys.argv
    res = check_and_apply_anti_reclamation(dry_run=dry_flag, check_only=check_flag)
    print(res)
