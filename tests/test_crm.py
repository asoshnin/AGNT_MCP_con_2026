"""Tests for SQLite CRM database and speaker collaboration workflows."""

import crm_db


def test_crm_inquiry_creation_and_retrieval(temp_crm_db):
    inq = crm_db.create_inquiry(
        inquiry_type="Speaker Correction",
        name="Alice Speaker",
        email="alice@redhat.com",
        org="Red Hat",
        profile="https://github.com/alice",
        session_id="2RBBJ",
        title="Session 2RBBJ Title",
        initial_message="Please update the slides link."
    )

    ticket_id = inq["id"]
    secret_token = inq["secret_token"]
    assert ticket_id.startswith("TICK-")
    assert len(secret_token) == 32

    # Fetch detail
    detail = crm_db.get_inquiry_detail(ticket_id)
    assert detail is not None
    assert detail["name"] == "Alice Speaker"
    assert detail["email"] == "alice@redhat.com"
    assert detail["secret_token"] == secret_token
    assert len(detail["messages"]) == 1
    assert detail["messages"][0]["body"] == "Please update the slides link."
    assert detail["messages"][0]["is_internal_note"] == 0

def test_crm_internal_notes_isolation(temp_crm_db):
    inq = crm_db.create_inquiry(
        inquiry_type="Collaboration",
        name="Bob Partner",
        email="bob@acme.com",
        initial_message="Let us collaborate."
    )
    ticket_id = inq["id"]

    # Add public maintainer reply
    crm_db.add_message(ticket_id, sender_type="admin", body="Thanks Bob, we received this.", is_note=False)

    # Add private internal note
    crm_db.add_message(ticket_id, sender_type="admin", body="INTERNAL ONLY: Verified identity via LinkedIn.", is_note=True)

    detail = crm_db.get_inquiry_detail(ticket_id)
    assert len(detail["messages"]) == 3

    # Client-facing filtration simulation (as implemented in serve.py)
    public_messages = [m for m in detail["messages"] if not m.get("is_internal_note")]
    assert len(public_messages) == 2
    for m in public_messages:
        assert "INTERNAL ONLY" not in m["body"]

def test_crm_status_transitions_and_bulk_operations(temp_crm_db):
    inq1 = crm_db.create_inquiry("Sponsorship", "User 1", "u1@test.com")
    inq2 = crm_db.create_inquiry("Sponsorship", "User 2", "u2@test.com")

    t1, t2 = inq1["id"], inq2["id"]

    # Bulk update status
    affected = crm_db.bulk_update_status([t1, t2], "resolved")
    assert affected == 2

    detail1 = crm_db.get_inquiry_detail(t1)
    detail2 = crm_db.get_inquiry_detail(t2)
    assert detail1["status"] == "resolved"
    assert detail2["status"] == "resolved"

    # Bulk delete
    del_count = crm_db.bulk_delete_inquiries([t1])
    assert del_count == 1
    assert crm_db.get_inquiry_detail(t1) is None
    assert crm_db.get_inquiry_detail(t2) is not None
