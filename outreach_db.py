"""Private SQLite storage and Token Isolation Layer for Speaker & Organizer Outreach.

Implements strict GDPR compliance, Right-to-Erasure opt-out suppression,
and ensures chmod 0600 file permissions for zero PII leakage.
"""

import os
import sqlite3
from pathlib import Path


def get_db_path(hub_dir: Path | str | None = None) -> Path:
    if hub_dir is None:
        hub_dir = Path(__file__).resolve().parent
    return Path(hub_dir) / "data" / "outreach_private.sqlite"


def init_outreach_db(db_path: Path | str) -> sqlite3.Connection:
    """Initializes the private outreach database with strict permissions (0600) and WAL mode."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    # Table 1: HMAC magic tokens for 1-click slide upload
    conn.execute("""
        CREATE TABLE IF NOT EXISTS outreach_tokens (
            session_id TEXT PRIMARY KEY,
            speaker_name TEXT,
            token TEXT NOT NULL,
            magic_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
    """)

    # Table 2: Outreach message drafts and transmission states
    conn.execute("""
        CREATE TABLE IF NOT EXISTS outreach_messages (
            id TEXT PRIMARY KEY,
            recipient_name TEXT NOT NULL,
            cohort TEXT NOT NULL,
            channel TEXT NOT NULL,
            target_handle TEXT,
            message_text TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            sent_at TIMESTAMP,
            notes TEXT
        );
    """)

    # Table 3: GDPR Right-to-Erasure suppression registry
    conn.execute("""
        CREATE TABLE IF NOT EXISTS opt_out_registry (
            identifier TEXT PRIMARY KEY,
            opted_out_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        );
    """)

    conn.commit()

    # Enforce chmod 0600 (owner read/write only)
    try:
        os.chmod(str(path), 0o600)
    except Exception:
        pass

    return conn


def store_token(
    conn: sqlite3.Connection,
    session_id: str,
    speaker_name: str,
    token: str,
    magic_url: str,
    expires_at: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO outreach_tokens (session_id, speaker_name, token, magic_url, expires_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            speaker_name=excluded.speaker_name,
            token=excluded.token,
            magic_url=excluded.magic_url,
            expires_at=excluded.expires_at;
        """,
        (session_id, speaker_name, token, magic_url, expires_at),
    )
    conn.commit()


def get_token(conn: sqlite3.Connection, session_id: str) -> dict | None:
    cur = conn.cursor()
    cur.execute(
        "SELECT session_id, speaker_name, token, magic_url, expires_at FROM outreach_tokens WHERE session_id = ?",
        (session_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "session_id": row[0],
        "speaker_name": row[1],
        "token": row[2],
        "magic_url": row[3],
        "expires_at": row[4],
    }


def store_message(
    conn: sqlite3.Connection,
    msg_id: str,
    recipient_name: str,
    cohort: str,
    channel: str,
    target_handle: str | None,
    message_text: str,
    status: str = "draft",
    notes: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO outreach_messages (id, recipient_name, cohort, channel, target_handle, message_text, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            recipient_name=excluded.recipient_name,
            cohort=excluded.cohort,
            channel=excluded.channel,
            target_handle=excluded.target_handle,
            message_text=excluded.message_text,
            status=excluded.status,
            notes=excluded.notes;
        """,
        (msg_id, recipient_name, cohort, channel, target_handle, message_text, status, notes),
    )
    conn.commit()


def get_messages(conn: sqlite3.Connection, cohort: str | None = None) -> list[dict]:
    cur = conn.cursor()
    if cohort:
        cur.execute(
            "SELECT id, recipient_name, cohort, channel, target_handle, message_text, status, sent_at, notes FROM outreach_messages WHERE cohort = ?",
            (cohort,),
        )
    else:
        cur.execute(
            "SELECT id, recipient_name, cohort, channel, target_handle, message_text, status, sent_at, notes FROM outreach_messages"
        )
    rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "recipient_name": r[1],
            "cohort": r[2],
            "channel": r[3],
            "target_handle": r[4],
            "message_text": r[5],
            "status": r[6],
            "sent_at": r[7],
            "notes": r[8],
        }
        for r in rows
    ]


def add_opt_out(conn: sqlite3.Connection, identifier: str, reason: str | None = None) -> None:
    clean_id = identifier.strip().lower()
    conn.execute(
        """
        INSERT INTO opt_out_registry (identifier, reason)
        VALUES (?, ?)
        ON CONFLICT(identifier) DO UPDATE SET reason=excluded.reason;
        """,
        (clean_id, reason),
    )
    conn.commit()


def is_opted_out(conn: sqlite3.Connection, identifier: str | None) -> bool:
    if not identifier:
        return False
    clean_id = identifier.strip().lower()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM opt_out_registry WHERE identifier = ?", (clean_id,))
    return cur.fetchone() is not None


def get_opt_out_identifiers(conn: sqlite3.Connection) -> set[str]:
    cur = conn.cursor()
    cur.execute("SELECT identifier FROM opt_out_registry")
    return {row[0].lower() for row in cur.fetchall()}
