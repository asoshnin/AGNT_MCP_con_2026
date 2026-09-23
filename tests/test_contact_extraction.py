"""Unit tests for Contact Harvester, Outreach Engine, and Token Isolation Layer (Sprint 18).

All tests use tmp_path fixtures with mocked HTTP responses to enforce test isolation.
"""

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure 02_public_hub is on sys.path
HUB_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HUB_DIR))
sys.path.insert(0, str(HUB_DIR / "scripts"))

import outreach_db
from scripts.extract_contacts import (
    extract_social_links,
    harvest_contacts,
    parse_lf_committee_page,
    parse_sched_speaker_directory,
    parse_sched_speaker_page,
    slugify,
)
from scripts.generate_outreach_campaign import (
    generate_campaign,
    render_missing_slides_template,
    render_organizer_template,
    render_public_launch_post,
    render_slides_available_template,
)
from scripts.generate_speaker_tokens import populate_tokens_in_db
from scripts.rescan_sched_slides import sync_speaker_cohort


def test_slugify_helper():
    assert slugify("Sam Morrow") == "sam_morrow"
    assert slugify("Angie Jones, Ph.D.") == "angie_jones_phd"
    assert slugify("  Dr. Jane-Doe  ") == "dr_jane_doe"
    assert slugify("") == "unknown"


def test_parse_sched_speaker_directory_and_speaker_page():
    dir_html = """
    <html>
      <body>
        <div class="sched-person">
          <a href="/speaker/sam_morrow">Sam Morrow</a>
        </div>
        <div class="sched-person">
          <a href="/speaker/jane_doe">Jane Doe</a>
        </div>
      </body>
    </html>
    """
    entries = parse_sched_speaker_directory(dir_html, "https://agntcon.sched.com")
    assert len(entries) == 2
    assert entries[0]["handle"] == "sam_morrow"
    assert entries[0]["url"] == "https://agntcon.sched.com/speaker/sam_morrow"

    spk_html = """
    <html>
      <head><title>Sam Morrow - Sched</title></head>
      <body>
        <h1 class="sched-person-name">Sam Morrow</h1>
        <div class="sched-person-company">Staff Software Engineer, GitHub</div>
        <div class="sched-person-bio">Sam is a Staff Software Engineer at GitHub leading MCP server development.</div>
        <div class="social-links">
          <a href="https://www.linkedin.com/in/sammorrow">LinkedIn</a>
          <a href="https://twitter.com/sammorrow">Twitter</a>
          <a href="https://twitter.com/intent/tweet">Share</a>
        </div>
        <div class="sched-event">
          <a href="/event/2RB8t/mcp-doesnt-have-a-context-problem">Session Talk</a>
        </div>
      </body>
    </html>
    """
    spk_data = parse_sched_speaker_page(spk_html, "sam_morrow", "https://agntcon.sched.com")
    assert spk_data["name"] == "Sam Morrow"
    assert spk_data["role"] == "Staff Software Engineer"
    assert spk_data["company"] == "GitHub"
    assert "leading MCP server development" in spk_data["bio"]
    assert spk_data["linkedin_url"] == "https://linkedin.com/in/sammorrow"
    assert spk_data["twitter_url"] == "https://twitter.com/sammorrow"
    assert spk_data["session_ids"] == ["2RB8t"]


def test_parse_lf_committee_page():
    lf_html = """
    <html>
      <body>
        <div class="speaker-card">
          <h3>Angie Jones</h3>
          <p class="title">Vice President, Agentic AI Foundation</p>
          <div class="bio">VP of Developer Relations and Agentic AI Foundation Chair.</div>
          <a href="https://linkedin.com/in/angiejones">LinkedIn</a>
          <a href="https://twitter.com/techgirl1908">Twitter</a>
        </div>
        <div class="speaker-card">
          <h3>Paul Carleton</h3>
          <p class="title">Lead Architect, Anthropic</p>
          <a href="https://linkedin.com/in/paulcarleton">LinkedIn</a>
        </div>
      </body>
    </html>
    """
    organizers = parse_lf_committee_page(lf_html)
    assert len(organizers) == 2
    assert organizers[0]["id"] == "org_angie_jones"
    assert organizers[0]["name"] == "Angie Jones"
    assert organizers[0]["role"] == "Vice President"
    assert organizers[0]["company"] == "Agentic AI Foundation"
    assert organizers[0]["cohort"] == "cohort_organizers"
    assert organizers[0]["linkedin_url"] == "https://linkedin.com/in/angiejones"
    assert organizers[0]["twitter_url"] == "https://twitter.com/techgirl1908"


def test_harvest_contacts_reconciliation_and_cohort_assignment(tmp_path):
    # Setup mock wiki/index.json
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    mock_index = [
        {
            "id": "sess_slides",
            "title": "Scaling Multi-Agent Systems",
            "speakers": ["Sam Morrow"],
            "has_slides": True,
        },
        {
            "id": "sess_no_slides",
            "title": "Observability for Autonomous Tools",
            "speakers": ["Jane Doe"],
            "has_slides": False,
        },
    ]
    with open(wiki_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(mock_index, f)

    dir_html = """
    <html>
      <body>
        <a href="/speaker/sam_morrow">Sam Morrow</a>
        <a href="/speaker/jane_doe">Jane Doe</a>
      </body>
    </html>
    """
    spk_map = {
        "sam_morrow": """
        <html>
          <h1>Sam Morrow</h1>
          <div class="sched-person-company">Staff Engineer, GitHub</div>
          <a href="https://linkedin.com/in/sammorrow">LinkedIn</a>
          <a href="/event/sess_slides">Session</a>
        </html>
        """,
        "jane_doe": """
        <html>
          <h1>Jane Doe</h1>
          <div class="sched-person-company">Researcher, AI Lab</div>
          <a href="/event/sess_no_slides">Session</a>
        </html>
        """,
    }

    res = harvest_contacts(
        hub_dir=tmp_path,
        delay_s=0.0,
        custom_directory_html=dir_html,
        custom_speaker_html_map=spk_map,
        skip_network=True,
    )

    assert res["status"] == "success"
    assert res["total_speakers"] == 2
    assert res["cohorts"]["cohort_missing_slides"] == 1
    assert res["cohorts"]["cohort_slides_available"] == 1
    assert res["cohorts"]["cohort_organizers"] >= 1

    contacts_file = tmp_path / "data" / "contacts.json"
    summary_file = tmp_path / "data" / "contacts_summary.json"
    assert contacts_file.exists()
    assert summary_file.exists()

    with open(contacts_file, encoding="utf-8") as f:
        c_data = json.load(f)
    speakers = c_data["speakers"]
    sam = next(s for s in speakers if s["name"] == "Sam Morrow")
    jane = next(s for s in speakers if s["name"] == "Jane Doe")

    assert sam["cohort"] == "cohort_slides_available"
    assert jane["cohort"] == "cohort_missing_slides"

    with open(summary_file, encoding="utf-8") as f:
        s_data = json.load(f)
    assert s_data["total_speakers"] == 2
    assert s_data["cohort_missing_slides_count"] == 1
    assert s_data["cohort_slides_available_count"] == 1


def test_pii_isolation_and_git_safety():
    # Verify .gitignore in 02_public_hub
    gitignore_path = HUB_DIR / ".gitignore"
    assert gitignore_path.exists()
    with open(gitignore_path, encoding="utf-8") as f:
        content = f.read()

    assert "data/contacts.json" in content
    assert "data/outreach_private.sqlite*" in content
    assert "out/" in content
    assert "!/data/contacts_summary.json" in content

    # Test git check-ignore
    proc1 = subprocess.run(
        ["git", "check-ignore", "data/contacts.json"],
        cwd=str(HUB_DIR),
        capture_output=True,
        text=True,
    )
    assert proc1.returncode == 0

    proc2 = subprocess.run(
        ["git", "check-ignore", "data/contacts_summary.json"],
        cwd=str(HUB_DIR),
        capture_output=True,
        text=True,
    )
    # Return code != 0 means NOT ignored (safe for git)
    assert proc2.returncode != 0


def test_outreach_db_and_permissions(tmp_path):
    db_file = tmp_path / "data" / "outreach_private.sqlite"
    conn = outreach_db.init_outreach_db(db_file)

    # Assert chmod 0600 on POSIX
    mode = os.stat(db_file).st_mode
    assert (mode & stat.S_IRUSR) and (mode & stat.S_IWUSR)
    assert not (mode & stat.S_IRGRP)
    assert not (mode & stat.S_IROTH)

    # Test storing and fetching token
    outreach_db.store_token(
        conn=conn,
        session_id="2RB8t",
        speaker_name="Sam Morrow",
        token="tok_12345",
        magic_url="https://agntcon.vwoosh.com/contribute?token=tok_12345",
    )
    tok = outreach_db.get_token(conn, "2RB8t")
    assert tok is not None
    assert tok["speaker_name"] == "Sam Morrow"
    assert tok["token"] == "tok_12345"

    # Test opt-out registry
    assert outreach_db.is_opted_out(conn, "optout@example.com") is False
    outreach_db.add_opt_out(conn, "optout@example.com", reason="User requested erasure")
    assert outreach_db.is_opted_out(conn, "optout@example.com") is True
    assert outreach_db.is_opted_out(conn, "OPTOUT@EXAMPLE.COM") is True  # case insensitive
    assert outreach_db.is_opted_out(conn, "someone_else@example.com") is False

    conn.close()


def test_populate_tokens_in_db(tmp_path):
    db_file = tmp_path / "data" / "outreach_private.sqlite"
    catalog = [
        {"id": "sess_1", "title": "Missing Talk", "speakers": ["Alice Smith"], "has_slides": False},
        {"id": "sess_2", "title": "Present Talk", "speakers": ["Bob Jones"], "has_slides": True},
    ]

    records = populate_tokens_in_db(
        catalog=catalog,
        db_path=db_file,
        secret="test_secret_key",
        valid_days=14,
        base_url="https://agntcon.vwoosh.com",
    )
    assert len(records) == 1
    assert records[0]["session_id"] == "sess_1"
    assert "token=" in records[0]["magic_url"]

    conn = outreach_db.init_outreach_db(db_file)
    saved = outreach_db.get_token(conn, "sess_1")
    assert saved is not None
    assert saved["speaker_name"] == "Alice Smith"
    conn.close()


def test_campaign_generation_and_opt_out_suppression(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    contacts_file = data_dir / "contacts.json"
    db_file = data_dir / "outreach_private.sqlite"
    out_dir = tmp_path / "out" / "campaigns"

    mock_contacts = {
        "organizers": [
            {
                "id": "org_angie",
                "name": "Angie Jones",
                "role": "VP",
                "company": "Agentic AI Foundation",
                "linkedin_url": "https://linkedin.com/in/angiejones",
                "cohort": "cohort_organizers",
            }
        ],
        "speakers": [
            {
                "id": "speaker_sam",
                "name": "Sam Morrow",
                "cohort": "cohort_slides_available",
                "linkedin_url": "https://linkedin.com/in/sammorrow",
                "sessions": [{"session_id": "2RB8t", "title": "MCP Context", "has_slides": True}],
            },
            {
                "id": "speaker_jane",
                "name": "Jane Doe",
                "cohort": "cohort_missing_slides",
                "linkedin_url": "https://linkedin.com/in/janedoe",
                "sessions": [{"session_id": "2RB8m", "title": "Orchestrating Agents", "has_slides": False}],
            },
            {
                "id": "speaker_opted_out",
                "name": "Opted Out User",
                "cohort": "cohort_missing_slides",
                "linkedin_url": "https://linkedin.com/in/optedout",
                "sessions": [{"session_id": "2RB99", "title": "Secret Talk", "has_slides": False}],
            },
        ],
    }
    with open(contacts_file, "w", encoding="utf-8") as f:
        json.dump(mock_contacts, f)

    # Mark one speaker as opted out
    conn = outreach_db.init_outreach_db(db_file)
    outreach_db.add_opt_out(conn, "https://linkedin.com/in/optedout")
    conn.close()

    summary = generate_campaign(
        contacts_path=contacts_file,
        db_path=db_file,
        out_dir=out_dir,
        base_url="https://agntcon-demo.vwoosh.com",
    )

    assert summary["counts"]["cohort_organizers"] == 1
    assert summary["counts"]["cohort_slides_available"] == 1
    assert summary["counts"]["cohort_missing_slides"] == 1
    assert summary["counts"]["suppressed_due_to_opt_out"] == 1

    # Verify generated campaign files
    assert (out_dir / "cohort_organizers.json").exists()
    assert (out_dir / "cohort_missing_slides.json").exists()
    assert (out_dir / "cohort_slides_available.json").exists()
    assert (out_dir / "public_launch_post.md").exists()
    assert (out_dir / "campaign_summary.json").exists()

    # Verify public launch post has anti-suppression mechanics
    with open(out_dir / "public_launch_post.md", encoding="utf-8") as f:
        post_content = f.read()
    assert "V2: The Open-Source AGNTCon Community Knowledge Hub" in post_content
    assert "first comment" in post_content.lower()

    # Verify slide available message has deep link
    with open(out_dir / "cohort_slides_available.json", encoding="utf-8") as f:
        avail_msgs = json.load(f)
    assert len(avail_msgs) == 1
    assert "#session-2RB8t" in avail_msgs[0]["message"]


def test_sync_speaker_cohort_re_scan_hook(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    contacts_file = data_dir / "contacts.json"

    initial_contacts = {
        "organizers": [],
        "speakers": [
            {
                "id": "speaker_alice",
                "name": "Alice Smith",
                "cohort": "cohort_missing_slides",
                "sessions": [
                    {"session_id": "sess_100", "title": "Future of Agents", "has_slides": False, "slide_url": None}
                ],
            }
        ],
        "cohorts_summary": {
            "cohort_organizers": 0,
            "cohort_missing_slides": 1,
            "cohort_slides_available": 0,
        },
    }
    with open(contacts_file, "w", encoding="utf-8") as f:
        json.dump(initial_contacts, f)

    # Trigger slide acquisition sync
    res = sync_speaker_cohort(tmp_path, "sess_100", has_slides=True)
    assert res is True

    with open(contacts_file, encoding="utf-8") as f:
        updated = json.load(f)

    spk = updated["speakers"][0]
    assert spk["cohort"] == "cohort_slides_available"
    assert spk["sessions"][0]["has_slides"] is True
    assert spk["sessions"][0]["slide_url"] == "/assets/slides/sess_100.pdf"
    assert updated["cohorts_summary"]["cohort_slides_available"] == 1
    assert updated["cohorts_summary"]["cohort_missing_slides"] == 0

    # Summary json check
    summary_file = data_dir / "contacts_summary.json"
    assert summary_file.exists()
    with open(summary_file, encoding="utf-8") as f:
        sum_data = json.load(f)
    assert sum_data["cohort_slides_available_count"] == 1
    assert sum_data["cohort_missing_slides_count"] == 0


def test_admin_api_endpoints_mocked(tmp_path, monkeypatch):
    import serve

    monkeypatch.setattr(serve, "HUB_DIR", tmp_path)
    summary_file = tmp_path / "data" / "contacts_summary.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    mock_summary = {
        "updated_at": "2026-09-23T12:00:00Z",
        "total_speakers": 10,
        "total_organizers": 3,
        "cohort_organizers_count": 3,
        "cohort_missing_slides_count": 4,
        "cohort_slides_available_count": 6,
    }
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(mock_summary, f)

    # Mock admin auth check
    monkeypatch.setattr(serve, "check_admin_auth", lambda headers, query_params=None: True)

    # Verify GET /api/admin/contacts-summary handling
    handler = serve.HubHTTPRequestHandler.__new__(serve.HubHTTPRequestHandler)
    handler.path = "/api/admin/contacts-summary"
    handler.headers = {"Authorization": "Bearer admin"}
    handler.client_address = ("127.0.0.1", 12345)

    captured_status = None
    captured_body = b""

    def mock_send_response(code):
        nonlocal captured_status
        captured_status = code

    def mock_send_header(k, v):
        pass

    def mock_end_headers():
        pass

    class MockWFile:
        def write(self, data):
            nonlocal captured_body
            captured_body += data

    handler.send_response = mock_send_response
    handler.send_header = mock_send_header
    handler.end_headers = mock_end_headers
    handler.wfile = MockWFile()

    handler.do_GET()

    assert captured_status == 200
    res_data = json.loads(captured_body.decode("utf-8"))
    assert res_data["total_speakers"] == 10
    assert res_data["cohort_missing_slides_count"] == 4
