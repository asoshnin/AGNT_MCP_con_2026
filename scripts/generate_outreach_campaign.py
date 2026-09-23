#!/usr/bin/env python3
"""Multi-Cohort Outreach Campaign Generator for AGNTCon & MCPCon Europe 2026.

Reads data/contacts.json and data/outreach_private.sqlite to generate personalized,
privacy-preserving message drafts and public social media announcement copy.

Standardized Cohort Keys:
1. cohort_organizers: European Community Hub as a gift & North America pilot proposal
2. cohort_missing_slides: 1-click HMAC magic link to upload slides in 10s
3. cohort_slides_available: Live session deep-link, LinkedIn repost & GitHub star ask
4. public_launch_post: Zero-link post body + link in first comment (Anti-suppression)

Outputs organized drafts into out/campaigns/ (strictly gitignored).
"""

import argparse
import datetime
import json
import logging
import os
import re
import sys
from pathlib import Path

HUB_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONTACTS = HUB_DIR / "data" / "contacts.json"
DEFAULT_DB = HUB_DIR / "data" / "outreach_private.sqlite"
DEFAULT_OUT_DIR = HUB_DIR / "out" / "campaigns"
DEFAULT_BASE_URL = "https://agntcon-demo.vwoosh.com"
DEFAULT_GITHUB = "github.com/asoshnin/AGNT_MCP_con_2026"

sys.path.insert(0, str(HUB_DIR))
try:
    import outreach_db
except ImportError:
    outreach_db = None

try:
    from scripts.generate_speaker_tokens import generate_token
except ImportError:
    from generate_speaker_tokens import generate_token

logger = logging.getLogger("outreach_campaign")


def get_first_name(full_name: str) -> str:
    """Extracts first name or friendly greeting token."""
    if not full_name:
        return "there"
    # Clean titles like Dr., Prof.
    cleaned = re.sub(r"^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+", "", full_name.strip(), flags=re.I)
    parts = cleaned.split()
    return parts[0] if parts else "there"


def render_organizer_template(
    first_name: str,
    base_url: str = DEFAULT_BASE_URL,
    github_repo: str = DEFAULT_GITHUB,
) -> tuple[str, str]:
    subject = "Community Knowledge Hub for AGNTCon EU (and a pilot idea for North America)"
    body = f"""Subject: {subject}

Hi {first_name},

Congratulations on a phenomenal AGNTCon + MCPCon Europe 2026! 

To help preserve the incredible talks from the event, I built an open-source Community Knowledge Hub: {base_url}

It provides instant full-text FTS5 search, local FastEmbed semantic RAG, and in-browser slide viewing across all 113 sessions.

We've already indexed 80+ presentations. For the remaining talks, we built a concierge batch-ingestion tool that can securely ingest a folder or archive in 60 seconds with zero manual overhead.

With AGNTCon North America on the horizon, I'd love to share our learnings and explore offering this as a turnkey, co-branded Community Knowledge Hub for the NA edition to give attendees instant search across all tracks.

Would you be open to a quick 5-minute chat or exchanging a few thoughts here?

Best regards,
Alexey Soshnin
GitHub: {github_repo}"""
    return subject, body


def render_missing_slides_template(
    first_name: str,
    session_title: str,
    magic_url: str,
    base_url: str = DEFAULT_BASE_URL,
) -> str:
    return f"""Hi {first_name},

Loved your session on "{session_title}" at AGNTCon Europe!

Attendees exploring our open-source AGNTCon Knowledge Hub ({base_url}) have been asking for your presentation materials.

I set up a 1-click upload link so you can attach your PDF slides or outline in 10 seconds — no passwords or login required:
👉 {magic_url}

You can also review the AI-generated summary of your talk on the page and submit any corrections.

Hope this helps give your talk even more reach in the developer community!

Best,
Alexey Soshnin"""


def render_slides_available_template(
    first_name: str,
    session_title: str,
    session_id: str,
    base_url: str = DEFAULT_BASE_URL,
    github_repo: str = DEFAULT_GITHUB,
    linkedin_post_url: str = "[Link to LinkedIn Post]",
) -> str:
    session_url = f"{base_url.rstrip('/')}/#session-{session_id}"
    return f"""Hi {first_name},

Just wanted to let you know that we've featured your session "{session_title}" on the AGNTCon 2026 Community Knowledge Hub!

Attendees can now read your slides side-by-side with full-text search and semantic Q&A:
👉 {session_url}

We also gave your session a shout-out in our community launch post on LinkedIn: {linkedin_post_url}

If you like how your talk is presented, a quick repost or a ⭐ on GitHub ({github_repo}) would mean the world to the project!

Best,
Alexey Soshnin"""


def render_public_launch_post(
    base_url: str = DEFAULT_BASE_URL,
    github_repo: str = DEFAULT_GITHUB,
) -> dict:
    post_body = """🚀 AGNTCon + MCPCon Europe 2026 is over, but the knowledge shouldn't stay scattered across slide decks.

Earlier this week, I shared an initial prototype for exploring the conference schedule. The response from developers was clear: they wanted deep search, instant access to slides, and AI-powered talk exploration.

Today, we're launching V2: The Open-Source AGNTCon Community Knowledge Hub! 🌐

What's new:
✨ Side-by-side in-browser slide preview for 80+ keynotes & sessions
🔍 Sub-second hybrid search (SQLite FTS5 full-text + local FastEmbed semantic vectors)
📑 1-Click concierge slide upload for speakers
💬 Author feedback system to refine AI-generated talk summaries
🛡️ 100% Zero-cost & privacy-preserving stack

If you spoke at AGNTCon, your talk is likely already indexed! Check out your session page and let us know what you think.

🔗 Live Hub demo & open-source GitHub repo in the first comment! 👇

#AI #AgenticAI #ModelContextProtocol #MCP #OpenSource #AGNTCon2026"""

    clean_repo = github_repo.removeprefix("https://").removeprefix("http://")
    first_comment = f"""🔗 Live Demo Hub: {base_url}
⭐ Open-Source GitHub Repository: https://{clean_repo}

If you have slides or updates for unindexed talks, use the 1-click contribute tool on the site!"""

    return {
        "post_body": post_body,
        "first_comment": first_comment,
    }


def generate_campaign(
    contacts_path: Path | str = DEFAULT_CONTACTS,
    db_path: Path | str = DEFAULT_DB,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    base_url: str = DEFAULT_BASE_URL,
    github_repo: str = DEFAULT_GITHUB,
) -> dict:
    contacts_path = Path(contacts_path)
    db_path = Path(db_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not contacts_path.exists():
        return {
            "status": "error",
            "error": f"Contacts file {contacts_path} does not exist. Run extract_contacts.py first.",
        }

    with open(contacts_path, encoding="utf-8") as f:
        contacts_data = json.load(f)

    # Initialize private DB and fetch opt-outs
    conn = None
    opt_outs: set[str] = set()
    if outreach_db:
        conn = outreach_db.init_outreach_db(db_path)
        opt_outs = outreach_db.get_opt_out_identifiers(conn)

    speakers = contacts_data.get("speakers", [])
    organizers = contacts_data.get("organizers", [])

    campaign_organizers = []
    campaign_missing_slides = []
    campaign_slides_available = []
    suppressed_count = 0

    # 1. Generate for cohort_organizers
    for org in organizers:
        name = org.get("name", "")
        ln_url = org.get("linkedin_url")
        tw_url = org.get("twitter_url")

        # Opt-out check
        if name.lower() in opt_outs or (ln_url and ln_url.lower() in opt_outs) or (tw_url and tw_url.lower() in opt_outs):
            suppressed_count += 1
            continue

        first_name = get_first_name(name)
        subject, body = render_organizer_template(first_name, base_url, github_repo)
        target = ln_url or tw_url or org.get("company", "")
        channel = "linkedin" if ln_url else ("twitter" if tw_url else "email")
        msg_id = f"msg_org_{org.get('id', name)}"

        rec = {
            "id": msg_id,
            "recipient_name": name,
            "role": org.get("role", ""),
            "company": org.get("company", ""),
            "channel": channel,
            "target": target,
            "subject": subject,
            "message": body,
            "cohort": "cohort_organizers",
        }
        campaign_organizers.append(rec)

        if conn and outreach_db:
            outreach_db.store_message(
                conn=conn,
                msg_id=msg_id,
                recipient_name=name,
                cohort="cohort_organizers",
                channel=channel,
                target_handle=target,
                message_text=body,
                status="draft",
            )

    # 2. Generate for Speakers (cohort_missing_slides & cohort_slides_available)
    for spk in speakers:
        name = spk.get("name", "")
        cohort = spk.get("cohort", "cohort_missing_slides")
        ln_url = spk.get("linkedin_url")
        tw_url = spk.get("twitter_url")

        if name.lower() in opt_outs or (ln_url and ln_url.lower() in opt_outs) or (tw_url and tw_url.lower() in opt_outs):
            suppressed_count += 1
            continue

        first_name = get_first_name(name)
        sessions = spk.get("sessions", [])
        primary_session = sessions[0] if sessions else {"session_id": "session", "title": "your talk"}
        sid = primary_session.get("session_id", "talk")
        title = primary_session.get("title", "your talk")

        target = ln_url or tw_url
        channel = "linkedin" if ln_url else ("twitter" if tw_url else "social")

        if cohort == "cohort_missing_slides":
            # Lookup or create magic link
            magic_url = ""
            if conn and outreach_db:
                tok_data = outreach_db.get_token(conn, sid)
                if tok_data:
                    magic_url = tok_data["magic_url"]
            if not magic_url:
                token = generate_token(sid)
                magic_url = f"{base_url.rstrip('/')}/contribute?token={token}"

            body = render_missing_slides_template(first_name, title, magic_url, base_url)
            msg_id = f"msg_missing_{spk.get('id', name)}_{sid}"
            rec = {
                "id": msg_id,
                "recipient_name": name,
                "session_id": sid,
                "session_title": title,
                "channel": channel,
                "target": target,
                "magic_url": magic_url,
                "message": body,
                "cohort": "cohort_missing_slides",
            }
            campaign_missing_slides.append(rec)

            if conn and outreach_db:
                outreach_db.store_message(
                    conn=conn,
                    msg_id=msg_id,
                    recipient_name=name,
                    cohort="cohort_missing_slides",
                    channel=channel,
                    target_handle=target,
                    message_text=body,
                    status="draft",
                )

        elif cohort == "cohort_slides_available":
            body = render_slides_available_template(first_name, title, sid, base_url, github_repo)
            msg_id = f"msg_available_{spk.get('id', name)}_{sid}"
            rec = {
                "id": msg_id,
                "recipient_name": name,
                "session_id": sid,
                "session_title": title,
                "channel": channel,
                "target": target,
                "session_url": f"{base_url.rstrip('/')}/#session-{sid}",
                "message": body,
                "cohort": "cohort_slides_available",
            }
            campaign_slides_available.append(rec)

            if conn and outreach_db:
                outreach_db.store_message(
                    conn=conn,
                    msg_id=msg_id,
                    recipient_name=name,
                    cohort="cohort_slides_available",
                    channel=channel,
                    target_handle=target,
                    message_text=body,
                    status="draft",
                )

    # 3. Public Launch Post
    public_post = render_public_launch_post(base_url, github_repo)

    # 4. Save campaign files into out/campaigns/
    # JSON files
    with open(out_dir / "cohort_organizers.json", "w", encoding="utf-8") as f:
        json.dump(campaign_organizers, f, indent=2, ensure_ascii=False)
    with open(out_dir / "cohort_missing_slides.json", "w", encoding="utf-8") as f:
        json.dump(campaign_missing_slides, f, indent=2, ensure_ascii=False)
    with open(out_dir / "cohort_slides_available.json", "w", encoding="utf-8") as f:
        json.dump(campaign_slides_available, f, indent=2, ensure_ascii=False)
    with open(out_dir / "public_launch_post.json", "w", encoding="utf-8") as f:
        json.dump(public_post, f, indent=2, ensure_ascii=False)

    # Formatted Markdown for easy human review
    with open(out_dir / "public_launch_post.md", "w", encoding="utf-8") as f:
        f.write("# Public Launch Announcement Copy (LinkedIn & Twitter/X)\n\n")
        f.write("## 📝 Main Post Body (Zero Links - Anti-Suppression Invariant)\n\n```\n")
        f.write(public_post["post_body"])
        f.write("\n```\n\n## 💬 First Comment (Place Outbound Links Here)\n\n```\n")
        f.write(public_post["first_comment"])
        f.write("\n```\n")

    with open(out_dir / "cohort_organizers.md", "w", encoding="utf-8") as f:
        f.write(f"# Cohort: Organizers & Program Committee ({len(campaign_organizers)} targets)\n\n")
        for c in campaign_organizers:
            f.write(f"### {c['recipient_name']} ({c['company']}) - {c['channel']}: {c['target']}\n\n")
            f.write("```\n" + c["message"] + "\n```\n\n---\n\n")

    with open(out_dir / "cohort_missing_slides.md", "w", encoding="utf-8") as f:
        f.write(f"# Cohort: Presenters WITHOUT Slides ({len(campaign_missing_slides)} targets)\n\n")
        for c in campaign_missing_slides:
            f.write(f"### {c['recipient_name']} - Session: {c['session_title']} ({c['session_id']})\n\n")
            f.write("```\n" + c["message"] + "\n```\n\n---\n\n")

    with open(out_dir / "cohort_slides_available.md", "w", encoding="utf-8") as f:
        f.write(f"# Cohort: Presenters WITH Slides ({len(campaign_slides_available)} targets)\n\n")
        for c in campaign_slides_available:
            f.write(f"### {c['recipient_name']} - Session: {c['session_title']} ({c['session_id']})\n\n")
            f.write("```\n" + c["message"] + "\n```\n\n---\n\n")

    summary = {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "counts": {
            "cohort_organizers": len(campaign_organizers),
            "cohort_missing_slides": len(campaign_missing_slides),
            "cohort_slides_available": len(campaign_slides_available),
            "public_launch_post": 1,
            "suppressed_due_to_opt_out": suppressed_count,
        },
        "output_directory": str(out_dir),
    }

    with open(out_dir / "campaign_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    if conn:
        conn.close()

    return summary


def main():
    parser = argparse.ArgumentParser(description="Generate Multi-Cohort Outreach Campaigns")
    parser.add_argument("--hub-dir", default=str(HUB_DIR), help="Path to 02_public_hub root directory")
    parser.add_argument("--contacts", default=str(DEFAULT_CONTACTS), help="Path to contacts.json")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to outreach_private.sqlite")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Path to output campaigns directory")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of Community Hub")
    args = parser.parse_args()

    res = generate_campaign(
        contacts_path=args.contacts,
        db_path=args.db,
        out_dir=args.out_dir,
        base_url=args.base_url,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
