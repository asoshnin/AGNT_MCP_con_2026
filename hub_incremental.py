"""Incremental RAG Indexing Engine for AGNTCon Knowledge Hub.
Updates FTS5 index and FastEmbed embeddings in < 2 seconds without server restarts.
Enforces WAL mode with busy_timeout=5000.
"""

import json
import os
import sqlite3
import struct
import sys
import time

_EMBED_MODEL = None


def get_embed_model():
    """Lazy singleton for FastEmbed model to prevent repeated disk loads."""
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        try:
            from fastembed import TextEmbedding
            _EMBED_MODEL = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except Exception as e:
            sys.stderr.write(f"[WARN] FastEmbed initialization skipped/failed: {e}\n")
            _EMBED_MODEL = False
    return _EMBED_MODEL if _EMBED_MODEL is not False else None


def incremental_upsert(
    session_id: str,
    slides_text: str,
    summary: str = "",
    hub_dir: str | None = None,
    custom_db_path: str | None = None,
) -> dict:
    """Incrementally updates FTS5 and vector embeddings for session_id.
    Executes in < 2 seconds.
    """
    start_time = time.time()
    base_hub_dir = hub_dir or os.path.dirname(os.path.abspath(__file__))
    
    # 1. Resolve DB path
    target_dbs = []
    if custom_db_path:
        target_dbs.append(custom_db_path)
    else:
        # Canonical location wiki/agntcon2026.sqlite, and site/data copy if present
        primary_db = os.path.join(base_hub_dir, "wiki", "agntcon2026.sqlite")
        site_db = os.path.join(base_hub_dir, "site", "data", "agntcon2026.sqlite")
        hub_db = os.path.join(base_hub_dir, "data", "hub.sqlite")

        if os.path.exists(primary_db):
            target_dbs.append(primary_db)
        if os.path.exists(site_db):
            target_dbs.append(site_db)
        if os.path.exists(hub_db) and hub_db not in target_dbs:
            target_dbs.append(hub_db)

    # Also support single-table hub.sqlite if created by tests
    updated_records = 0
    vector_embedded = False

    for db_path in target_dbs:
        if not os.path.exists(db_path):
            continue
        try:
            with sqlite3.connect(db_path, timeout=10.0) as conn:
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA busy_timeout = 5000;")
                cur = conn.cursor()

                # Check if talks table exists
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='talks'")
                if cur.fetchone():
                    # Fetch talk metadata
                    cur.execute("SELECT title, speakers, sched_url, relevance_score, concepts, one_paragraph, content FROM talks WHERE id = ?", (session_id,))
                    row = cur.fetchone()
                    if row:
                        title, speakers, _sched_url, _rel_score, concepts, one_par, old_content = row
                        combined_content = (old_content or "") + "\n\n=== SLIDES CONTENT ===\n" + (slides_text or "")
                        updated_one_par = summary if summary else one_par

                        cur.execute(
                            "UPDATE talks SET one_paragraph = ?, content = ? WHERE id = ?",
                            (updated_one_par, combined_content, session_id),
                        )
                        # FTS5 index update: talks_fts is an external content table on talks
                        # We re-index the session
                        try:
                            cur.execute("INSERT INTO talks_fts(talks_fts, rowid, id, title, speakers, concepts, one_paragraph, content) VALUES('delete', (SELECT rowid FROM talks WHERE id = ?), ?, ?, ?, ?, ?, ?)",
                                        (session_id, session_id, title, speakers, concepts, one_par, old_content))
                        except Exception:
                            pass
                        try:
                            cur.execute("INSERT INTO talks_fts(rowid, id, title, speakers, concepts, one_paragraph, content) SELECT rowid, id, title, speakers, concepts, one_paragraph, content FROM talks WHERE id = ?",
                                        (session_id,))
                        except Exception:
                            pass
                        updated_records += 1

                # Check if generic sessions table exists (e.g. hub.sqlite schema)
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
                if cur.fetchone():
                    cur.execute("UPDATE sessions SET has_slides = 1 WHERE id = ?", (session_id,))
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions_fts'")
                    if cur.fetchone():
                        cur.execute("DELETE FROM sessions_fts WHERE id = ?", (session_id,))
                        meta = cur.execute("SELECT title, speaker, company FROM sessions WHERE id = ?", (session_id,)).fetchone()
                        if meta:
                            title, speaker, company = meta
                            cur.execute(
                                "INSERT INTO sessions_fts (id, title, speaker, company, summary, content) VALUES (?, ?, ?, ?, ?, ?)",
                                (session_id, title, speaker, company, summary, slides_text),
                            )
                        updated_records += 1

                # 2. FastEmbed vector embedding update
                model = get_embed_model()
                if model and (slides_text or summary):
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='talk_embeddings'")
                    if cur.fetchone():
                        # Generate embedding for the new content + summary
                        embed_text = f"{summary}\n{slides_text[:2000]}"
                        try:
                            emb = next(iter(model.embed([embed_text])))
                            dim = len(emb)
                            blob = struct.pack(f"{dim}f", *emb)
                            cur.execute(
                                "INSERT OR REPLACE INTO talk_embeddings (talk_id, model, dimension, vector) VALUES (?, ?, ?, ?)",
                                (session_id, "bge-small-en-v1.5", dim, blob),
                            )
                            vector_embedded = True
                        except Exception as e:
                            sys.stderr.write(f"[WARN] Embedding generation failed: {e}\n")

                conn.commit()
        except Exception as e:
            sys.stderr.write(f"[WARN] Incremental upsert error on {db_path}: {e}\n")

    # 3. Update index.json catalog if it exists
    index_json_path = os.path.join(base_hub_dir, "wiki", "index.json")
    if os.path.exists(index_json_path):
        try:
            with open(index_json_path, encoding="utf-8") as f:
                catalog = json.load(f)
            modified = False
            for item in catalog:
                if item.get("id") == session_id:
                    item["has_slides"] = True
                    item["slide_source"] = "community"
                    item["slide_url"] = f"/assets/slides/{session_id}.pdf"
                    if summary:
                        item["one_paragraph"] = summary
                    modified = True
                    break
            if modified:
                with open(index_json_path, "w", encoding="utf-8") as f:
                    json.dump(catalog, f, indent=2, ensure_ascii=False)
        except Exception as e:
            sys.stderr.write(f"[WARN] Failed to update wiki/index.json: {e}\n")

    elapsed = time.time() - start_time
    return {
        "status": "ok",
        "session_id": session_id,
        "updated_records": updated_records,
        "vector_embedded": vector_embedded,
        "elapsed_seconds": round(elapsed, 4),
    }
