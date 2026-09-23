#!/usr/bin/env python3
"""Batch ingestion and matching tool for organizer presentation decks.
Supports folder path or ZIP archive, Anti-Zip Slip protection (SEC-3009-01),
two-tier session matching (Speaker Surname + Slide Title),
and stages matched presentations into data/submissions.sqlite and data/submissions/pending/<sub_id>/.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

# Auto-resolve parent import path for submissions_db
HUB_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HUB_DIR))

from submissions_db import SubmissionsDB


def run_extract_worker(pdf_path: str | Path, max_pages: int = 120) -> dict | None:
    """Runs extract_pdf_worker in an isolated subprocess to protect parent process memory."""
    worker_script = HUB_DIR / "scripts" / "extract_pdf_worker.py"
    if not worker_script.exists():
        return None
    cmd = [sys.executable, str(worker_script), str(pdf_path), str(max_pages)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20.0)
        if proc.stdout:
            return json.loads(proc.stdout)
    except Exception:
        pass
    return None


STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "are", "you", "your",
    "how", "what", "can", "into", "our", "all", "out", "over", "about", "using",
    "more", "when", "then", "will", "have", "been", "session", "talk", "slides",
    "presentation", "agntcon", "mcpcon", "europe", "2026", "building", "build"
}


def safe_extract_zip(zip_path: str | Path, extract_to: str | Path) -> list[str]:
    """Safely extracts ZIP archive rejecting Zip Slip path traversal (SEC-3009-01).

    Sanitizes all member filenames using os.path.basename and enforces
    Path.resolve().is_relative_to(target_root).
    Rejects path traversal (.. or leading / or \\).
    """
    import zipfile

    extracted_files: list[str] = []
    target_root = Path(extract_to).resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(str(zip_path), "r") as zf:
        for member in zf.infolist():
            raw_name = member.filename
            # Reject directory traversal and root-relative paths (SEC-3009-01)
            if raw_name.startswith("/") or raw_name.startswith("\\") or ".." in raw_name:
                raise ValueError(f"Zip Slip attempt detected: {raw_name}")

            clean_name = os.path.basename(raw_name)
            if not clean_name or raw_name.endswith("/") or raw_name.endswith("\\"):
                continue

            dest_path = (target_root / clean_name).resolve()
            if not dest_path.is_relative_to(target_root):
                raise ValueError(f"Zip Slip attempt detected: {raw_name}")

            with zf.open(member) as source, open(dest_path, "wb") as target:
                shutil.copyfileobj(source, target)
            extracted_files.append(str(dest_path))

    return extracted_files


def load_sessions(sessions_path: str | Path) -> list[dict]:
    """Loads session catalog from sessions.json or equivalent JSON file."""
    with open(str(sessions_path), encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        # Could be {session_id: dict, ...}
        return list(data.values())
    elif isinstance(data, list):
        return data
    return []


def get_missing_session_ids(hub_dir: Path | None = None) -> set[str]:
    """Extracts session IDs that are missing slide presentations."""
    root = hub_dir or HUB_DIR
    index_file = root / "wiki" / "index.json"
    if index_file.exists():
        try:
            with open(index_file, encoding="utf-8") as f:
                items = json.load(f)
            return {it["id"] for it in items if not it.get("has_slides")}
        except Exception:
            pass
    return set()


def extract_pdf_first_pages_text(pdf_path: str | Path, max_pages: int = 2) -> str:
    """Extracts raw text from the first max_pages of a PDF."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path), strict=False)
        pages_count = min(len(reader.pages), max_pages)
        texts = [reader.pages[i].extract_text() or "" for i in range(pages_count)]
        return " ".join(texts)
    except Exception:
        return ""


def match_deck_to_session(
    pdf_path: str | Path,
    sessions: list[dict] | dict,
    missing_session_ids: set[str] | None = None,
) -> tuple[str | None, float]:
    """Two-tier matching engine:
    Tier 1: Speaker surname matching against sessions.json.
    Tier 2: Slide title text overlap.
    """
    if isinstance(sessions, dict):
        sess_list = list(sessions.values())
    else:
        sess_list = sessions

    filename = os.path.basename(str(pdf_path)).lower()
    fn_name_only = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE)
    fn_tokens = set(re.findall(r"[a-z0-9]{3,}", fn_name_only)) - STOPWORDS

    # Filter candidate pool to missing_session_ids if non-empty
    if missing_session_ids:
        candidates = [s for s in sess_list if s.get("id") in missing_session_ids]
        if not candidates:
            # Fall back to all sessions if missing list empty/not matched
            candidates = sess_list
    else:
        candidates = sess_list

    # ── Tier 1: Speaker Surname Matching ───────────────────────────
    for s in candidates:
        sid = s.get("id", "")
        speakers = s.get("session_speakers") or s.get("speakers") or []
        for spk in speakers:
            spk_parts = re.findall(r"[a-zA-Z]+", str(spk).lower())
            surname = spk_parts[-1] if spk_parts else ""
            if len(surname) >= 3 and surname in filename:
                return sid, 0.95

    # ── Tier 2: Slide Title Text Overlap ───────────────────────────
    pdf_text = extract_pdf_first_pages_text(pdf_path, max_pages=2)
    sample_tokens = set(re.findall(r"[a-z0-9]{3,}", pdf_text.lower())) - STOPWORDS

    best_match_id = None
    best_score = 0.0

    for s in candidates:
        sid = s.get("id", "")
        title = s.get("session_title") or s.get("title") or ""
        title_tokens = set(re.findall(r"[a-z0-9]{3,}", title.lower())) - STOPWORDS
        if not title_tokens:
            continue

        # Overlap between slide content / filename and session title
        overlap = (sample_tokens & title_tokens) | (fn_tokens & title_tokens)
        if len(overlap) >= 2:
            score = len(overlap) / len(title_tokens)
            if score > best_score:
                best_score = score
                best_match_id = sid

    if best_match_id and best_score >= 0.30:
        confidence = round(min(0.92, max(0.50, best_score)), 2)
        return best_match_id, confidence

    return None, 0.0


def stage_submission(
    pdf_path: str | Path,
    session_id: str,
    confidence: float,
    db: SubmissionsDB,
    pending_dir: Path,
    submitter_name: str = "Conference Concierge Ingestion",
    submitter_email: str = "organizer@agntcon.eu",
) -> str:
    """Stages a matched PDF into data/submissions/pending/<sub_id>/ and records in submissions.sqlite."""
    sub_id = f"sub_org_{uuid.uuid4().hex[:10]}"
    sub_pending_dir = pending_dir / sub_id
    sub_pending_dir.mkdir(parents=True, exist_ok=True)

    clean_basename = os.path.basename(str(pdf_path))
    dest_file = sub_pending_dir / clean_basename
    shutil.copyfile(str(pdf_path), str(dest_file))

    with open(str(dest_file), "rb") as f:
        file_bytes = f.read()

    file_size = len(file_bytes)
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    page_count = 1
    text_yield = 0
    ocr_required = False
    risk_score = "clean"
    injection_details = None

    scan_res = run_extract_worker(str(dest_file), max_pages=120)
    if scan_res:
        page_count = scan_res.get("page_count", 1)
        text_yield = scan_res.get("text_yield_chars", 0)
        ocr_required = bool(scan_res.get("ocr_required", False))
        risk_score = scan_res.get("injection_risk_score", "clean")
        injection_details = scan_res.get("injection_details")
    else:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(dest_file), strict=False)
            page_count = len(reader.pages)
        except Exception:
            pass

    db.insert_submission({
        "id": sub_id,
        "session_id": session_id,
        "token": None,
        "submitter_name": submitter_name,
        "submitter_email": submitter_email,
        "submitter_role": "organizer",
        "submission_type": "pdf",
        "source_url": None,
        "file_path": str(dest_file),
        "file_hash": file_hash,
        "file_size_bytes": file_size,
        "page_count": page_count,
        "text_yield_chars": text_yield,
        "ocr_required": 1 if ocr_required else 0,
        "injection_risk_score": risk_score,
        "injection_details": injection_details,
        "status": "pending",
        "client_ip_hash": "concierge_batch",
        "user_agent": "agntcon-batch-ingest/1.0",
        "draft_summary": f"Concierge batch ingested with match confidence {int(confidence * 100)}%",
        "match_confidence": confidence,
    })

    return sub_id


def batch_ingest(
    input_path: str | Path,
    db_path: str | Path | None = None,
    sessions_path: str | Path | None = None,
    pending_dir: str | Path | None = None,
    missing_session_ids: set[str] | None = None,
    submitter_name: str = "Conference Concierge Ingestion",
    submitter_email: str = "organizer@agntcon.eu",
) -> dict:
    """Executes end-to-end batch ingestion of folder or ZIP archive."""
    input_p = Path(input_path).resolve()
    if not input_p.exists():
        raise FileNotFoundError(f"Input path not found: {input_p}")

    hub_root = HUB_DIR
    db = SubmissionsDB(str(db_path) if db_path else None)

    sess_p = Path(sessions_path).resolve() if sessions_path else (hub_root / "data" / "sessions.json")
    sessions = load_sessions(sess_p)

    target_pending = Path(pending_dir).resolve() if pending_dir else (hub_root / "data" / "submissions" / "pending")
    target_pending.mkdir(parents=True, exist_ok=True)

    if missing_session_ids is None:
        missing_session_ids = get_missing_session_ids(hub_root)

    temp_extract_dir = None
    pdf_files: list[str] = []

    try:
        if input_p.is_file() and input_p.suffix.lower() == ".zip":
            temp_extract_dir = tempfile.mkdtemp(prefix="agntcon_batch_zip_")
            pdf_files = safe_extract_zip(input_p, temp_extract_dir)
            # Keep only pdf files
            pdf_files = [f for f in pdf_files if f.lower().endswith(".pdf")]
        elif input_p.is_dir():
            for root, _, files in os.walk(str(input_p)):
                for file in files:
                    if file.lower().endswith(".pdf"):
                        pdf_files.append(os.path.join(root, file))
        elif input_p.is_file() and input_p.suffix.lower() == ".pdf":
            pdf_files.append(str(input_p))
        else:
            raise ValueError(f"Unsupported input type: {input_p}. Must be folder or .zip archive or .pdf file.")

        results = {
            "total_files": len(pdf_files),
            "matched": 0,
            "unmatched": 0,
            "submissions": [],
        }

        for pdf_file in pdf_files:
            sess_id, confidence = match_deck_to_session(pdf_file, sessions, missing_session_ids)
            if sess_id:
                sub_id = stage_submission(
                    pdf_path=pdf_file,
                    session_id=sess_id,
                    confidence=confidence,
                    db=db,
                    pending_dir=target_pending,
                    submitter_name=submitter_name,
                    submitter_email=submitter_email,
                )
                results["matched"] += 1
                results["submissions"].append({
                    "sub_id": sub_id,
                    "session_id": sess_id,
                    "file": os.path.basename(pdf_file),
                    "confidence": confidence,
                })
            else:
                results["unmatched"] += 1

        return results
    finally:
        if temp_extract_dir and os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description="Concierge Batch Ingestion & Session Matching for AGNTCon EU 2026."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to folder or ZIP archive containing keynote/presentation decks.",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="Path to submissions.sqlite database.",
    )
    parser.add_argument(
        "--sessions",
        default=None,
        help="Path to sessions.json catalog.",
    )
    parser.add_argument(
        "--pending-dir",
        default=None,
        help="Path to staging pending submissions directory.",
    )
    parser.add_argument(
        "--submitter-name",
        default="Conference Concierge Ingestion",
        help="Name to record as submitter.",
    )
    parser.add_argument(
        "--submitter-email",
        default="organizer@agntcon.eu",
        help="Email to record as submitter.",
    )

    args = parser.parse_args()

    try:
        res = batch_ingest(
            input_path=args.input,
            db_path=args.db,
            sessions_path=args.sessions,
            pending_dir=args.pending_dir,
            submitter_name=args.submitter_name,
            submitter_email=args.submitter_email,
        )
        print(f"Batch Ingestion Complete: {res['matched']}/{res['total_files']} decks matched.")
        for item in res["submissions"]:
            print(f"  ✓ [{item['session_id']}] {item['file']} -> {item['sub_id']} (confidence: {int(item['confidence']*100)}%)")
        if res["unmatched"] > 0:
            print(f"  ⚠️  {res['unmatched']} files could not be matched with high confidence.")
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"Error during batch ingestion: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
