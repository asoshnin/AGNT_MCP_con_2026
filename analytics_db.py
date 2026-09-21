"""Zero-PII Engagement Analytics and Aggregation for AGNTCon Knowledge Hub.
Enforces SQLite WAL mode, busy timeout, allowlisted events, and parameterized queries.
"""

import json
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "analytics.sqlite")
TALKS_DB_PATH = os.path.join(os.path.dirname(__file__), "wiki", "agntcon2026.sqlite")

ALLOWED_EVENTS: set[str] = {
    "page_view",
    "search",
    "talk_opened",
    "track_curate",
    "track_export_obsidian",
    "track_export_pdf",
    "chat_query",
}

_TALK_TITLE_CACHE: dict[str, str] = {}


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    target_path = db_path or os.environ.get("ANALYTICS_DB_PATH", DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def init_analytics_db(db_path: str | None = None) -> None:
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        session_hash TEXT NOT NULL,
        event_type TEXT NOT NULL,
        country TEXT NOT NULL DEFAULT 'XX',
        referrer TEXT NOT NULL DEFAULT 'direct',
        metadata TEXT
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_country ON events(country);")
    conn.commit()
    conn.close()


def _resolve_talk_title(talk_id: str) -> str:
    if not talk_id:
        return "Unknown Talk"
    if talk_id in _TALK_TITLE_CACHE:
        return _TALK_TITLE_CACHE[talk_id]

    title = talk_id
    if os.path.exists(TALKS_DB_PATH):
        try:
            conn = sqlite3.connect(f"file:{os.path.abspath(TALKS_DB_PATH)}?mode=ro", uri=True)
            cur = conn.cursor()
            cur.execute("SELECT title FROM talks WHERE id = ? LIMIT 1;", (talk_id,))
            row = cur.fetchone()
            if row and row[0]:
                title = row[0]
            conn.close()
        except Exception:
            pass

    _TALK_TITLE_CACHE[talk_id] = title
    return title


def record_event(
    session_hash: str,
    event_type: str,
    country: str = "XX",
    referrer: str = "direct",
    metadata: Any | None = None,
    timestamp: str | None = None,
    db_path: str | None = None,
) -> int:
    """Record an allowlisted interaction event into the analytics store."""
    if event_type not in ALLOWED_EVENTS:
        raise ValueError(f"Invalid event type: {event_type}. Allowed: {sorted(ALLOWED_EVENTS)}")

    init_analytics_db(db_path)

    # Sanitize inputs
    clean_hash = (session_hash or "anonymous")[:64]
    clean_country = (country or "XX").strip().upper()
    if len(clean_country) != 2 or not clean_country.isalpha():
        clean_country = "XX"

    clean_referrer = (referrer or "direct").strip()[:255]

    meta_str = None
    if metadata is not None:
        if isinstance(metadata, (dict, list)):
            meta_str = json.dumps(metadata, ensure_ascii=False)
        else:
            meta_str = str(metadata)[:1024]

    now_ts = timestamp or datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events (timestamp, session_hash, event_type, country, referrer, metadata)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (now_ts, clean_hash, event_type, clean_country, clean_referrer, meta_str),
    )
    event_id = cur.lastrowid or 0
    conn.commit()
    conn.close()
    return event_id


def get_analytics_summary(db_path: str | None = None) -> dict[str, Any]:
    """Aggregate engagement analytics for the operator dashboard."""
    init_analytics_db(db_path)
    conn = get_db(db_path)
    cur = conn.cursor()

    cutoff_24h = (datetime.now(UTC) - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

    # 1. KPIs
    cur.execute("SELECT COUNT(DISTINCT session_hash) FROM events WHERE timestamp >= ?;", (cutoff_24h,))
    uv_24h = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(DISTINCT session_hash) FROM events;")
    uv_all = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM events;")
    total_events = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM events WHERE event_type != 'page_view';")
    engaged_actions = cur.fetchone()[0] or 0

    # Type counts
    cur.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type;")
    type_counts = {row[0]: row[1] for row in cur.fetchall()}

    visits_count = type_counts.get("page_view", 0)
    searches_count = type_counts.get("search", 0)
    talk_views_count = type_counts.get("talk_opened", 0)
    curate_count = type_counts.get("track_curate", 0)
    obsidian_exports = type_counts.get("track_export_obsidian", 0)
    pdf_exports = type_counts.get("track_export_pdf", 0)
    total_exports = obsidian_exports + pdf_exports
    chat_queries_count = type_counts.get("chat_query", 0)

    # 2. Conversion Funnel
    base_funnel = max(visits_count, 1) if visits_count > 0 else 1
    funnel = [
        {
            "stage": "Visits",
            "count": visits_count,
            "percent": 100.0 if visits_count > 0 else 0.0,
        },
        {
            "stage": "Searches",
            "count": searches_count,
            "percent": round((searches_count / base_funnel) * 100, 1) if visits_count > 0 else 0.0,
        },
        {
            "stage": "Talk Views",
            "count": talk_views_count,
            "percent": round((talk_views_count / base_funnel) * 100, 1) if visits_count > 0 else 0.0,
        },
        {
            "stage": "AI Chat",
            "count": chat_queries_count,
            "percent": round((chat_queries_count / base_funnel) * 100, 1) if visits_count > 0 else 0.0,
        },
        {
            "stage": "Exports",
            "count": total_exports,
            "percent": round((total_exports / base_funnel) * 100, 1) if visits_count > 0 else 0.0,
        },
    ]

    # 3. Geo Distribution (Top 10)
    cur.execute(
        """
        SELECT country, COUNT(DISTINCT session_hash) AS visitors, COUNT(*) AS total_count
        FROM events
        GROUP BY country
        ORDER BY visitors DESC, total_count DESC
        LIMIT 10;
        """
    )
    geo_rows = cur.fetchall()
    total_geo_visitors = sum(r["visitors"] for r in geo_rows) or 1
    geo_distribution = [
        {
            "country": r["country"],
            "visitors": r["visitors"],
            "events": r["total_count"],
            "percent": round((r["visitors"] / total_geo_visitors) * 100, 1),
        }
        for r in geo_rows
    ]

    # 4. Top Clicked Talks
    top_talks: list[dict[str, Any]] = []
    try:
        cur.execute(
            """
            SELECT json_extract(metadata, '$.talk_id') AS tid,
                   COALESCE(json_extract(metadata, '$.title'), '') AS meta_title,
                   COUNT(*) AS cnt
            FROM events
            WHERE event_type = 'talk_opened' AND metadata IS NOT NULL AND json_extract(metadata, '$.talk_id') IS NOT NULL
            GROUP BY tid
            ORDER BY cnt DESC
            LIMIT 5;
            """
        )
        for r in cur.fetchall():
            tid = str(r["tid"])
            raw_meta_title = str(r["meta_title"]).strip()
            title = raw_meta_title if raw_meta_title else _resolve_talk_title(tid)
            top_talks.append({"talk_id": tid, "title": title, "count": r["cnt"]})
    except Exception:
        # Fallback if json_extract failed
        cur.execute("SELECT metadata FROM events WHERE event_type = 'talk_opened' AND metadata IS NOT NULL;")
        talk_freq: dict[str, int] = {}
        talk_titles: dict[str, str] = {}
        for r in cur.fetchall():
            try:
                m = json.loads(r[0])
                tid = m.get("talk_id")
                if tid:
                    talk_freq[tid] = talk_freq.get(tid, 0) + 1
                    if m.get("title"):
                        talk_titles[tid] = m["title"]
            except Exception:
                continue
        for tid, cnt in sorted(talk_freq.items(), key=lambda x: x[1], reverse=True)[:5]:
            title = talk_titles.get(tid) or _resolve_talk_title(tid)
            top_talks.append({"talk_id": tid, "title": title, "count": cnt})

    # 5. Top Search Queries
    top_searches: list[dict[str, Any]] = []
    try:
        cur.execute(
            """
            SELECT LOWER(TRIM(json_extract(metadata, '$.query'))) AS q, COUNT(*) AS cnt
            FROM events
            WHERE event_type = 'search' AND metadata IS NOT NULL AND json_extract(metadata, '$.query') IS NOT NULL
            GROUP BY q
            HAVING q != ''
            ORDER BY cnt DESC
            LIMIT 5;
            """
        )
        for r in cur.fetchall():
            top_searches.append({"query": r["q"], "count": r["cnt"]})
    except Exception:
        cur.execute("SELECT metadata FROM events WHERE event_type = 'search' AND metadata IS NOT NULL;")
        q_freq: dict[str, int] = {}
        for r in cur.fetchall():
            try:
                m = json.loads(r[0])
                q = str(m.get("query", "")).strip().lower()
                if q:
                    q_freq[q] = q_freq.get(q, 0) + 1
            except Exception:
                continue
        for q, cnt in sorted(q_freq.items(), key=lambda x: x[1], reverse=True)[:5]:
            top_searches.append({"query": q, "count": cnt})

    # 6. Hourly Activity (Last 24 Hours)
    # Generate 24 hourly buckets: current hour down to 23 hours ago
    now_utc = datetime.now(UTC)
    hour_buckets: dict[str, int] = {}
    for i in range(23, -1, -1):
        dt = now_utc - timedelta(hours=i)
        hour_buckets[dt.strftime("%Y-%m-%d %H:00")] = 0

    cur.execute(
        """
        SELECT strftime('%Y-%m-%d %H:00', timestamp) AS hr, COUNT(*) AS cnt
        FROM events
        WHERE timestamp >= ?
        GROUP BY hr;
        """,
        (cutoff_24h,),
    )
    for r in cur.fetchall():
        hr = r["hr"]
        if hr in hour_buckets:
            hour_buckets[hr] = r["cnt"]

    hourly_activity = [
        {
            "hour": hr.split(" ")[1],  # "HH:00"
            "date_hour": hr,
            "count": cnt,
        }
        for hr, cnt in hour_buckets.items()
    ]

    conn.close()

    return {
        "kpis": {
            "unique_visitors_24h": uv_24h,
            "unique_visitors_all": uv_all,
            "total_events": total_events,
            "engaged_actions": engaged_actions,
            "exports_count": total_exports,
            "chat_queries_count": chat_queries_count,
            "talk_views_count": talk_views_count,
            "searches_count": searches_count,
            "curate_count": curate_count,
        },
        "conversion_funnel": funnel,
        "geo_distribution": geo_distribution,
        "top_talks": top_talks,
        "top_searches": top_searches,
        "hourly_activity": hourly_activity,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def reset_analytics_events(db_path: str | None = None) -> int:
    """Safely purge all records in the events table and reset sqlite_sequence, returning deleted count."""
    init_analytics_db(db_path)
    conn = get_db(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM events;")
    count = cur.fetchone()[0] or 0
    cur.execute("DELETE FROM events;")
    try:
        cur.execute("DELETE FROM sqlite_sequence WHERE name = 'events';")
    except sqlite3.OperationalError:
        # sqlite_sequence might not exist if autoincrement table has had no inserts
        pass
    conn.commit()
    conn.close()
    return int(count)
