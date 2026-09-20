"""Lightweight SQLite CRM and Thread Message Storage for AGNTCon Knowledge Hub.
Enforces WAL mode, busy timeout, and atomic writes.
"""

import sqlite3
import os
import time
import uuid
import secrets

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "crm.sqlite")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_crm_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inquiries (
        id TEXT PRIMARY KEY,
        secret_token TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'new',
        project_name TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        organization TEXT,
        profile_url TEXT,
        session_id TEXT,
        title TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS thread_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inquiry_id TEXT NOT NULL,
        sender_type TEXT NOT NULL,
        body TEXT NOT NULL,
        is_internal_note BOOLEAN NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (inquiry_id) REFERENCES inquiries(id)
    );
    """)
    conn.commit()
    conn.close()

def create_inquiry(inquiry_type: str, name: str, email: str, org: str = "", profile: str = "", session_id: str = "", title: str = "", initial_message: str = "", project_name: str = "AGNTCon EU 2026") -> dict:
    init_crm_db()
    ticket_num = secrets.randbelow(9000) + 1000
    ticket_id = f"TICK-{ticket_num}"
    secret_token = secrets.token_hex(16)
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO inquiries (id, secret_token, type, status, project_name, name, email, organization, profile_url, session_id, title, created_at, updated_at)
    VALUES (?, ?, ?, 'new', ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticket_id, secret_token, inquiry_type, project_name, name, email, org, profile, session_id, title, now, now))

    if initial_message:
        cur.execute("""
        INSERT INTO thread_messages (inquiry_id, sender_type, body, is_internal_note, created_at)
        VALUES (?, 'client', ?, 0, ?)
        """, (ticket_id, initial_message, now))

    conn.commit()
    conn.close()

    return {
        "id": ticket_id,
        "secret_token": secret_token,
        "name": name,
        "email": email,
        "type": inquiry_type,
        "title": title
    }

def get_inquiries_list(status_filter: str = None) -> list:
    init_crm_db()
    conn = get_db()
    cur = conn.cursor()
    if status_filter and status_filter != "all":
        cur.execute("SELECT * FROM inquiries WHERE status = ? ORDER BY updated_at DESC", (status_filter,))
    else:
        cur.execute("SELECT * FROM inquiries ORDER BY updated_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_inquiry_detail(inquiry_id: str) -> dict | None:
    init_crm_db()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inquiries WHERE id = ?", (inquiry_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    inquiry = dict(row)

    cur.execute("SELECT * FROM thread_messages WHERE inquiry_id = ? ORDER BY id ASC", (inquiry_id,))
    inquiry["messages"] = [dict(m) for m in cur.fetchall()]
    conn.close()
    return inquiry

def add_message(inquiry_id: str, sender_type: str, body: str, is_note: bool = False, new_status: str = None) -> dict:
    init_crm_db()
    conn = get_db()
    cur = conn.cursor()
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
    INSERT INTO thread_messages (inquiry_id, sender_type, body, is_internal_note, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (inquiry_id, sender_type, body, 1 if is_note else 0, now))

    if new_status:
        cur.execute("UPDATE inquiries SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, inquiry_id))
    else:
        cur.execute("UPDATE inquiries SET updated_at = ? WHERE id = ?", (now, inquiry_id))

    conn.commit()
    conn.close()
    return {"status": "ok", "time": now}
