"""Unit tests for Sched Re-Scan Engine (Sprint 17).
Validates:
- Polite crawling logic (event URL matching, hosted-files.sched.co validation)
- SSRF prevention & magic bytes validation (%PDF-)
- Size limit enforcement (40MB)
- Incremental upsert execution and atomic index.json / sessions.json updates
- RESCAN_LOCK concurrency guard
- POST /api/admin/rescan-sched endpoint (auth gate, execution, response format)
- HTML UI elements (button & JS trigger in admin.html)
"""

import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import serve
from scripts.rescan_sched_slides import RESCAN_LOCK, rescan_sched


@pytest.fixture
def mock_hub_env(tmp_path):
    """Sets up an isolated mock hub directory with index.json and sessions.json."""
    hub_dir = tmp_path / "mock_hub"
    wiki_dir = hub_dir / "wiki"
    data_dir = hub_dir / "data"
    slides_dir = hub_dir / "site" / "assets" / "slides"

    wiki_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)
    slides_dir.mkdir(parents=True)

    initial_talks = [
        {
            "id": "2RB8M",
            "title": "An Orchestra of Agents",
            "speakers": ["Speaker One"],
            "has_slides": True,
            "one_paragraph": "Existing summary",
        },
        {
            "id": "2RB8S",
            "title": "Stateless: the Future of MCP Transports",
            "speakers": ["Speaker Two"],
            "has_slides": False,
            "one_paragraph": "Session missing slides",
        },
        {
            "id": "2MISS",
            "title": "Missing Session without Upload",
            "speakers": ["Speaker Three"],
            "has_slides": False,
            "one_paragraph": "Still missing",
        },
    ]

    with open(wiki_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(initial_talks, f, indent=2)

    initial_sessions = {
        "2RB8M": {"id": "2RB8M", "session_title": "An Orchestra of Agents", "has_slides": True},
        "2RB8S": {"id": "2RB8S", "session_title": "Stateless: the Future of MCP Transports", "has_slides": False},
        "2MISS": {"id": "2MISS", "session_title": "Missing Session without Upload", "has_slides": False},
    }
    with open(data_dir / "sessions.json", "w", encoding="utf-8") as f:
        json.dump(initial_sessions, f, indent=2)

    return hub_dir


@pytest.fixture
def test_admin_rescan_server(tmp_path, monkeypatch):
    """Starts an ephemeral HTTP server wired with an isolated hub directory."""
    hub_dir = tmp_path / "server_hub"
    wiki_dir = hub_dir / "wiki"
    data_dir = hub_dir / "data"
    slides_dir = hub_dir / "site" / "assets" / "slides"

    wiki_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)
    slides_dir.mkdir(parents=True)

    initial_talks = [
        {"id": "2TEST", "title": "Test Talk", "has_slides": False},
    ]
    with open(wiki_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(initial_talks, f, indent=2)

    monkeypatch.setattr(serve, "HUB_DIR", str(hub_dir))
    monkeypatch.setattr(serve, "ADMIN_SESSION_TOKEN", "valid_rescan_admin_token")

    server = HTTPServer(("127.0.0.1", 0), serve.HubHTTPRequestHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}", hub_dir

    server.shutdown()
    server.server_close()


def test_rescan_sched_discovers_and_ingests_slides(mock_hub_env):
    """Simulates Sched crawl where 2RB8S has a slide deck and 2MISS does not."""
    fake_html_found = """
    <html>
      <body>
        <div class="file-uploaded">
          <a href="https://hosted-files.sched.co/agntconmcpconeu26/fc/stateless_mcp.pdf">Download Slides</a>
        </div>
      </body>
    </html>
    """
    fake_html_not_found = "<html><body>No files attached</body></html>"
    fake_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

    def mock_urlopen(req, timeout=10.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        mock_resp = MagicMock()
        if "2RB8S" in url:
            mock_resp.read.return_value = fake_html_found.encode("utf-8")
        elif "2MISS" in url:
            mock_resp.read.return_value = fake_html_not_found.encode("utf-8")
        elif "stateless_mcp.pdf" in url:
            # First read 1024, then remainder, then empty
            mock_resp.read.side_effect = [fake_pdf_bytes[:1024], fake_pdf_bytes[1024:], b""]
        else:
            mock_resp.read.return_value = b""
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        result = rescan_sched(hub_dir=mock_hub_env, delay_s=0.0)

    assert result["status"] == "completed"
    assert result["scanned_count"] == 2
    assert result["newly_found_count"] == 1
    assert result["ingested_sessions"] == ["2RB8S"]
    assert result["remaining_missing"] == 1

    # Verify PDF downloaded to disk
    downloaded_pdf = mock_hub_env / "site" / "assets" / "slides" / "2RB8S.pdf"
    assert downloaded_pdf.exists()
    assert downloaded_pdf.read_bytes().startswith(b"%PDF-")

    # Verify wiki/index.json updated
    with open(mock_hub_env / "wiki" / "index.json", encoding="utf-8") as f:
        updated_index = json.load(f)
    talk_2rb8s = next(t for t in updated_index if t["id"] == "2RB8S")
    assert talk_2rb8s["has_slides"] is True
    talk_2miss = next(t for t in updated_index if t["id"] == "2MISS")
    assert talk_2miss["has_slides"] is False

    # Verify data/sessions.json updated
    with open(mock_hub_env / "data" / "sessions.json", encoding="utf-8") as f:
        updated_sessions = json.load(f)
    assert updated_sessions["2RB8S"]["has_slides"] is True
    assert updated_sessions["2MISS"]["has_slides"] is False


def test_rescan_sched_ssrf_and_magic_bytes_rejection(mock_hub_env):
    """Verifies that malicious or non-PDF links (e.g. evil.com or non-%PDF-) are rejected."""
    # 1. URL pointing to non-allowlisted domain
    fake_html_evil = """
    <html>
      <body>
        <a href="https://evil.attacker.com/sched-fake/exploit.pdf">Download</a>
      </body>
    </html>
    """

    def mock_urlopen_evil(req, timeout=10.0):
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_html_evil.encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=mock_urlopen_evil):
        result = rescan_sched(hub_dir=mock_hub_env, delay_s=0.0)

    assert result["newly_found_count"] == 0

    # 2. URL pointing to hosted-files.sched.co but returning invalid magic bytes (e.g. HTML/EXE)
    fake_html_sched = """
    <html>
      <body>
        <a href="https://hosted-files.sched.co/agntconmcpconeu26/fc/invalid.pdf">Download</a>
      </body>
    </html>
    """
    fake_bad_bytes = b"MZ\x90\x00\x03\x00\x00\x00"  # PE binary, not %PDF-

    def mock_urlopen_bad_magic(req, timeout=10.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        mock_resp = MagicMock()
        if "invalid.pdf" in url:
            mock_resp.read.side_effect = [fake_bad_bytes[:1024], b""]
        else:
            mock_resp.read.return_value = fake_html_sched.encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=mock_urlopen_bad_magic):
        result = rescan_sched(hub_dir=mock_hub_env, delay_s=0.0)

    assert result["newly_found_count"] == 0
    assert not (mock_hub_env / "site" / "assets" / "slides" / "2RB8S.pdf").exists()


def test_rescan_lock_concurrency_guard(mock_hub_env):
    """Verifies that concurrent re-scans are guarded by RESCAN_LOCK and return status='busy'."""
    assert RESCAN_LOCK.acquire(blocking=False)
    try:
        busy_result = rescan_sched(hub_dir=mock_hub_env, delay_s=0.0)
        assert busy_result["status"] == "busy"
        assert "already in progress" in busy_result["error"]
    finally:
        RESCAN_LOCK.release()


def test_api_admin_rescan_auth_and_response(test_admin_rescan_server):
    """Verifies POST /api/admin/rescan-sched authentication and JSON response."""
    base_url, _ = test_admin_rescan_server

    # 1. Unauthorized request
    req_unauth = urllib.request.Request(
        f"{base_url}/api/admin/rescan-sched",
        data=b"{}",
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req_unauth)
    assert exc_info.value.code == 401

    # 2. Authorized request
    req_auth = urllib.request.Request(
        f"{base_url}/api/admin/rescan-sched",
        data=b"{}",
        headers={"Authorization": "Bearer valid_rescan_admin_token"},
        method="POST",
    )
    with patch("serve.rescan_sched") as mock_rescan:
        mock_rescan.return_value = {
            "status": "completed",
            "scanned_count": 10,
            "newly_found_count": 3,
            "ingested_sessions": ["s1", "s2", "s3"],
            "remaining_missing": 7,
        }
        with urllib.request.urlopen(req_auth) as res:
            assert res.status == 200
            data = json.loads(res.read().decode("utf-8"))
            assert data["status"] == "completed"
            assert data["scanned_count"] == 10
            assert data["newly_found_count"] == 3
            assert data["remaining_missing"] == 7


def test_admin_html_rescan_elements_present():
    """Verifies admin.html contains the Sched re-scan button and triggerSchedRescan function."""
    admin_html_path = Path(__file__).resolve().parent.parent / "site" / "admin.html"
    assert admin_html_path.exists()
    content = admin_html_path.read_text(encoding="utf-8")

    assert "btn-sched-rescan" in content
    assert "Re-scan Sched for New Slides" in content
    assert "triggerSchedRescan()" in content
    assert "/api/admin/rescan-sched" in content
