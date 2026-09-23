"""Tests for upload endpoint /api/contribute/upload and /api/contribute/session-info."""

import io
import json
import threading
from http.server import HTTPServer

import pytest
import serve
from submissions_db import SubmissionsDB


@pytest.fixture
def test_server(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_submissions.sqlite")
    monkeypatch.setattr(serve, "HUB_DIR", str(serve.HUB_DIR))
    monkeypatch.setenv("SUBMISSIONS_DB_PATH", test_db)
    serve.CONTRIBUTE_RATE_LIMIT.clear()

    # Start a test HTTP server on an ephemeral port
    server = HTTPServer(("127.0.0.1", 0), serve.HubHTTPRequestHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}", test_db

    server.shutdown()
    server.server_close()


def build_multipart(fields: dict, file_info: tuple[str, bytes] | None = None) -> tuple[bytes, str]:
    boundary = "----WebKitFormBoundaryXtest123"
    body = io.BytesIO()
    for k, v in fields.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        body.write(f"{v}\r\n".encode())
    if file_info:
        filename, data = file_info
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
        body.write(b"Content-Type: application/pdf\r\n\r\n")
        body.write(data)
        body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())
    content_type = f"multipart/form-data; boundary={boundary}"
    return body.getvalue(), content_type


def test_contribute_session_info(test_server):
    import urllib.request
    base_url, _ = test_server

    # Valid session
    req = urllib.request.Request(f"{base_url}/api/contribute/session-info?session_id=2RB8M")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["id"] == "2RB8M"
        assert "Orchestra" in data["title"]

    # Invalid session regex
    try:
        urllib.request.urlopen(f"{base_url}/api/contribute/session-info?session_id=bad_id")
    except urllib.error.HTTPError as e:
        assert e.code == 400


def test_contribute_upload_url_submission(test_server):
    import urllib.request
    base_url, db_path = test_server

    fields = {
        "session_id": "2RB8M",
        "submitter_name": "Bob Presenter",
        "submitter_email": "bob@acme.com",
        "submitter_role": "speaker",
        "presentation_url": "https://docs.google.com/presentation/d/12345/edit",
        "license_accepted": "true",
    }
    payload, content_type = build_multipart(fields)

    req = urllib.request.Request(
        f"{base_url}/api/contribute/upload",
        data=payload,
        headers={"Content-Type": content_type},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode())
        assert res["status"] == "received"
        sub_id = res["submission_id"]

    db = SubmissionsDB(db_path=db_path)
    sub = db.get_submission(sub_id)
    assert sub is not None
    assert sub["submitter_name"] == "Bob Presenter"
    assert sub["submission_type"] == "url"
    assert sub["source_url"] == "https://docs.google.com/presentation/d/12345/edit"
    assert sub["status"] == "pending"


def test_contribute_upload_pdf_submission(test_server):
    import urllib.request
    base_url, db_path = test_server

    import tempfile

    from test_extract_worker import create_minimal_pdf
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_pdf:
        create_minimal_pdf(tmp_pdf.name, "Clean slide content for testing.")
        with open(tmp_pdf.name, "rb") as f:
            pdf_bytes = f.read()

    fields = {
        "session_id": "2RB8M",
        "submitter_name": "Carol Author",
        "submitter_email": "carol@example.org",
        "submitter_role": "coauthor",
        "license_accepted": "true",
    }
    payload, content_type = build_multipart(fields, file_info=("slides.pdf", pdf_bytes))

    req = urllib.request.Request(
        f"{base_url}/api/contribute/upload",
        data=payload,
        headers={"Content-Type": content_type},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode())
        assert res["status"] == "received"
        sub_id = res["submission_id"]

    db = SubmissionsDB(db_path=db_path)
    sub = db.get_submission(sub_id)
    assert sub is not None
    assert sub["submission_type"] == "pdf"
    assert sub["page_count"] >= 1
    assert sub["injection_risk_score"] == "clean"
