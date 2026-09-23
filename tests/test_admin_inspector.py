"""Tests for Sprint 14: Submissions Inspector & LLM Authenticity Gate.
Covers:
- GET /api/admin/submissions/{id}/download (protected, path-contained attachment)
- GET /api/admin/submissions/{id}/preview (protected, inline for iframe)
- Path traversal & containment rejection (HTTP 403 Forbidden)
- Sched metadata enrichment in submissions list & detail
- POST /api/admin/submissions/{id}/verify-relevance (heuristic & LLM gate, caching, ?force=1)
- POST /api/admin/submissions/{id}/reply (CRM bridge & email dispatch)
"""

import json
import os
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

import crm_db
import pytest
import serve
from submissions_db import SubmissionsDB


@pytest.fixture
def inspector_test_server(tmp_path, monkeypatch):
    test_sub_db = str(tmp_path / "test_inspector_submissions.sqlite")
    test_crm_db = str(tmp_path / "test_inspector_crm.sqlite")
    pending_dir = str(tmp_path / "submissions" / "pending")
    canonical_dir = str(tmp_path / "assets" / "slides")
    os.makedirs(pending_dir, exist_ok=True)
    os.makedirs(canonical_dir, exist_ok=True)

    monkeypatch.setenv("SUBMISSIONS_DB_PATH", test_sub_db)
    monkeypatch.setenv("PENDING_SUBMISSIONS_DIR", pending_dir)
    monkeypatch.setenv("CANONICAL_SLIDES_DIR", canonical_dir)
    monkeypatch.setattr(crm_db, "DB_PATH", test_crm_db)

    # Provide mock sessions.json
    sessions_json_path = str(tmp_path / "sessions.json")
    mock_sessions = {
        "2RB8t": {
            "id": "2RB8t",
            "session_title": "MCP Context Engineering in Production",
            "session_speakers": ["Sam Morrow"],
            "session_company": "GitHub",
            "session_abstract": "Deep dive into Model Context Protocol (MCP) servers, context engineering, and agent memory architecture in production systems.",
            "sched_url": "https://agntconmcpconeu26.sched.com/event/2RB8t",
        }
    }
    with open(sessions_json_path, "w", encoding="utf-8") as f:
        json.dump(mock_sessions, f)
    monkeypatch.setenv("SESSIONS_JSON_PATH", sessions_json_path)

    # Prevent external network calls in unit tests
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("KILOCODE_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)

    # Freeze admin token
    test_admin_token = "inspector_secret_token_12345"
    serve.ADMIN_SESSION_TOKEN = test_admin_token
    crm_db.init_crm_db()

    server = HTTPServer(("127.0.0.1", 0), serve.HubHTTPRequestHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield {
        "base_url": f"http://127.0.0.1:{port}",
        "token": test_admin_token,
        "sub_db_path": test_sub_db,
        "crm_db_path": test_crm_db,
        "pending_dir": pending_dir,
        "canonical_dir": canonical_dir,
        "tmp_path": tmp_path,
    }

    server.shutdown()
    server.server_close()


def test_download_endpoint_authorized_and_containment(inspector_test_server):
    info = inspector_test_server
    base_url = info["base_url"]
    token = info["token"]
    db = SubmissionsDB(db_path=info["sub_db_path"])

    # Create dummy PDF in pending dir
    sub_dir = os.path.join(info["pending_dir"], "sub_2RB8t_valid")
    os.makedirs(sub_dir, exist_ok=True)
    pdf_path = os.path.join(sub_dir, "upload.tmp")
    pdf_content = b"%PDF-1.4 Fake PDF Content for AGNTCon"
    with open(pdf_path, "wb") as f:
        f.write(pdf_content)

    sub_data = {
        "id": "sub_2RB8t_valid",
        "session_id": "2RB8t",
        "submitter_name": "Sam Morrow",
        "submitter_email": "sam.morrow@github.com",
        "submitter_role": "speaker",
        "submission_type": "pdf",
        "file_path": pdf_path,
        "status": "pending",
    }
    db.insert_submission(sub_data)

    # 1. Unauthorized request (no token) -> 401
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(f"{base_url}/api/admin/submissions/sub_2RB8t_valid/download")
    assert exc_info.value.code == 401

    # 2. Authorized request via Bearer header -> 200 attachment
    req = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_2RB8t_valid/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type") == "application/pdf"
        assert 'attachment; filename="2RB8t_Sam_Morrow.pdf"' in resp.headers.get("Content-Disposition", "")
        data = resp.read()
        assert data == pdf_content

    # 3. Authorized request via query parameter ?token=*** -> 200 attachment
    req_query = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_2RB8t_valid/download?token={token}"
    )
    with urllib.request.urlopen(req_query) as resp:
        assert resp.status == 200
        assert resp.read() == pdf_content


def test_preview_endpoint_inline_and_xframe(inspector_test_server):
    info = inspector_test_server
    base_url = info["base_url"]
    token = info["token"]
    db = SubmissionsDB(db_path=info["sub_db_path"])

    sub_dir = os.path.join(info["pending_dir"], "sub_2RB8t_prev")
    os.makedirs(sub_dir, exist_ok=True)
    pdf_path = os.path.join(sub_dir, "upload.tmp")
    pdf_content = b"%PDF-1.4 Preview Content"
    with open(pdf_path, "wb") as f:
        f.write(pdf_content)

    sub_data = {
        "id": "sub_2RB8t_prev",
        "session_id": "2RB8t",
        "submitter_name": "Sam Morrow",
        "submitter_email": "sam.morrow@github.com",
        "submitter_role": "speaker",
        "submission_type": "pdf",
        "file_path": pdf_path,
        "status": "pending",
    }
    db.insert_submission(sub_data)

    # Query param token preview (used by <iframe>)
    req = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_2RB8t_prev/preview?token={token}"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type") == "application/pdf"
        assert resp.headers.get("Content-Disposition") == "inline"
        assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert resp.read() == pdf_content


def test_path_traversal_containment_rejection(inspector_test_server):
    info = inspector_test_server
    base_url = info["base_url"]
    token = info["token"]
    db = SubmissionsDB(db_path=info["sub_db_path"])

    # Create file outside pending and canonical dirs
    evil_file = info["tmp_path"] / "outside_secret.txt"
    evil_file.write_bytes(b"SECRET DATA")

    sub_data = {
        "id": "sub_evil_traversal",
        "session_id": "2RB8t",
        "submitter_name": "Attacker",
        "submitter_email": "evil@attacker.com",
        "submitter_role": "attendee",
        "submission_type": "pdf",
        "file_path": str(evil_file),
        "status": "pending",
    }
    db.insert_submission(sub_data)

    # 1. Download must be rejected with HTTP 403 Forbidden
    req = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_evil_traversal/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 403

    # 2. Preview must also be rejected with HTTP 403 Forbidden
    req_prev = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_evil_traversal/preview?token={token}"
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info_prev:
        urllib.request.urlopen(req_prev)
    assert exc_info_prev.value.code == 403


def test_submissions_metadata_enrichment(inspector_test_server):
    info = inspector_test_server
    base_url = info["base_url"]
    token = info["token"]
    db = SubmissionsDB(db_path=info["sub_db_path"])

    db.insert_submission({
        "id": "sub_enriched_1",
        "session_id": "2RB8t",
        "submitter_name": "Sam Morrow",
        "submitter_email": "sam.morrow@github.com",
        "submitter_role": "speaker",
        "submission_type": "url",
        "status": "pending",
    })

    # List endpoint
    req = urllib.request.Request(
        f"{base_url}/api/admin/submissions",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        items = json.loads(resp.read().decode())
        item = next(i for i in items if i["id"] == "sub_enriched_1")
        assert item["session_title"] == "MCP Context Engineering in Production"
        assert "Sam Morrow" in item["session_speakers"]
        assert item["session_company"] == "GitHub"
        assert "Model Context Protocol" in item["session_abstract"]
        assert item["sched_url"] == "https://agntconmcpconeu26.sched.com/event/2RB8t"
        assert item["domain_matched"] is True

    # Single detail endpoint
    req_single = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_enriched_1",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req_single) as resp:
        assert resp.status == 200
        single_item = json.loads(resp.read().decode())
        assert single_item["id"] == "sub_enriched_1"
        assert single_item["session_title"] == "MCP Context Engineering in Production"


def test_verify_relevance_endpoint_and_caching(inspector_test_server):
    info = inspector_test_server
    base_url = info["base_url"]
    token = info["token"]
    db = SubmissionsDB(db_path=info["sub_db_path"])

    # High match submission
    db.insert_submission({
        "id": "sub_match_test",
        "session_id": "2RB8t",
        "submitter_name": "Sam Morrow",
        "submitter_email": "sam.morrow@github.com",
        "submitter_role": "speaker",
        "submission_type": "pdf",
        "draft_summary": "In this presentation we discuss Model Context Protocol (MCP) servers, context engineering patterns, agent memory architectures, and production scaling.",
        "status": "pending",
    })

    # 1. Unauthorized -> 401
    req_unauth = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_match_test/verify-relevance",
        data=b"{}",
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req_unauth)
    assert exc_info.value.code == 401

    # 2. First verify run -> calculates score, verdict MATCH
    req_verify = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_match_test/verify-relevance",
        data=b"{}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req_verify) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["relevance_score"] >= 80
        assert data["authenticity_verdict"] == "MATCH"
        assert "keyword" in data["authenticity_rationale"].lower() or "verified" in data["authenticity_rationale"].lower()
        assert data["cached"] is False

    # Check database persistence
    sub_row = db.get_submission("sub_match_test")
    assert sub_row["relevance_score"] == data["relevance_score"]
    assert sub_row["authenticity_verdict"] == "MATCH"

    # 3. Second run without force=1 -> returns cached result
    with urllib.request.urlopen(req_verify) as resp:
        data_cached = json.loads(resp.read().decode())
        assert data_cached["cached"] is True
        assert data_cached["relevance_score"] == data["relevance_score"]

    # 4. Third run with force=1 -> recomputes (cached is False)
    req_force = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_match_test/verify-relevance?force=1",
        data=b"{}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req_force) as resp:
        data_forced = json.loads(resp.read().decode())
        assert data_forced["cached"] is False
        assert data_forced["relevance_score"] >= 80


def test_verify_relevance_mismatch(inspector_test_server):
    info = inspector_test_server
    base_url = info["base_url"]
    token = info["token"]
    db = SubmissionsDB(db_path=info["sub_db_path"])

    # Unrelated spam submission
    db.insert_submission({
        "id": "sub_mismatch_test",
        "session_id": "2RB8t",
        "submitter_name": "Spam User",
        "submitter_email": "spam@example.com",
        "submitter_role": "attendee",
        "submission_type": "pdf",
        "draft_summary": "Top recipes for Italian pasta and homemade pizza baking techniques in wood fired ovens.",
        "status": "pending",
    })

    req = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_mismatch_test/verify-relevance",
        data=b"{}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["relevance_score"] < 50
        assert data["authenticity_verdict"] == "MISMATCH"


def test_reply_endpoint_creates_crm_and_links(inspector_test_server):
    info = inspector_test_server
    base_url = info["base_url"]
    token = info["token"]
    db = SubmissionsDB(db_path=info["sub_db_path"])

    db.insert_submission({
        "id": "sub_reply_target",
        "session_id": "2RB8t",
        "submitter_name": "Sam Morrow",
        "submitter_email": "sam.morrow@github.com",
        "submitter_role": "speaker",
        "submission_type": "pdf",
        "status": "pending",
    })

    # 1. Unauthorized -> 401
    req_unauth = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_reply_target/reply",
        data=json.dumps({"message": "Hello"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req_unauth)
    assert exc_info.value.code == 401

    # 2. Missing message -> 400
    req_empty = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_reply_target/reply",
        data=json.dumps({"message": "   "}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info_empty:
        urllib.request.urlopen(req_empty)
    assert exc_info_empty.value.code == 400

    # 3. Successful reply
    payload = {
        "message": "Hi Sam, thanks for submitting! Could you check slide 12?",
        "subject": "Regarding your AGNTCon presentation",
    }
    req_ok = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_reply_target/reply",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req_ok) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode())
        assert res["status"] == "sent"
        assert res["inquiry_id"].startswith("TICK-")
        assert res["recipient"] == "sam.morrow@github.com"

        inquiry_id = res["inquiry_id"]

    # Verify CRM SQLite record
    inq_detail = crm_db.get_inquiry_detail(inquiry_id)
    assert inq_detail is not None
    assert inq_detail["email"] == "sam.morrow@github.com"
    assert inq_detail["session_id"] == "2RB8t"
    assert any("Could you check slide 12?" in m["body"] for m in inq_detail["messages"])

    # Verify submissions database linked crm_inquiry_id
    sub_row = db.get_submission("sub_reply_target")
    assert sub_row["crm_inquiry_id"] == inquiry_id


def test_verify_relevance_mocked_llm_cascade(inspector_test_server, monkeypatch):
    from unittest.mock import MagicMock
    info = inspector_test_server
    base_url = info["base_url"]
    token = info["token"]
    db = SubmissionsDB(db_path=info["sub_db_path"])

    db.insert_submission({
        "id": "sub_mock_llm",
        "session_id": "2RB8t",
        "submitter_name": "Sam Morrow",
        "submitter_email": "sam.morrow@github.com",
        "submitter_role": "speaker",
        "submission_type": "pdf",
        "draft_summary": "Extracted slides discussing MCP architecture.",
        "status": "pending",
    })

    # Enable mock key
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock_key_test")

    mock_llm_json = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "relevance_score": 96,
                        "authenticity_verdict": "MATCH",
                        "authenticity_rationale": "High-confidence alignment with MCP production architecture abstract."
                    })
                }
            }
        ]
    }

    # Intercept urllib.request.urlopen for OpenRouter API call
    real_urlopen = urllib.request.urlopen

    def fake_urlopen(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "openrouter.ai" in url:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = json.dumps(mock_llm_json).encode("utf-8")
            mock_resp.__enter__.return_value = mock_resp
            mock_resp.__exit__.return_value = None
            return mock_resp
        return real_urlopen(req, *args, **kwargs)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    req = urllib.request.Request(
        f"{base_url}/api/admin/submissions/sub_mock_llm/verify-relevance",
        data=b"{}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode())
        assert res["relevance_score"] == 96
        assert res["authenticity_verdict"] == "MATCH"
        assert "High-confidence" in res["authenticity_rationale"]

