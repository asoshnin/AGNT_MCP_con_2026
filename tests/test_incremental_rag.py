"""Unit tests for hub_incremental.py ensuring sub-2s incremental upsert into FTS5 & FastEmbed."""

import sqlite3
import time

from hub_incremental import incremental_upsert


def test_incremental_rag_hub_sqlite(tmp_path):
    # Setup test DB matching hub.sqlite schema from spec
    db_file = str(tmp_path / "test_hub.sqlite")
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, title TEXT, speaker TEXT, company TEXT, has_slides INTEGER DEFAULT 0);")
    conn.execute("CREATE VIRTUAL TABLE sessions_fts USING fts5(id, title, speaker, company, summary, content);")
    conn.execute("INSERT INTO sessions (id, title, speaker, company, has_slides) VALUES ('2RB8M', 'Test Title', 'Speaker Name', 'Acme Inc', 0);")
    conn.commit()
    conn.close()

    start_time = time.time()
    res = incremental_upsert(
        session_id="2RB8M",
        slides_text="Extracted text from community slide submission about agent orchestration.",
        summary="Executive summary of the session deck.",
        custom_db_path=db_file,
    )
    elapsed = time.time() - start_time

    assert res["status"] == "ok"
    assert res["updated_records"] > 0
    # Must execute in under 2.0 seconds
    assert elapsed < 2.0

    # Verify FTS5 query
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT has_slides FROM sessions WHERE id = '2RB8M'")
    assert cur.fetchone()[0] == 1

    cur.execute("SELECT id, title, content FROM sessions_fts WHERE sessions_fts MATCH 'orchestration'")
    matched = cur.fetchall()
    assert len(matched) == 1
    assert matched[0][0] == "2RB8M"
    conn.close()


def test_incremental_rag_agntcon_schema(tmp_path):
    # Setup test DB matching agntcon2026.sqlite schema
    db_file = str(tmp_path / "test_agntcon.sqlite")
    conn = sqlite3.connect(db_file)
    conn.execute("""
    CREATE TABLE talks (
        id TEXT PRIMARY KEY,
        title TEXT,
        speakers TEXT,
        sched_url TEXT,
        relevance_score REAL,
        concepts TEXT,
        one_paragraph TEXT,
        content TEXT
    );
    """)
    conn.execute("""
    CREATE VIRTUAL TABLE talks_fts USING fts5(
        id UNINDEXED,
        title,
        speakers,
        concepts,
        one_paragraph,
        content,
        content='talks',
        content_rowid='rowid'
    );
    """)
    conn.execute("""
    CREATE TABLE talk_embeddings (
        talk_id TEXT PRIMARY KEY,
        model TEXT NOT NULL,
        dimension INTEGER NOT NULL,
        vector BLOB NOT NULL
    );
    """)
    conn.execute("""
    INSERT INTO talks (id, title, speakers, sched_url, relevance_score, concepts, one_paragraph, content)
    VALUES ('ABC12', 'Building Autonomous Agents', 'Jane Doe', 'https://sched.com/1', 9.5, 'agents, llm', 'Initial summary', 'Initial talk notes');
    """)
    conn.commit()
    conn.close()

    start = time.time()
    res = incremental_upsert(
        session_id="ABC12",
        slides_text="New slides covering multi-agent routing and tool use.",
        summary="Updated executive summary.",
        custom_db_path=db_file,
    )
    duration = time.time() - start

    assert res["status"] == "ok"
    assert duration < 2.0

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT one_paragraph, content FROM talks WHERE id = 'ABC12'")
    row = cur.fetchone()
    assert row[0] == "Updated executive summary."
    assert "multi-agent routing" in row[1]
    conn.close()
