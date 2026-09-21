"""Tests for Zero-PII Engagement Analytics and Operator Dashboard."""

import sqlite3
import threading
import time

import analytics_db
import httpx
import pytest
import serve
from serve import HubHTTPRequestHandler, ThreadingHTTPServer

TEST_PORT = 8996
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


@pytest.fixture(scope="module")
def analytics_test_server():
    """Spins up a lightweight ThreadingHTTPServer instance for analytics HTTP tests."""
    server = ThreadingHTTPServer(("127.0.0.1", TEST_PORT), HubHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.3)
    yield BASE_URL
    server.shutdown()
    server.server_close()


def test_analytics_db_init_and_wal_mode(temp_analytics_db):
    """Verify SQLite WAL mode, schema, and indexes."""
    conn = sqlite3.connect(temp_analytics_db)
    cur = conn.cursor()

    # Check journal mode is WAL
    cur.execute("PRAGMA journal_mode;")
    mode = cur.fetchone()[0]
    assert mode.lower() == "wal"

    # Check table structure
    cur.execute("PRAGMA table_info(events);")
    columns = {col[1]: col[2] for col in cur.fetchall()}
    assert "id" in columns
    assert "timestamp" in columns
    assert "session_hash" in columns
    assert "event_type" in columns
    assert "country" in columns
    assert "referrer" in columns
    assert "metadata" in columns

    # Check indexes exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='index';")
    indexes = {row[0] for row in cur.fetchall()}
    assert "idx_events_timestamp" in indexes
    assert "idx_events_type" in indexes
    assert "idx_events_country" in indexes
    conn.close()


def test_record_all_allowlisted_events(temp_analytics_db):
    """Verify all 7 allowlisted event types can be recorded."""
    events = [
        ("page_view", None),
        ("search", {"query": "mcp architecture", "result_count": 5}),
        ("talk_opened", {"talk_id": "2RBBJ"}),
        ("track_curate", {"threshold": 75, "talk_count": 8}),
        ("track_export_obsidian", {"talk_count": 8}),
        ("track_export_pdf", {"talk_count": 8}),
        ("chat_query", {"tier": "cloud", "breadth": "auto"}),
    ]

    for etype, meta in events:
        eid = analytics_db.record_event(
            session_hash="a1b2c3d4e5f6",
            event_type=etype,
            country="nl",
            referrer="https://linkedin.com",
            metadata=meta,
            db_path=temp_analytics_db,
        )
        assert eid > 0

    summary = analytics_db.get_analytics_summary(temp_analytics_db)
    assert summary["kpis"]["total_events"] == 7
    assert summary["kpis"]["engaged_actions"] == 6
    assert summary["kpis"]["unique_visitors_all"] == 1
    assert summary["kpis"]["exports_count"] == 2
    assert summary["kpis"]["chat_queries_count"] == 1
    assert summary["kpis"]["talk_views_count"] == 1
    assert summary["kpis"]["searches_count"] == 1
    assert summary["kpis"]["curate_count"] == 1


def test_record_invalid_event_raises(temp_analytics_db):
    """Ensure non-allowlisted events are rejected."""
    with pytest.raises(ValueError, match="Invalid event type"):
        analytics_db.record_event(
            session_hash="test_session",
            event_type="malicious_event_injection",
            db_path=temp_analytics_db,
        )


def test_country_and_referrer_sanitization(temp_analytics_db):
    """Verify country codes are sanitized to 2 uppercase chars or XX, and referrers clamped."""
    eid1 = analytics_db.record_event(
        session_hash="sess1",
        event_type="page_view",
        country="de",
        referrer="direct",
        db_path=temp_analytics_db,
    )
    eid2 = analytics_db.record_event(
        session_hash="sess2",
        event_type="page_view",
        country="UNKNOWN_LONG_STRING",
        referrer="https://example.com/" + ("a" * 500),
        db_path=temp_analytics_db,
    )
    assert eid1 > 0
    assert eid2 > 0

    conn = analytics_db.get_db(temp_analytics_db)
    cur = conn.cursor()
    cur.execute("SELECT country, referrer FROM events WHERE id = ?;", (eid1,))
    r1 = cur.fetchone()
    assert r1["country"] == "DE"

    cur.execute("SELECT country, referrer FROM events WHERE id = ?;", (eid2,))
    r2 = cur.fetchone()
    assert r2["country"] == "XX"
    assert len(r2["referrer"]) <= 255
    conn.close()


def test_empty_analytics_summary(temp_analytics_db):
    """Verify empty database returns clean zeroed metrics without errors."""
    summary = analytics_db.get_analytics_summary(temp_analytics_db)
    assert summary["kpis"]["unique_visitors_24h"] == 0
    assert summary["kpis"]["unique_visitors_all"] == 0
    assert summary["kpis"]["total_events"] == 0
    assert summary["kpis"]["engaged_actions"] == 0
    assert len(summary["conversion_funnel"]) == 5
    assert len(summary["geo_distribution"]) == 0
    assert len(summary["top_talks"]) == 0
    assert len(summary["top_searches"]) == 0
    assert len(summary["hourly_activity"]) == 24


def test_daily_salt_and_session_hash():
    """Verify daily salt rotation and non-reversible session hash generation."""
    salt1 = serve.get_daily_salt()
    assert len(salt1) >= 16

    h1 = serve.get_session_hash("192.168.1.50")
    h2 = serve.get_session_hash("192.168.1.50")
    h3 = serve.get_session_hash("10.0.0.1")

    assert len(h1) == 12
    assert h1 == h2
    assert h1 != h3
    assert "192.168.1.50" not in h1


def test_telemetry_rate_limiter():
    """Verify in-memory 60 events/minute rate limiting per session hash."""
    test_hash = "ratelimit_test"
    serve.TELEMETRY_LOG.pop(test_hash, None)

    for _ in range(60):
        assert serve.check_telemetry_rate_limit(test_hash) is True

    # 61st event within the same minute must be rejected
    assert serve.check_telemetry_rate_limit(test_hash) is False


def test_http_telemetry_post_and_country_enrichment(analytics_test_server, temp_analytics_db):
    """Verify HTTP POST /api/telemetry processes Cloudflare CF-IPCountry header and records event."""
    with httpx.Client() as client:
        payload = {
            "event_type": "page_view",
            "metadata": {"source": "unit_test"},
        }
        res = client.post(
            f"{analytics_test_server}/api/telemetry",
            json=payload,
            headers={
                "CF-IPCountry": "NL",
                "Referer": "https://news.ycombinator.com",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"

    summary = analytics_db.get_analytics_summary(temp_analytics_db)
    assert summary["kpis"]["total_events"] >= 1
    countries = [g["country"] for g in summary["geo_distribution"]]
    assert "NL" in countries


def test_http_telemetry_payload_clamping(analytics_test_server):
    """Verify requests over 1024 bytes ceiling are rejected with HTTP 413."""
    with httpx.Client() as client:
        huge_payload = {
            "event_type": "page_view",
            "metadata": {"blob": "X" * 2000},
        }
        res = client.post(f"{analytics_test_server}/api/telemetry", json=huge_payload)
        assert res.status_code == 413
        assert "exceeds 1024 bytes" in res.json().get("error", "")


def test_http_telemetry_invalid_event_type(analytics_test_server):
    """Verify invalid event types return HTTP 400."""
    with httpx.Client() as client:
        res = client.post(f"{analytics_test_server}/api/telemetry", json={"event_type": "hack_attempt"})
        assert res.status_code == 400
        assert "Invalid event type" in res.json().get("error", "")


def test_http_admin_analytics_summary_auth_gate(analytics_test_server, temp_analytics_db):
    """Verify /api/admin/analytics-summary returns 401 without auth and 200 with valid Bearer token."""
    with httpx.Client() as client:
        # 1. Unauthenticated request
        unauth_res = client.get(f"{analytics_test_server}/api/admin/analytics-summary")
        assert unauth_res.status_code == 401

        # 2. Authenticated request with valid session token
        auth_res = client.get(
            f"{analytics_test_server}/api/admin/analytics-summary",
            headers={"Authorization": f"Bearer {serve.ADMIN_SESSION_TOKEN}"},
        )
        assert auth_res.status_code == 200
        data = auth_res.json()
        assert "kpis" in data
        assert "conversion_funnel" in data
        assert "geo_distribution" in data
        assert "top_talks" in data
        assert "top_searches" in data
        assert "hourly_activity" in data
        assert "cloudflare" in data


def test_cloudflare_analytics_unconfigured(monkeypatch):
    """Verify graceful fallback when Cloudflare credentials are not configured."""
    from cloudflare_analytics import fetch_cloudflare_edge_analytics

    monkeypatch.delenv("CLOUDFLARE_ANALYTICS_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDFLARE_ZONE_ID", raising=False)
    import cloudflare_analytics

    cloudflare_analytics._CF_CACHE["data"] = None

    res = fetch_cloudflare_edge_analytics()
    assert res["available"] is False
    assert "not configured" in res["reason"]


def test_reset_analytics_events(temp_analytics_db):
    """Verify reset_analytics_events purges all rows and resets sqlite_sequence."""
    # 1. Insert initial events
    eid1 = analytics_db.record_event("sess1", "page_view", "US", db_path=temp_analytics_db)
    eid2 = analytics_db.record_event("sess2", "search", "DE", metadata={"query": "agent"}, db_path=temp_analytics_db)
    assert eid1 > 0
    assert eid2 > 0

    summary_before = analytics_db.get_analytics_summary(temp_analytics_db)
    assert summary_before["kpis"]["total_events"] >= 2

    # 2. Reset events
    deleted = analytics_db.reset_analytics_events(temp_analytics_db)
    assert deleted >= 2

    # 3. Verify zeroed state
    summary_after = analytics_db.get_analytics_summary(temp_analytics_db)
    assert summary_after["kpis"]["total_events"] == 0
    assert summary_after["kpis"]["unique_visitors_all"] == 0

    # 4. Verify sqlite_sequence reset (next insert starts at id=1)
    new_eid = analytics_db.record_event("sess3", "page_view", "NL", db_path=temp_analytics_db)
    assert new_eid == 1


def test_get_real_client_ip_precedence():
    """Verify CF-Connecting-IP > X-Forwarded-For > client_address precedence."""
    # CF-Connecting-IP takes highest priority
    headers_cf = {
        "CF-Connecting-IP": "203.0.113.195",
        "X-Forwarded-For": "198.51.100.1, 10.0.0.1",
    }
    assert serve.get_real_client_ip(headers_cf, ("127.0.0.1", 54321)) == "203.0.113.195"

    # X-Forwarded-For takes second priority (first IP in CSV)
    headers_xff = {
        "X-Forwarded-For": "198.51.100.1, 10.0.0.1",
    }
    assert serve.get_real_client_ip(headers_xff, ("127.0.0.1", 54321)) == "198.51.100.1"

    # Fallback to client_address tuple
    headers_empty = {}
    assert serve.get_real_client_ip(headers_empty, ("192.168.1.10", 8088)) == "192.168.1.10"

    # Fallback to string
    assert serve.get_real_client_ip(headers_empty, "192.168.1.20") == "192.168.1.20"


def test_http_telemetry_ignored_ip_filter(analytics_test_server, temp_analytics_db, monkeypatch):
    """Verify requests matching ANALYTICS_IGNORE_IPS are suppressed with 200 ignored."""
    monkeypatch.setenv("ANALYTICS_IGNORE_IPS", "203.0.113.50, 198.51.100.22")

    with httpx.Client() as client:
        res = client.post(
            f"{analytics_test_server}/api/telemetry",
            json={"event_type": "page_view"},
            headers={"CF-Connecting-IP": "203.0.113.50"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ignored"
        assert data.get("reason") == "internal_traffic"

    summary = analytics_db.get_analytics_summary(temp_analytics_db)
    assert summary["kpis"]["total_events"] == 0


def test_http_telemetry_internal_headers_filter(analytics_test_server, temp_analytics_db):
    """Verify X-Internal-Test and X-Internal-Agent headers suppress telemetry."""
    with httpx.Client() as client:
        # X-Internal-Test: 1
        res1 = client.post(
            f"{analytics_test_server}/api/telemetry",
            json={"event_type": "page_view"},
            headers={"X-Internal-Test": "1"},
        )
        assert res1.status_code == 200
        assert res1.json() == {"status": "ignored", "reason": "internal_traffic"}

        # X-Internal-Agent: true
        res2 = client.post(
            f"{analytics_test_server}/api/telemetry",
            json={"event_type": "search", "metadata": {"query": "test"}},
            headers={"X-Internal-Agent": "true"},
        )
        assert res2.status_code == 200
        assert res2.json() == {"status": "ignored", "reason": "internal_traffic"}

    summary = analytics_db.get_analytics_summary(temp_analytics_db)
    assert summary["kpis"]["total_events"] == 0


def test_http_telemetry_bot_user_agent_filter(analytics_test_server, temp_analytics_db):
    """Verify automated testing and bot user agents are excluded from analytics."""
    bot_agents = [
        "Mozilla/5.0 (compatible; Googlebot/2.1)",
        "pytest-agent/8.0",
        "playwright/1.40 (headless)",
        "openclaw/2.0-core",
        "curl/7.88.1",
    ]

    with httpx.Client() as client:
        for ua in bot_agents:
            res = client.post(
                f"{analytics_test_server}/api/telemetry",
                json={"event_type": "page_view"},
                headers={"User-Agent": ua},
            )
            assert res.status_code == 200
            assert res.json() == {"status": "ignored", "reason": "internal_traffic"}

    summary = analytics_db.get_analytics_summary(temp_analytics_db)
    assert summary["kpis"]["total_events"] == 0


def test_http_admin_analytics_reset_endpoint(analytics_test_server, temp_analytics_db):
    """Verify POST /api/admin/analytics-reset requires admin auth and clears events table."""
    with httpx.Client() as client:
        # 1. Populate some events
        analytics_db.record_event("s1", "page_view", "US", db_path=temp_analytics_db)
        analytics_db.record_event("s2", "search", "NL", db_path=temp_analytics_db)
        assert analytics_db.get_analytics_summary(temp_analytics_db)["kpis"]["total_events"] == 2

        # 2. Unauthenticated request must return 401
        unauth_res = client.post(f"{analytics_test_server}/api/admin/analytics-reset")
        assert unauth_res.status_code == 401

        # 3. Invalid token must return 401
        invalid_res = client.post(
            f"{analytics_test_server}/api/admin/analytics-reset",
            headers={"Authorization": "Bearer bad-token"},
        )
        assert invalid_res.status_code == 401

        # 4. Valid admin token must purge records and return count
        auth_res = client.post(
            f"{analytics_test_server}/api/admin/analytics-reset",
            headers={"Authorization": f"Bearer {serve.ADMIN_SESSION_TOKEN}"},
        )
        assert auth_res.status_code == 200
        data = auth_res.json()
        assert data.get("status") == "ok"
        assert data.get("deleted_rows") == 2

        # 5. Verify database is now empty
        assert analytics_db.get_analytics_summary(temp_analytics_db)["kpis"]["total_events"] == 0

