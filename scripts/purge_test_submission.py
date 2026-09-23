#!/usr/bin/env python3
"""Clean Rollback Helper: Purges a test submission and restores session slide status."""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

HUB_DIR = Path(__file__).resolve().parent.parent


def purge_test_session(session_id: str, hub_dir: Path | str = HUB_DIR) -> dict:
    hub_dir = Path(hub_dir)
    res = {"session_id": session_id, "actions": []}

    # 1. Remove slide PDF if exists
    pdf_path = hub_dir / "site" / "assets" / "slides" / f"{session_id}.pdf"
    if pdf_path.exists():
        pdf_path.unlink()
        res["actions"].append(f"Deleted {pdf_path}")

    # 2. Update wiki/index.json
    index_path = hub_dir / "wiki" / "index.json"
    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            talks = json.load(f)
        modified = False
        for t in talks:
            if t.get("id") == session_id:
                t["has_slides"] = False
                modified = True
        if modified:
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(talks, f, indent=2, ensure_ascii=False)
            res["actions"].append(f"Reset has_slides: false in {index_path}")

    # 3. Update data/sessions.json
    sessions_path = hub_dir / "data" / "sessions.json"
    if sessions_path.exists():
        with open(sessions_path, encoding="utf-8") as f:
            s_data = json.load(f)
        if isinstance(s_data, dict) and session_id in s_data:
            s_data[session_id]["has_slides"] = False
            with open(sessions_path, "w", encoding="utf-8") as f:
                json.dump(s_data, f, indent=2, ensure_ascii=False)
            res["actions"].append(f"Reset has_slides: false in {sessions_path}")
        elif isinstance(s_data, list):
            for t in s_data:
                if t.get("id") == session_id:
                    t["has_slides"] = False
            with open(sessions_path, "w", encoding="utf-8") as f:
                json.dump(s_data, f, indent=2, ensure_ascii=False)
            res["actions"].append(f"Reset has_slides: false in {sessions_path}")

    # 4. Remove from submissions.sqlite
    sub_db = hub_dir / "data" / "submissions.sqlite"
    if sub_db.exists():
        conn = sqlite3.connect(str(sub_db))
        cur = conn.cursor()
        cur.execute("DELETE FROM submissions WHERE session_id = ?", (session_id,))
        deleted_count = cur.rowcount
        conn.commit()
        conn.close()
        res["actions"].append(f"Deleted {deleted_count} submission records from {sub_db}")

    return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge test submission")
    parser.add_argument("session_id", help="5-char session ID (e.g. 2RBA6)")
    args = parser.parse_args()
    result = purge_test_session(args.session_id)
    print(json.dumps(result, indent=2))
