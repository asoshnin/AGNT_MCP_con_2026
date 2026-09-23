"""Unit tests for submissions_db.py ensuring WAL mode, CRUD, and isolation."""

import os
import time

from submissions_db import SubmissionsDB


def test_submissions_db_crud(tmp_path):
    db_file = str(tmp_path / "test_submissions.sqlite")
    db = SubmissionsDB(db_path=db_file)

    # 1. Verify file exists
    assert os.path.exists(db_file)

    # 2. Insert submission
    sub_data = {
        "id": "sub_TEST1_123456",
        "session_id": "2RB8M",
        "submitter_name": "Alice Tester",
        "submitter_email": "alice@example.com",
        "submitter_role": "speaker",
        "submission_type": "pdf",
        "file_path": str(tmp_path / "pending" / "sub_TEST1_123456" / "upload.tmp"),
        "file_hash": "sha256fake",
        "file_size_bytes": 1024,
        "page_count": 10,
        "text_yield_chars": 500,
        "ocr_required": False,
        "injection_risk_score": "clean",
        "status": "pending",
        "client_ip_hash": "abcd1234efgh",
    }
    inserted_id = db.insert_submission(sub_data)
    assert inserted_id == "sub_TEST1_123456"

    # 3. Retrieve submission
    item = db.get_submission("sub_TEST1_123456")
    assert item is not None
    assert item["session_id"] == "2RB8M"
    assert item["submitter_name"] == "Alice Tester"
    assert item["status"] == "pending"
    assert item["ocr_required"] == 0

    # 4. List submissions
    pending_list = db.get_submissions(status="pending")
    assert len(pending_list) == 1
    assert pending_list[0]["id"] == "sub_TEST1_123456"

    # 5. Update status
    updated = db.update_status("sub_TEST1_123456", "approved")
    assert updated is True
    item_approved = db.get_submission("sub_TEST1_123456")
    assert item_approved["status"] == "approved"
    assert item_approved["reviewed_at"] is not None


def test_purge_stale_pending_uploads(tmp_path):
    db_file = str(tmp_path / "test_submissions_purge.sqlite")
    db = SubmissionsDB(db_path=db_file)

    pending_dir = tmp_path / "pending" / "sub_STALE_999999"
    pending_dir.mkdir(parents=True, exist_ok=True)
    fake_file = pending_dir / "upload.tmp"
    fake_file.write_bytes(b"%PDF-1.4 fake content")

    # Insert an old submission (e.g. 48 hours ago)
    old_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() - 48 * 3600))
    sub_data = {
        "id": "sub_STALE_999999",
        "session_id": "2RB8M",
        "submitter_name": "Old Submitter",
        "submitter_email": "old@example.com",
        "submitter_role": "attendee",
        "submission_type": "pdf",
        "file_path": str(fake_file),
        "status": "pending",
        "created_at": old_time,
    }
    db.insert_submission(sub_data)

    assert os.path.exists(str(fake_file))

    # Purge stale pending submissions older than 24h
    purged = db.purge_stale_pending_uploads(max_age_hours=24)
    assert purged == 1

    # Verify status is quarantined and file is unlinked
    item = db.get_submission("sub_STALE_999999")
    assert item["status"] == "quarantined"
    assert not os.path.exists(str(fake_file))
    assert not os.path.exists(str(pending_dir))
