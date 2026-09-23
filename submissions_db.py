"""Submissions database state machine for AGNTCon community contributions.
Enforces SQLite WAL mode, busy timeout, CRUD operations, and safe reaper purge.
"""

import os
import shutil
import sqlite3
import time
from typing import Any

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "submissions.sqlite")


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    target_path = db_path or os.environ.get("SUBMISSIONS_DB_PATH", DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


class SubmissionsDB:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.environ.get("SUBMISSIONS_DB_PATH", DB_PATH)
        self.create_tables()

    def get_connection(self) -> sqlite3.Connection:
        return get_db(self.db_path)

    def create_tables(self) -> None:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            token TEXT,
            submitter_name TEXT NOT NULL,
            submitter_email TEXT NOT NULL,
            submitter_role TEXT NOT NULL,
            submission_type TEXT NOT NULL,
            source_url TEXT,
            file_path TEXT,
            file_hash TEXT,
            file_size_bytes INTEGER,
            page_count INTEGER,
            text_yield_chars INTEGER,
            ocr_required BOOLEAN DEFAULT 0,
            injection_risk_score TEXT DEFAULT 'clean',
            injection_details TEXT,
            status TEXT DEFAULT 'pending',
            client_ip_hash TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            rejection_reason TEXT,
            draft_summary TEXT,
            relevance_score INTEGER DEFAULT NULL,
            authenticity_verdict TEXT DEFAULT NULL,
            authenticity_rationale TEXT DEFAULT NULL,
            crm_inquiry_id TEXT DEFAULT NULL
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sub_session ON submissions(session_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sub_status ON submissions(status);")

        # Idempotent column migrations for existing tables
        cur.execute("PRAGMA table_info(submissions);")
        existing_cols = {row["name"] for row in cur.fetchall()}
        migrations = [
            ("relevance_score", "INTEGER DEFAULT NULL"),
            ("authenticity_verdict", "TEXT DEFAULT NULL"),
            ("authenticity_rationale", "TEXT DEFAULT NULL"),
            ("crm_inquiry_id", "TEXT DEFAULT NULL"),
        ]
        for col_name, col_def in migrations:
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE submissions ADD COLUMN {col_name} {col_def};")

        conn.commit()
        conn.close()

    def insert_submission(self, data: dict[str, Any]) -> str:
        conn = self.get_connection()
        cur = conn.cursor()
        sub_id = data["id"]
        cur.execute("""
        INSERT INTO submissions (
            id, session_id, token, submitter_name, submitter_email, submitter_role,
            submission_type, source_url, file_path, file_hash, file_size_bytes,
            page_count, text_yield_chars, ocr_required, injection_risk_score,
            injection_details, status, client_ip_hash, user_agent, created_at,
            reviewed_at, rejection_reason, draft_summary,
            relevance_score, authenticity_verdict, authenticity_rationale, crm_inquiry_id
        ) VALUES (
            :id, :session_id, :token, :submitter_name, :submitter_email, :submitter_role,
            :submission_type, :source_url, :file_path, :file_hash, :file_size_bytes,
            :page_count, :text_yield_chars, :ocr_required, :injection_risk_score,
            :injection_details, :status, :client_ip_hash, :user_agent, :created_at,
            :reviewed_at, :rejection_reason, :draft_summary,
            :relevance_score, :authenticity_verdict, :authenticity_rationale, :crm_inquiry_id
        )
        """, {
            "id": sub_id,
            "session_id": data.get("session_id", ""),
            "token": data.get("token"),
            "submitter_name": data.get("submitter_name", ""),
            "submitter_email": data.get("submitter_email", ""),
            "submitter_role": data.get("submitter_role", "speaker"),
            "submission_type": data.get("submission_type", "pdf"),
            "source_url": data.get("source_url"),
            "file_path": data.get("file_path"),
            "file_hash": data.get("file_hash"),
            "file_size_bytes": data.get("file_size_bytes", 0),
            "page_count": data.get("page_count", 0),
            "text_yield_chars": data.get("text_yield_chars", 0),
            "ocr_required": 1 if data.get("ocr_required") else 0,
            "injection_risk_score": data.get("injection_risk_score", "clean"),
            "injection_details": data.get("injection_details"),
            "status": data.get("status", "pending"),
            "client_ip_hash": data.get("client_ip_hash"),
            "user_agent": data.get("user_agent"),
            "created_at": data.get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S"),
            "reviewed_at": data.get("reviewed_at"),
            "rejection_reason": data.get("rejection_reason"),
            "draft_summary": data.get("draft_summary"),
            "relevance_score": data.get("relevance_score"),
            "authenticity_verdict": data.get("authenticity_verdict"),
            "authenticity_rationale": data.get("authenticity_rationale"),
            "crm_inquiry_id": data.get("crm_inquiry_id"),
        })
        conn.commit()
        conn.close()
        return sub_id

    def get_submission(self, sub_id: str) -> dict[str, Any] | None:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM submissions WHERE id = ?", (sub_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_submissions(self, status: str | None = None) -> list[dict[str, Any]]:
        conn = self.get_connection()
        cur = conn.cursor()
        if status and status != "all":
            cur.execute("SELECT * FROM submissions WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cur.execute("SELECT * FROM submissions ORDER BY created_at DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def update_status(self, sub_id: str, new_status: str, rejection_reason: str | None = None) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            "UPDATE submissions SET status = ?, reviewed_at = ?, rejection_reason = ? WHERE id = ?",
            (new_status, now, rejection_reason, sub_id),
        )
        affected = cur.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def update_verification(
        self, sub_id: str, relevance_score: int, verdict: str, rationale: str
    ) -> bool:
        """Updates automated LLM authenticity verification results."""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE submissions
            SET relevance_score = ?, authenticity_verdict = ?, authenticity_rationale = ?
            WHERE id = ?
            """,
            (relevance_score, verdict, rationale, sub_id),
        )
        affected = cur.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def update_crm_inquiry(self, sub_id: str, crm_inquiry_id: str) -> bool:
        """Links a CRM thread inquiry to this submission."""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE submissions SET crm_inquiry_id = ? WHERE id = ?",
            (crm_inquiry_id, sub_id),
        )
        affected = cur.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def purge_stale_pending_uploads(self, max_age_hours: int = 24) -> int:
        """Purges pending submissions older than max_age_hours and deletes unapproved pending files."""
        conn = self.get_connection()
        cur = conn.cursor()
        cutoff_seconds = time.time() - (max_age_hours * 3600)
        cutoff_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(cutoff_seconds))

        cur.execute(
            "SELECT id, file_path FROM submissions WHERE status = 'pending' AND created_at < ?",
            (cutoff_str,),
        )
        stale_rows = cur.fetchall()

        purged_count = 0
        for row in stale_rows:
            sub_id = row["id"]
            file_path = row["file_path"]
            if file_path and os.path.exists(file_path):
                try:
                    dir_name = os.path.dirname(file_path)
                    if os.path.isdir(dir_name) and "pending" in dir_name:
                        shutil.rmtree(dir_name, ignore_errors=True)
                    else:
                        os.unlink(file_path)
                except Exception:
                    pass
            cur.execute("UPDATE submissions SET status = 'quarantined', rejection_reason = 'expired_stale' WHERE id = ?", (sub_id,))
            purged_count += 1

        conn.commit()
        conn.close()
        return purged_count
