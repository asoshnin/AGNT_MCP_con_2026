"""Tests for the Community Feedback Endpoint (POST /api/community-feedback)."""

import json
import sqlite3
import threading
import time
from http.server import HTTPServer
from pathlib import Path

import pytest
import httpx

import crm_db
from serve import HubHTTPRequestHandler


@pytest.fixture(scope="module")
def feedback_test_server(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("feedback_env")
    data_dir = temp_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    crm_db_path = str(data_dir / "crm.sqlite")
    # Monkeypatch CRM db path in crm_db module
    orig_path = crm_db.DB_PATH
    crm_db.DB_PATH = crm_db_path
    crm_db.init_crm_db()

    # Start ephemeral HTTP server on random free port
    server = HTTPServer(("127.0.0.1", 0), HubHTTPRequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    yield base_url, crm_db_path

    server.shutdown()
    crm_db.DB_PATH = orig_path


def test_submit_valid_feedback(feedback_test_server):
    base_url, db_path = feedback_test_server
    payload = {
        "name": "Jane Developer",
        "email": "jane@example.com",
        "category": "MCP Feature Request",
        "message": "It would be great to have an MCP tool that returns related sessions by cosine similarity!",
        "session_id": "2RBAU"
    }

    res = httpx.post(f"{base_url}/api/community-feedback", json=payload, timeout=5.0)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "ticket_id" in data
    assert "sent directly to the project maintainer" in data["message"]

    # Verify stored in CRM DB
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT type, name, email, session_id, title FROM inquiries WHERE id = ?", (data["ticket_id"],)).fetchone()
    msg_row = conn.execute("SELECT body FROM thread_messages WHERE inquiry_id = ?", (data["ticket_id"],)).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "feedback"
    assert row[1] == "Jane Developer"
    assert row[2] == "jane@example.com"
    assert row[3] == "2RBAU"
    assert "Feedback: MCP Feature Request" in row[4]
    assert msg_row is not None
    assert "cosine similarity" in msg_row[0]


def test_submit_anonymous_feedback(feedback_test_server):
    base_url, db_path = feedback_test_server
    payload = {
        "name": "",
        "email": "",
        "category": "General Feedback",
        "message": "Loved the sub-second search speed. Very smooth UI."
    }

    res = httpx.post(f"{base_url}/api/community-feedback", json=payload, timeout=5.0)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"

    # Verify stored with default name
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT name FROM inquiries WHERE id = ?", (data["ticket_id"],)).fetchone()
    msg_row = conn.execute("SELECT body FROM thread_messages WHERE inquiry_id = ?", (data["ticket_id"],)).fetchone()
    conn.close()
    assert row[0] == "Anonymous Attendee"
    assert msg_row is not None
    assert "sub-second search speed" in msg_row[0]


def test_submit_missing_message_fails(feedback_test_server):
    base_url, _ = feedback_test_server
    payload = {
        "name": "Alex",
        "email": "alex@example.com",
        "category": "Bug Report",
        "message": "   "
    }

    res = httpx.post(f"{base_url}/api/community-feedback", json=payload, timeout=5.0)
    assert res.status_code == 400
    assert "required" in res.json()["error"].lower()


def test_submit_honeypot_spam_dropped(feedback_test_server):
    base_url, db_path = feedback_test_server
    payload = {
        "website_hp": "http://spam-bot-trap.com",
        "name": "Spam Bot",
        "email": "bot@spam.com",
        "category": "General Feedback",
        "message": "Buy cheap watches"
    }

    count_before = 0
    conn = sqlite3.connect(db_path)
    count_before = conn.execute("SELECT count(*) FROM inquiries").fetchone()[0]
    conn.close()

    res = httpx.post(f"{base_url}/api/community-feedback", json=payload, timeout=5.0)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # Verify NO new ticket created
    conn = sqlite3.connect(db_path)
    count_after = conn.execute("SELECT count(*) FROM inquiries").fetchone()[0]
    conn.close()
    assert count_after == count_before
