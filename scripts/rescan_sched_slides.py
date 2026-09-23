#!/usr/bin/env python3
"""Automated Re-scan of Sched.com for newly uploaded presentation decks.

Politely scans sessions missing slides against official Sched event URLs:
https://agntconmcpconeu26.sched.com/event/<session_id>
Detects attached PDFs from hosted-files.sched.co, validates %PDF- magic bytes,
enforces file size ceiling (40MB), extracts text via extract_pdf_worker.py,
indexes incrementally into FTS5 & FastEmbed via hub_incremental.py,
and updates wiki/index.json and data/sessions.json.
Enforces RESCAN_LOCK to prevent overlapping scans.
"""

import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Resolve base paths
HUB_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger("sched_rescan")

# Concurrent Re-Scan Lock (SEC-S17-02)
RESCAN_LOCK = threading.Lock()

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
MAX_PDF_BYTES = 40 * 1024 * 1024  # 40MB ceiling


def run_extract_worker(hub_dir: Path, pdf_path: Path, max_pages: int = 120) -> dict | None:
    """Runs extract_pdf_worker in an isolated subprocess to protect parent process memory."""
    worker_script = hub_dir / "scripts" / "extract_pdf_worker.py"
    if not worker_script.exists():
        return None
    cmd = [sys.executable, str(worker_script), str(pdf_path), str(max_pages)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25.0)
        if proc.stdout:
            return json.loads(proc.stdout)
    except Exception as e:
        logger.warning(f"Error running extract worker for {pdf_path}: {e}")
    return None


def sync_speaker_cohort(hub_dir: Path | str, session_id: str, has_slides: bool = True) -> bool:
    """Updates the speaker's session slide status and transitions their cohort from cohort_missing_slides to cohort_slides_available."""
    hub_path = Path(hub_dir)
    contacts_path = hub_path / "data" / "contacts.json"
    summary_path = hub_path / "data" / "contacts_summary.json"

    if not contacts_path.exists():
        return False

    try:
        with open(contacts_path, encoding="utf-8") as f:
            contacts_data = json.load(f)

        speakers = contacts_data.get("speakers", [])
        modified = False

        for spk in speakers:
            sessions = spk.get("sessions", [])
            spk_has_sid = False
            for s in sessions:
                if s.get("session_id") == session_id:
                    s["has_slides"] = has_slides
                    s["slide_url"] = f"/assets/slides/{session_id}.pdf" if has_slides else None
                    spk_has_sid = True
                    modified = True

            if spk_has_sid:
                if any(s.get("has_slides") for s in sessions):
                    spk["cohort"] = "cohort_slides_available"
                else:
                    spk["cohort"] = "cohort_missing_slides"

        if not modified:
            return False

        organizers = contacts_data.get("organizers", [])
        missing_count = sum(1 for s in speakers if s.get("cohort") == "cohort_missing_slides")
        available_count = sum(1 for s in speakers if s.get("cohort") == "cohort_slides_available")
        org_count = len(organizers)

        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        contacts_data["updated_at"] = now_iso
        contacts_data["cohorts_summary"] = {
            "cohort_organizers": org_count,
            "cohort_missing_slides": missing_count,
            "cohort_slides_available": available_count,
        }

        tmp_contacts = contacts_path.with_suffix(".tmp")
        with open(tmp_contacts, "w", encoding="utf-8") as f:
            json.dump(contacts_data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_contacts, contacts_path)

        summary_payload = {
            "updated_at": now_iso,
            "total_speakers": len(speakers),
            "total_organizers": org_count,
            "cohort_organizers_count": org_count,
            "cohort_missing_slides_count": missing_count,
            "cohort_slides_available_count": available_count,
        }
        tmp_summary = summary_path.with_suffix(".tmp")
        with open(tmp_summary, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp_summary, summary_path)

        return True
    except Exception as e:
        logger.warning(f"Error syncing speaker cohort for {session_id}: {e}")
        return False


def _download_pdf_safely(url: str, dest_path: Path, headers: dict) -> tuple[bool, str]:
    """Downloads PDF from hosted-files.sched.co strictly, verifying SSRF rules, size, and %PDF- magic bytes."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "invalid_scheme"
    if parsed.netloc.lower() != "hosted-files.sched.co":
        return False, "disallowed_host"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25.0) as res:
            first_chunk = res.read(1024)
            if not first_chunk.startswith(b"%PDF-"):
                return False, "invalid_magic_bytes"

            total_bytes = bytearray(first_chunk)
            while True:
                chunk = res.read(64 * 1024)
                if not chunk:
                    break
                total_bytes.extend(chunk)
                if len(total_bytes) > MAX_PDF_BYTES:
                    return False, "file_too_large"

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(total_bytes)
            return True, "ok"
    except Exception as e:
        return False, f"download_failed: {e}"


def _execute_rescan(hub_dir: Path, delay_s: float = 0.2) -> dict:
    """Internal execution logic for polite Sched re-scan."""
    index_json_path = hub_dir / "wiki" / "index.json"
    sessions_json_path = hub_dir / "data" / "sessions.json"
    slides_dir = hub_dir / "site" / "assets" / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    if not index_json_path.exists():
        return {
            "status": "error",
            "error": f"{index_json_path} not found",
            "scanned_count": 0,
            "newly_found_count": 0,
            "ingested_sessions": [],
            "remaining_missing": 0,
        }

    with open(index_json_path, encoding="utf-8") as f:
        talks = json.load(f)

    # Missing talks from wiki/index.json
    missing_talks = [t for t in talks if not t.get("has_slides")]
    scanned_count = len(missing_talks)
    ingested_sessions: list[str] = []

    # Import incremental upsert dynamically from hub_incremental
    sys.path.insert(0, str(hub_dir))
    try:
        import hub_incremental
    except ImportError:
        hub_incremental = None

    headers = {"User-Agent": USER_AGENT}

    for t in missing_talks:
        sid = t.get("id")
        if not sid:
            continue

        sched_event_url = f"https://agntconmcpconeu26.sched.com/event/{sid}"
        req = urllib.request.Request(sched_event_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10.0) as res:
                html = res.read().decode("utf-8", errors="ignore")
                hosted_links = list(set(re.findall(r"https?://hosted-files\.sched\.co[^\s\"\'<>]+", html)))
                pdf_decks = [h for h in hosted_links if ".pdf" in h.lower()]

                if pdf_decks:
                    deck_url = pdf_decks[0]
                    dest_pdf = slides_dir / f"{sid}.pdf"

                    success, _reason = _download_pdf_safely(deck_url, dest_pdf, headers)
                    if success:
                        extracted = run_extract_worker(hub_dir, dest_pdf)
                        slides_text = ""
                        if extracted and extracted.get("sample_text"):
                            slides_text = extracted["sample_text"]

                        summary = t.get("one_paragraph", "")
                        if hub_incremental:
                            hub_incremental.incremental_upsert(
                                session_id=sid,
                                slides_text=slides_text,
                                summary=summary,
                                hub_dir=str(hub_dir),
                            )

                        t["has_slides"] = True
                        ingested_sessions.append(sid)
        except Exception as e:
            logger.debug(f"Sched fetch skipped for {sid}: {e}")

        if delay_s > 0:
            time.sleep(delay_s)

    # Atomically update wiki/index.json
    tmp_index_path = index_json_path.with_suffix(".tmp")
    with open(tmp_index_path, "w", encoding="utf-8") as f:
        json.dump(talks, f, indent=2, ensure_ascii=False)
    os.replace(tmp_index_path, index_json_path)

    # Atomically update data/sessions.json if present
    if sessions_json_path.exists() and ingested_sessions:
        try:
            with open(sessions_json_path, encoding="utf-8") as sf:
                sessions_data = json.load(sf)
            modified_sessions = False
            for sid in ingested_sessions:
                if isinstance(sessions_data, dict) and sid in sessions_data:
                    sessions_data[sid]["has_slides"] = True
                    modified_sessions = True
                elif isinstance(sessions_data, list):
                    for s_item in sessions_data:
                        if s_item.get("id") == sid:
                            s_item["has_slides"] = True
                            modified_sessions = True
            if modified_sessions:
                tmp_sessions_path = sessions_json_path.with_suffix(".tmp")
                with open(tmp_sessions_path, "w", encoding="utf-8") as sf:
                    json.dump(sessions_data, sf, indent=2, ensure_ascii=False)
                os.replace(tmp_sessions_path, sessions_json_path)
        except Exception as e:
            logger.warning(f"Failed to update data/sessions.json: {e}")

    # Synchronize speaker cohorts in data/contacts.json (Sprint 18)
    if ingested_sessions:
        for sid in ingested_sessions:
            sync_speaker_cohort(hub_dir, sid, has_slides=True)

    remaining_missing = scanned_count - len(ingested_sessions)

    return {
        "status": "completed",
        "scanned_count": scanned_count,
        "newly_found_count": len(ingested_sessions),
        "ingested_sessions": ingested_sessions,
        "remaining_missing": remaining_missing,
    }


def rescan_sched(hub_dir: str | Path | None = None, delay_s: float = 0.2) -> dict:
    """Thread-safe public entry point to re-scan Sched.com for new slides."""
    target_hub = Path(hub_dir) if hub_dir else HUB_DIR
    if not RESCAN_LOCK.acquire(blocking=False):
        return {
            "status": "busy",
            "error": "A Sched re-scan is already in progress.",
            "scanned_count": 0,
            "newly_found_count": 0,
            "ingested_sessions": [],
            "remaining_missing": 0,
        }
    try:
        return _execute_rescan(target_hub, delay_s)
    finally:
        RESCAN_LOCK.release()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Re-scan Sched.com for newly attached presentation decks")
    parser.add_argument("--hub-dir", default=str(HUB_DIR), help="Path to 02_public_hub root directory")
    parser.add_argument("--delay", type=float, default=0.2, help="Politeness sleep delay between requests (default: 0.2s)")
    args = parser.parse_args()

    result = rescan_sched(args.hub_dir, delay_s=args.delay)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
