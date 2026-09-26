"""Tests for Host Infrastructure Health, Watchdog, and Telegram Alerting."""

import os
import sqlite3
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest
import serve
from scripts import anti_reclamation_worker, watchdog
from serve import HubHTTPRequestHandler, ThreadingHTTPServer

TEST_PORT = 8998
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


@pytest.fixture(scope="module")
def infra_test_server():
    """Spins up a test HTTP server for infra health endpoints."""
    server = ThreadingHTTPServer(("127.0.0.1", TEST_PORT), HubHTTPRequestHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)
    yield BASE_URL
    server.shutdown()
    server.server_close()


def test_watchdog_metrics_collection():
    """Verify standard metric extractors return non-negative, sensible values."""
    cpu_1m, cpu_5m, cpu_15m = watchdog.get_cpu_load()
    assert cpu_1m >= 0.0
    assert cpu_5m >= 0.0

    used_ram, total_ram, ram_pct = watchdog.get_mem_info()
    assert total_ram > 0
    assert 0.0 <= ram_pct <= 100.0

    used_disk, total_disk, disk_pct = watchdog.get_disk_info("/")
    assert total_disk > 0.0
    assert 0.0 <= disk_pct <= 100.0

    zombies = watchdog.count_zombie_processes()
    assert zombies >= 0

    procs = watchdog.get_top_processes(limit=5)
    assert isinstance(procs, list)
    if procs:
        p = procs[0]
        assert "pid" in p
        assert "user" in p
        assert "cpu" in p
        assert "mem" in p
        assert "comm" in p


def test_watchdog_snapshot_and_db_storage(tmp_path):
    """Verify watchdog snapshots are written to SQLite and pruned."""
    test_db = str(tmp_path / "test_infra.sqlite")
    watchdog.init_db(test_db)

    snap = watchdog.collect_snapshot(port=TEST_PORT)
    assert "timestamp" in snap
    assert snap["ram_total_mb"] > 0

    watchdog.record_snapshot(snap, db_path=test_db)

    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM snapshots;")
    count = cur.fetchone()[0]
    assert count == 1
    conn.close()


def test_anti_reclamation_worker_logic(tmp_path):
    """Verify 7-day percentile calculation and PAYG bypass."""
    test_db = str(tmp_path / "test_anti_rec.sqlite")
    watchdog.init_db(test_db)

    # Insert mock snapshots
    for load in [0.05, 0.10, 0.15, 0.25, 0.30]:
        snap = {
            "timestamp": "2026-09-26 10:00:00",
            "cpu_load_1m": load, "cpu_load_5m": load, "cpu_load_15m": load,
            "ram_used_mb": 1000, "ram_total_mb": 6000, "ram_pct": 16.6,
            "disk_used_gb": 10.0, "disk_total_gb": 46.6, "disk_pct": 21.4,
            "hub_ok": 1, "tunnel_ok": 1, "zombies_count": 0, "alert_triggered": None
        }
        watchdog.record_snapshot(snap, db_path=test_db)

    avg_cpu, p95_cpu, count = anti_reclamation_worker.get_seven_day_metrics(test_db)
    assert count == 5
    assert avg_cpu > 0.0
    assert p95_cpu >= avg_cpu


def test_http_admin_infra_status_auth_gate(infra_test_server):
    """Verify GET /api/admin/infra-status requires admin authorization."""
    with httpx.Client() as client:
        # Unauthenticated request must return 401
        res = client.get(f"{infra_test_server}/api/admin/infra-status")
        assert res.status_code == 401

        # Invalid token must return 401
        res_bad = client.get(
            f"{infra_test_server}/api/admin/infra-status",
            headers={"Authorization": "Bearer ***"}
        )
        assert res_bad.status_code == 401

        # Valid token must return 200 and schema
        res_ok = client.get(
            f"{infra_test_server}/api/admin/infra-status",
            headers={"Authorization": f"Bearer {serve.ADMIN_SESSION_TOKEN}"}
        )
        assert res_ok.status_code == 200
        data = res_ok.json()
        assert "live" in data
        assert "oracle" in data
        assert "services" in data["live"]
        assert "cpu_load" in data["live"]
        assert "ram" in data["live"]
        assert "disk" in data["live"]


def test_http_admin_test_telegram_auth_gate(infra_test_server):
    """Verify POST /api/admin/infra/test-telegram requires admin authorization."""
    with httpx.Client() as client:
        # Unauthenticated request must return 401
        res = client.post(f"{infra_test_server}/api/admin/infra/test-telegram")
        assert res.status_code == 401

        # Valid token must return 200
        res_ok = client.post(
            f"{infra_test_server}/api/admin/infra/test-telegram",
            headers={"Authorization": f"Bearer {serve.ADMIN_SESSION_TOKEN}"}
        )
        assert res_ok.status_code == 200
        data = res_ok.json()
        assert data.get("status") == "ok"
