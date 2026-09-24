"""Tests for Sprint 15: CRM Inbox Polish, Category Triage, and Activity Ordering."""

import json
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from http.server import HTTPServer

import crm_db
import pytest
import serve


@pytest.fixture
def crm_test_server(tmp_path, monkeypatch):
    """Starts an isolated HTTP server with dedicated temp CRM database."""
    test_crm = str(tmp_path / "test_serve_crm.sqlite")
    monkeypatch.setattr(crm_db, "DB_PATH", test_crm)
    crm_db.init_crm_db()
    serve.ADMIN_SESSION_TOKEN = "valid_test_admin_token"

    server = HTTPServer(("127.0.0.1", 0), serve.HubHTTPRequestHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}", test_crm

    server.shutdown()
    server.server_close()


def test_crm_schema_indices_created(temp_crm_db):
    """Ensure performance indices on thread_messages are properly created."""
    conn = sqlite3.connect(temp_crm_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'thread_messages'")
    indices = {row[0] for row in cur.fetchall()}
    conn.close()

    assert "idx_thread_inq_created" in indices
    assert "idx_thread_inq_id_desc" in indices


def test_crm_inquiries_enrichment_and_categories(temp_crm_db):
    """Verify computed category, last message join, and unread flag logic."""
    # 1. Presenter inquiry (submission_review)
    inq_pres = crm_db.create_inquiry(
        inquiry_type="submission_review",
        name="Speaker Alice",
        email="alice@speaker.com",
        session_id="2RB8t",
        title="Speaker deck dispute",
        initial_message="Here are my updated slides."
    )

    # 2. Collaboration inquiry (partnership)
    inq_collab = crm_db.create_inquiry(
        inquiry_type="partnership",
        name="Partner Bob",
        email="bob@partner.org",
        title="Sponsorship inquiry",
        initial_message="We want to sponsor AGNTCon."
    )

    # 3. Community Feedback inquiry (feedback)
    inq_fb = crm_db.create_inquiry(
        inquiry_type="feedback",
        name="Visitor Charlie",
        email="charlie@gmail.com",
        title="Great event",
        initial_message="When will recordings be available?"
    )

    # 4. General inquiry (other)
    inq_gen = crm_db.create_inquiry(
        inquiry_type="general",
        name="Visitor Dave",
        email="dave@gmail.com",
        title="General Question",
        initial_message="Where is RAI Amsterdam located?"
    )

    # Fetch all
    items = crm_db.get_inquiries_list()
    assert len(items) == 4

    item_map = {i["id"]: i for i in items}
    pres_item = item_map[inq_pres["id"]]
    collab_item = item_map[inq_collab["id"]]
    fb_item = item_map[inq_fb["id"]]
    gen_item = item_map[inq_gen["id"]]

    # Check categories
    assert pres_item["category"] == "presenter"
    assert collab_item["category"] == "collaboration"
    assert fb_item["category"] == "feedback"
    assert gen_item["category"] == "general"

    # Check initial unread status (status='new' and last sender was client)
    assert pres_item["is_unread"] is True
    assert pres_item["last_message_sender"] == "client"
    assert pres_item["last_message_body"] == "Here are my updated slides."
    assert pres_item["last_message_at"] is not None

    # Operator replies to Alice with status 'in_progress'
    crm_db.add_message(
        inquiry_id=inq_pres["id"],
        sender_type="operator",
        body="Thanks Alice, reviewing now.",
        is_note=False,
        new_status="in_progress"
    )

    # Re-fetch inquiries
    items_after = crm_db.get_inquiries_list()
    pres_after = {i["id"]: i for i in items_after}[inq_pres["id"]]

    # Since status is 'in_progress' and last message was from operator, is_unread should now be False!
    assert pres_after["status"] == "in_progress"
    assert pres_after["last_message_sender"] == "operator"
    assert pres_after["last_message_body"] == "Thanks Alice, reviewing now."
    assert pres_after["is_unread"] is False

    # Alice replies back
    crm_db.add_message(
        inquiry_id=inq_pres["id"],
        sender_type="client",
        body="Any updates on this?",
        is_note=False
    )
    pres_re_reply = {i["id"]: i for i in crm_db.get_inquiries_list()}[inq_pres["id"]]
    assert pres_re_reply["last_message_sender"] == "client"
    assert pres_re_reply["last_message_body"] == "Any updates on this?"
    assert pres_re_reply["is_unread"] is True


def test_crm_internal_notes_ignored_in_last_message(temp_crm_db):
    """Internal notes (is_internal_note=1) must not overwrite last_message_body or sender."""
    inq = crm_db.create_inquiry(
        inquiry_type="general",
        name="Dana",
        email="dana@test.com",
        initial_message="Public client message."
    )
    ticket_id = inq["id"]

    # Add internal note
    crm_db.add_message(
        inquiry_id=ticket_id,
        sender_type="operator",
        body="SECRET INTERNAL NOTE: do not expose.",
        is_note=True
    )

    items = crm_db.get_inquiries_list()
    item = {i["id"]: i for i in items}[ticket_id]
    assert item["last_message_body"] == "Public client message."
    assert item["last_message_sender"] == "client"
    assert "SECRET INTERNAL NOTE" not in item["last_message_body"]


def test_crm_category_filter(temp_crm_db):
    """Test filtering by category parameter in get_inquiries_list."""
    crm_db.create_inquiry("speaker_dispute", "Speaker", "s@test.com")
    crm_db.create_inquiry("enterprise_pilot", "Enterprise", "e@test.com")
    crm_db.create_inquiry("general", "General", "g@test.com")

    pres_list = crm_db.get_inquiries_list(category_filter="presenter")
    collab_list = crm_db.get_inquiries_list(category_filter="collaboration")
    gen_list = crm_db.get_inquiries_list(category_filter="general")

    assert len(pres_list) == 1
    assert pres_list[0]["category"] == "presenter"

    assert len(collab_list) == 1
    assert collab_list[0]["category"] == "collaboration"

    assert len(gen_list) == 1
    assert gen_list[0]["category"] == "general"


def test_crm_sorting_by_activity(temp_crm_db):
    """Inquiries should be sorted by COALESCE(last_message_at, updated_at) DESC."""
    inq1 = crm_db.create_inquiry("general", "User 1", "u1@test.com", initial_message="First msg")
    time.sleep(1.05)
    inq2 = crm_db.create_inquiry("general", "User 2", "u2@test.com", initial_message="Second msg")

    items = crm_db.get_inquiries_list()
    assert items[0]["id"] == inq2["id"]
    assert items[1]["id"] == inq1["id"]

    # Now reply to inq1, making it the most recently active
    time.sleep(1.05)
    crm_db.add_message(inq1["id"], "operator", "Latest reply to first user")

    items_updated = crm_db.get_inquiries_list()
    assert items_updated[0]["id"] == inq1["id"]
    assert items_updated[1]["id"] == inq2["id"]


def test_api_admin_inquiries_category_filtering(crm_test_server):
    """Test GET /api/admin/inquiries?category=... endpoint."""
    base_url, _ = crm_test_server

    crm_db.create_inquiry("submission_review", "Speaker Bob", "bob@speaker.com")
    crm_db.create_inquiry("partnership", "Partner Eve", "eve@partner.com")
    crm_db.create_inquiry("general", "Attendee Guy", "guy@general.com")

    headers = {"Authorization": "Bearer valid_test_admin_token"}

    # All
    req_all = urllib.request.Request(f"{base_url}/api/admin/inquiries", headers=headers)
    with urllib.request.urlopen(req_all) as resp:
        assert resp.status == 200
        items_all = json.loads(resp.read().decode())
        assert len(items_all) == 3

    # Presenter
    req_pres = urllib.request.Request(f"{base_url}/api/admin/inquiries?category=presenter", headers=headers)
    with urllib.request.urlopen(req_pres) as resp:
        assert resp.status == 200
        items_pres = json.loads(resp.read().decode())
        assert len(items_pres) == 1
        assert items_pres[0]["category"] == "presenter"
        assert items_pres[0]["name"] == "Speaker Bob"

    # Collaboration
    req_collab = urllib.request.Request(f"{base_url}/api/admin/inquiries?category=collaboration", headers=headers)
    with urllib.request.urlopen(req_collab) as resp:
        assert resp.status == 200
        items_collab = json.loads(resp.read().decode())
        assert len(items_collab) == 1
        assert items_collab[0]["category"] == "collaboration"
        assert items_collab[0]["name"] == "Partner Eve"
