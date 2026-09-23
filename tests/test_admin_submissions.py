"""Tests for admin submissions management endpoints:
GET /api/admin/submissions
POST /api/admin/submissions/{id}/approve
POST /api/admin/submissions/{id}/reject
"""

import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

import pytest
import serve
from submissions_db import SubmissionsDB


@pytest.fixture
def test_admin_server(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_admin_submissions.sqlite")
    monkeypatch.setenv("SUBMISSIONS_DB_PATH", test_db)
    serve.ADMIN_SESSION_TOKEN = "valid_test_admin_token"

    server = HTTPServer(("127.0.0.1", 0), serve.HubHTTPRequestHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}", test_db

    server.shutdown()
    server.server_close()


def test_admin_submissions_unauthorized(test_admin_server):
    base_url, _ = test_admin_server
    req = urllib.request.Request(f"{base_url}/api/admin/submissions")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 401


def test_admin_submissions_list_and_actions(test_admin_server, tmp_path):
    base_url, db_path = test_admin_server
    db = SubmissionsDB(db_path=db_path)

    # Insert test pending submissions
    sub1_data = {
        "id": "sub_2RB8M_111111",
        "session_id": "2RB8M",
        "submitter_name": "Dave Speaker",
        "submitter_email": "dave@example.com",
        "submitter_role": "speaker",
        "submission_type": "url",
        "source_url": "https://slides.com/dave",
        "status": "pending",
        "draft_summary": "Summary of agent architecture",
    }
    sub2_data = {
        "id": "sub_2RB8M_222222",
        "session_id": "2RB8M",
        "submitter_name": "Eve Spammer",
        "submitter_email": "eve@spam.com",
        "submitter_role": "attendee",
        "submission_type": "url",
        "source_url": "https://spam.com/slides",
        "status": "pending",
    }
    db.insert_submission(sub1_data)
    db.insert_submission(sub2_data)

    headers = {"Authorization": "Bearer valid_test_admin_token"}

    # 1. GET /api/admin/submissions
    req = urllib.request.Request(f"{base_url}/api/admin/submissions", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        items = json.loads(resp.read().decode())
        assert len(items) == 2
        assert items[0]["id"] in ("sub_2RB8M_111111", "sub_2RB8M_222222")

    # 2. POST /api/admin/submissions/{id}/approve
    req_approve = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_2RB8M_111111/approve",
        data=b"{}",
        headers={"Authorization": "Bearer valid_test_admin_token", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req_approve) as resp:
        assert resp.status == 200
        approve_res = json.loads(resp.read().decode())
        assert approve_res["status"] == "approved"
        assert approve_res["session_id"] == "2RB8M"

    sub1_item = db.get_submission("sub_2RB8M_111111")
    assert sub1_item["status"] == "approved"

    # 3. POST /api/admin/submissions/{id}/reject
    req_reject = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_2RB8M_222222/reject",
        data=json.dumps({"reason": "Unverified spam link"}).encode(),
        headers={"Authorization": "Bearer valid_test_admin_token", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req_reject) as resp:
        assert resp.status == 200
        reject_res = json.loads(resp.read().decode())
        assert reject_res["status"] == "rejected"
        assert reject_res["reason"] == "Unverified spam link"

    sub2_item = db.get_submission("sub_2RB8M_222222")
    assert sub2_item["status"] == "rejected"
    assert sub2_item["rejection_reason"] == "Unverified spam link"
