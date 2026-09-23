"""Unit tests for Concierge Batch Ingestion & Session Matching (Sprint 16).
Enforces Test Isolation using tmp_path, Anti-Zip Slip defense (SEC-3009-01),
Two-Tier Matching (DOM-3009-01), and staging in submissions.sqlite.
"""

import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

HUB_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HUB_DIR))
sys.path.insert(0, str(HUB_DIR / "scripts"))

from batch_ingest_folder import (
    batch_ingest,
    load_sessions,
    match_deck_to_session,
    safe_extract_zip,
)
from submissions_db import SubmissionsDB


def make_pdf(dest_path: Path | str, text: str = "Presentation Content") -> Path:
    """Creates a minimal valid PDF containing the specified text."""
    p = Path(dest_path)
    try:
        import pymupdf

        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((50, 72), text)
        doc.save(str(p))
        doc.close()
    except Exception:
        # Fallback to pypdf blank page
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        with open(str(p), "wb") as f:
            writer.write(f)
    return p


# ── Anti-Zip Slip Tests (SEC-3009-01) ──────────────────────────────────────────


def test_zip_slip_rejection_parent_traversal(tmp_path):
    """Verifies that zip archives containing parent directory traversal are rejected."""
    bad_zip = tmp_path / "malicious_parent.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("../../etc/cron.d/evil.sh", b"echo pwned")

    extract_dir = tmp_path / "quarantine"
    with pytest.raises(ValueError, match="Zip Slip attempt detected"):
        safe_extract_zip(bad_zip, extract_dir)


def test_zip_slip_rejection_root_traversal(tmp_path):
    """Verifies that zip archives containing root-relative paths are rejected."""
    bad_zip = tmp_path / "malicious_root.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("/root/.bashrc", b"echo hacked")

    extract_dir = tmp_path / "quarantine"
    with pytest.raises(ValueError, match="Zip Slip attempt detected"):
        safe_extract_zip(bad_zip, extract_dir)


def test_safe_zip_extraction(tmp_path):
    """Verifies that safe zip archives are cleanly extracted to basenames within target root."""
    good_zip = tmp_path / "good.zip"
    with zipfile.ZipFile(good_zip, "w") as zf:
        zf.writestr("nested/folder/keynote.pdf", b"%PDF-1.4 mock content")
        zf.writestr("speaker_deck.pdf", b"%PDF-1.4 mock content 2")

    extract_dir = tmp_path / "quarantine"
    extracted = safe_extract_zip(good_zip, extract_dir)

    assert len(extracted) == 2
    for file_path in extracted:
        p = Path(file_path).resolve()
        assert p.is_relative_to(extract_dir.resolve())
        assert p.exists()


# ── Two-Tier Matching Engine Tests (DOM-3009-01) ──────────────────────────────


@pytest.fixture
def sample_sessions():
    return [
        {
            "id": "2Wur4",
            "session_title": "Delegated Authorization for AI Agents",
            "session_speakers": ["Sohan Maheshwar"],
        },
        {
            "id": "2RB8q",
            "session_title": "Multi-Agent Orchestration Patterns with MCP",
            "session_speakers": ["Alice Wonderland", "Bob Builder"],
        },
        {
            "id": "2RB8M",
            "session_title": "Orchestrating Autonomous AI Teams",
            "session_speakers": ["Carol Danvers"],
        },
    ]


def test_match_tier1_speaker_surname(tmp_path, sample_sessions):
    """Tier 1: Filename containing speaker surname matches with 95% confidence."""
    deck_path = make_pdf(tmp_path / "Maheshwar_final_presentation.pdf", "Introduction to permissions")
    matched_id, confidence = match_deck_to_session(deck_path, sample_sessions)

    assert matched_id == "2Wur4"
    assert confidence >= 0.90


def test_match_tier2_title_semantic_overlap(tmp_path, sample_sessions):
    """Tier 2: Slide title text overlap matches when surname is not in filename."""
    deck_path = make_pdf(
        tmp_path / "deck_generic_01.pdf",
        "Multi-Agent Orchestration Patterns with MCP in Production Enterprise",
    )
    matched_id, confidence = match_deck_to_session(deck_path, sample_sessions)

    assert matched_id == "2RB8q"
    assert 0.50 <= confidence <= 0.95


def test_match_no_match(tmp_path, sample_sessions):
    """Unrelated content and filename returns (None, 0.0)."""
    deck_path = make_pdf(tmp_path / "unrelated_recipe.pdf", "How to bake sourdough bread")
    matched_id, confidence = match_deck_to_session(deck_path, sample_sessions)

    assert matched_id is None
    assert confidence == 0.0


def test_match_respects_missing_session_filter(tmp_path, sample_sessions):
    """Matching restricts candidates to missing_session_ids when supplied."""
    deck_path = make_pdf(tmp_path / "Maheshwar_slides.pdf", "Some slides")
    # Only 2RB8q is missing slides
    missing_ids = {"2RB8q"}
    matched_id, _ = match_deck_to_session(deck_path, sample_sessions, missing_session_ids=missing_ids)

    # 2Wur4 is not in missing_ids, so it should not match 2Wur4
    assert matched_id != "2Wur4"


# ── Batch Ingest Pipeline End-to-End Tests ────────────────────────────────────


def test_batch_ingest_from_folder(tmp_path, sample_sessions):
    """Full folder batch ingestion creates pending submissions with submitter_role='organizer'."""
    in_dir = tmp_path / "incoming"
    in_dir.mkdir()

    # Create 2 matchable PDFs
    make_pdf(in_dir / "Maheshwar_auth.pdf", "Slide text")
    make_pdf(in_dir / "Danvers_orchestration.pdf", "Slide text 2")
    # And 1 unmatchable file
    make_pdf(in_dir / "random_notes.pdf", "Nothing here")

    db_path = tmp_path / "test_submissions.sqlite"
    sess_file = tmp_path / "sessions.json"
    sess_file.write_text(json.dumps(sample_sessions), encoding="utf-8")
    pending_dir = tmp_path / "pending"

    res = batch_ingest(
        input_path=in_dir,
        db_path=db_path,
        sessions_path=sess_file,
        pending_dir=pending_dir,
        missing_session_ids={"2Wur4", "2RB8M"},
    )

    assert res["total_files"] == 3
    assert res["matched"] == 2
    assert res["unmatched"] == 1

    db = SubmissionsDB(str(db_path))
    subs = db.get_submissions("pending")
    assert len(subs) == 2

    for sub in subs:
        assert sub["submitter_role"] == "organizer"
        assert sub["status"] == "pending"
        assert sub["match_confidence"] is not None
        assert sub["match_confidence"] >= 0.50
        assert os.path.exists(sub["file_path"])
        assert Path(sub["file_path"]).is_relative_to(pending_dir)


def test_batch_ingest_from_zip(tmp_path, sample_sessions):
    """ZIP archive batch ingestion safely unzips and stages submissions."""
    zip_path = tmp_path / "organizer_dump.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        pdf1 = make_pdf(tmp_path / "tmp1.pdf", "Text")
        zf.write(pdf1, arcname="slides/Maheshwar_keynote.pdf")

    db_path = tmp_path / "test_submissions.sqlite"
    sess_file = tmp_path / "sessions.json"
    sess_file.write_text(json.dumps(sample_sessions), encoding="utf-8")
    pending_dir = tmp_path / "pending"

    res = batch_ingest(
        input_path=zip_path,
        db_path=db_path,
        sessions_path=sess_file,
        pending_dir=pending_dir,
        missing_session_ids={"2Wur4"},
    )

    assert res["total_files"] == 1
    assert res["matched"] == 1

    db = SubmissionsDB(str(db_path))
    subs = db.get_submissions("pending")
    assert len(subs) == 1
    assert subs[0]["session_id"] == "2Wur4"
    assert subs[0]["submitter_role"] == "organizer"


def test_batch_ingest_cli_execution(tmp_path, sample_sessions):
    """Executes the CLI script batch_ingest_folder.py via subprocess."""
    in_dir = tmp_path / "incoming"
    in_dir.mkdir()
    make_pdf(in_dir / "Danvers_slides.pdf", "Content")

    db_path = tmp_path / "test_submissions.sqlite"
    sess_file = tmp_path / "sessions.json"
    sess_file.write_text(json.dumps(sample_sessions), encoding="utf-8")
    pending_dir = tmp_path / "pending"

    cmd = [
        sys.executable,
        str(HUB_DIR / "scripts" / "batch_ingest_folder.py"),
        "--input", str(in_dir),
        "--db", str(db_path),
        "--sessions", str(sess_file),
        "--pending-dir", str(pending_dir),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Batch Ingestion Complete" in proc.stdout
    assert "2RB8M" in proc.stdout


# ── Frontend Contract Verification (DOM-3009-02, CLA-3009-01) ─────────────────


def test_index_html_organizer_elements():
    """Verifies that index.html contains all required DOM elements for Sprint 16."""
    html_path = HUB_DIR / "site" / "index.html"
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")

    # FR-1.1: Missing slides filter tab
    assert 'id="tab-filter-missing-slides"' in content
    assert 'id="missing-slides-count"' in content

    # FR-2: Autocomplete session selector wrap & select
    assert 'id="contrib-session-picker-wrap"' in content
    assert 'id="contrib-select-session"' in content

    # FR-3: Dynamic license consent label
    assert 'id="contrib-license-label"' in content


def test_app_js_organizer_and_presenter_logic():
    """Verifies that app.js implements dynamic counting, filtering, session picker, and consent switching."""
    js_path = HUB_DIR / "site" / "assets" / "app.js"
    assert js_path.exists()
    content = js_path.read_text(encoding="utf-8")

    # Dynamic count and filter
    assert "updateMissingSlidesCount" in content
    assert "MISSING_SLIDES_ONLY" in content
    assert "tab-filter-missing-slides" in content

    # Multi-session picker and Lock-in Precedence (CLA-3009-01)
    assert "populateContribSessionPicker" in content
    assert "updateSessionPickerVisibility" in content
    assert "updateSelectedSessionPreview" in content

    # Dynamic legal consent text (FR-3)
    assert "updateConsentText" in content
    assert "authorized representative of the AGNTCon organizing committee" in content

    # Multi-submission workflow loop (FR-1.3)
    assert "btn-submit-another" in content

