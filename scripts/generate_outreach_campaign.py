#!/usr/bin/env python3
"""Multi-Cohort Outreach Campaign Generator for AGNTCon & MCPCon Europe 2026.

Reads data/contacts.json and data/outreach_private.sqlite to generate personalized,
privacy-preserving message drafts and public social media announcement copy.

Standardized Cohort Keys & Templates (Proposal 30.11 / Sprint 19 Hardening):
1. Template C (cohort_organizers): European Community Hub as a gift & North America pilot proposal (<= 280 chars)
2. Template B (cohort_missing_slides): Compact 1-click magic link agntcon-demo.vwoosh.com/c?t={token} (<= 280 chars)
3. Template A (cohort_slides_available): Live session deep-link, honest toy demo disclosure, GitHub star ask (<= 280 chars)
4. Template D (cohort_external_organizers): Open-source peer exchange for other tech conference organizers (<= 280 chars)
5. Public Launch Post: Zero-link post body + link in first comment (Anti-suppression)

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


def clean_domain(url: str) -> str:
    """Strips protocol and trailing slashes to produce a compact domain string."""
    if not url:
        return "agntcon-demo.vwoosh.com"
    u = url.strip()
    u = re.sub(r"^https?://", "", u, flags=re.I)
    return u.rstrip("/")


def format_short_title(title: str, max_chars: int = 25) -> str:
    """Format talk or conference title to strictly stay within max_chars bound."""
    if not title:
        return ""
    cleaned = title.strip().replace('"', "'")
    if len(cleaned) <= max_chars:
        return cleaned
    if max_chars <= 3:
        return cleaned[:max_chars]
    return cleaned[: max_chars - 3] + "..."


def clamp_note_length(note: str, max_chars: int = 280) -> str:
    """Mathematically guarantees the note never exceeds max_chars bound."""
    if len(note) <= max_chars:
        return note
    signoff = " Apologies if misdirected!"
    if len(signoff) >= max_chars:
        return note[:max_chars]
    available = max_chars - len(signoff)
    return note[:available].rstrip() + signoff


def get_first_name(full_name: str) -> str:
    """Extracts first name or friendly greeting token."""
    if not full_name:
        return "there"
    cleaned = re.sub(r"^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+", "", full_name.strip(), flags=re.I)
    parts = cleaned.split()
    first = parts[0] if parts else "there"
    return first[:15] if len(first) > 15 else first


def is_suspect_contact(contact: dict) -> bool:
    """Checks if a contact has been flagged as suspect by the verification engine."""
    if contact.get("verification_status") == "suspect":
        return True
    verif = contact.get("verification")
    if isinstance(verif, dict) and verif.get("status") == "suspect":
        return True
    return False


def render_organizer_template(
    first_name: str,
    base_url: str = DEFAULT_BASE_URL,
    github_repo: str = DEFAULT_GITHUB,
) -> tuple[str, str]:
    """Template C: AGNTCon Organizers (<= 280 chars, honest toy demo disclosure)."""
    domain = clean_domain(base_url)
    subject = "Community Knowledge Hub for AGNTCon EU (and a pilot idea for North America)"
    body = (
        f"Hi {first_name}, congrats on AGNTCon EU! I built an open-source toy demo ({domain}) "
        f"indexing 80+ talks on free LLMs. Would love to share learnings or explore a community hub "
        f"for AGNTCon NA if useful. Open to a chat? Apologies if misdirected!"
    )
    return subject, clamp_note_length(body, 280)


def render_missing_slides_template(
    first_name: str,
    session_title: str,
    token: str,
    base_url: str = DEFAULT_BASE_URL,
) -> str:
    """Template B: Presenters WITHOUT Slides (<= 280 chars, compact link, honest demo disclosure)."""
    domain = clean_domain(base_url)
    short_title = format_short_title(session_title, 25)

    # If full URL was passed instead of token, extract token
    raw_token = token
    if "token=" in raw_token:
        raw_token = raw_token.split("token=")[1].split("&")[0]
    elif "t=" in raw_token:
        raw_token = raw_token.split("t=")[1].split("&")[0]

    compact_url = f"{domain}/c?t={raw_token}"
    note = (
        f'Hi {first_name}! AGNTCon attendees want your slides for "{short_title}". '
        f'10s 1-click upload: {compact_url} (free toy demo on free LLMs). '
        f'Apologies if misdirected!'
    )
    return clamp_note_length(note, 280)


def render_slides_available_template(
    first_name: str,
    session_title: str,
    session_id: str,
    base_url: str = DEFAULT_BASE_URL,
    github_repo: str = DEFAULT_GITHUB,
    linkedin_post_url: str = "[Link to LinkedIn Post]",
) -> str:
    """Template A: Presenters WITH Slides (<= 280 chars, deep-link, honest demo disclosure)."""
    domain = clean_domain(base_url)
    short_title = format_short_title(session_title, 25)
    note = (
        f'Hi {first_name}! Featured your talk "{short_title}" on our free toy demo: '
        f'{domain}/#session-{session_id} (slide viewer + RAG on free LLMs; super helpful for my agents!). '
        f'If you like it, a quick GitHub star means a lot! Apologies if misdirected!'
    )
    return clamp_note_length(note, 280)


def render_external_organizer_template(
    first_name: str,
    conf_name: str,
    base_url: str = DEFAULT_BASE_URL,
) -> tuple[str, str]:
    """Template D: External Conference Organizers (<= 280 chars, peer exchange, honest demo disclosure)."""
    domain = clean_domain(base_url)
    short_conf = format_short_title(conf_name, 25)
    subject = f"Open-source AI talk search for {short_conf} (learnings from AGNTCon demo)"
    body = (
        f"Hi {first_name}! Saw you organize {short_conf}. I built a free open-source toy demo for AGNTCon "
        f"({domain}) giving attendees instant AI search across 100+ talks & slides. "
        f"Happy to share the code if helpful for your event! Apologies if misdirected!"
    )
    return subject, clamp_note_length(body, 280)


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
    campaign_external_organizers = []
    suppressed_count = 0
    suppressed_verification_count = 0

    # 1. Generate for cohort_organizers (Template C)
    for org in organizers:
        name = org.get("name", "")
        cohort = org.get("cohort", "cohort_organizers")
        if cohort == "cohort_external_organizers":
            continue

        ln_url = org.get("linkedin_url")
        tw_url = org.get("twitter_url")

        if is_suspect_contact(org):
            suppressed_verification_count += 1
            continue

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

        if is_suspect_contact(spk):
            suppressed_verification_count += 1
            continue

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
            # Lookup or create magic link & compact link
            magic_url = ""
            token = ""
            if conn and outreach_db:
                tok_data = outreach_db.get_token(conn, sid)
                if tok_data:
                    magic_url = tok_data.get("magic_url", "")
                    token = tok_data.get("token", "")
            if not token:
                token = generate_token(sid)
                magic_url = f"{base_url.rstrip('/')}/contribute?token={token}"

            compact_url = f"{clean_domain(base_url)}/c?t={token}"
            body = render_missing_slides_template(first_name, title, token, base_url)
            msg_id = f"msg_missing_{spk.get('id', name)}_{sid}"
            rec = {
                "id": msg_id,
                "recipient_name": name,
                "session_id": sid,
                "session_title": title,
                "channel": channel,
                "target": target,
                "token": token,
                "compact_url": compact_url,
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

    # 3. Generate for External Organizers (cohort_external_organizers - Template D)
    external_orgs = list(contacts_data.get("external_organizers", []))
    for org in organizers:
        if org.get("cohort") == "cohort_external_organizers" and org not in external_orgs:
            external_orgs.append(org)

    for ext_org in external_orgs:
        name = ext_org.get("name", "")
        ln_url = ext_org.get("linkedin_url")
        tw_url = ext_org.get("twitter_url")

        if is_suspect_contact(ext_org):
            suppressed_verification_count += 1
            continue

        if name.lower() in opt_outs or (ln_url and ln_url.lower() in opt_outs) or (tw_url and tw_url.lower() in opt_outs):
            suppressed_count += 1
            continue

        first_name = get_first_name(name)
        conf_name = ext_org.get("conference_name") or ext_org.get("conference", "your conference")
        subject, body = render_external_organizer_template(first_name, conf_name, base_url)
        target = ln_url or tw_url or ext_org.get("company", "")
        channel = "linkedin" if ln_url else ("twitter" if tw_url else "email")
        msg_id = f"msg_ext_{ext_org.get('id', name)}"

        rec = {
            "id": msg_id,
            "recipient_name": name,
            "role": ext_org.get("role", ""),
            "company": ext_org.get("company", ""),
            "conference_name": conf_name,
            "channel": channel,
            "target": target,
            "subject": subject,
            "message": body,
            "cohort": "cohort_external_organizers",
        }
        campaign_external_organizers.append(rec)

        if conn and outreach_db:
            outreach_db.store_message(
                conn=conn,
                msg_id=msg_id,
                recipient_name=name,
                cohort="cohort_external_organizers",
                channel=channel,
                target_handle=target,
                message_text=body,
                status="draft",
            )

    # 4. Public Launch Post
    public_post = render_public_launch_post(base_url, github_repo)

    # 5. Save campaign files into out/campaigns/
    with open(out_dir / "cohort_organizers.json", "w", encoding="utf-8") as f:
        json.dump(campaign_organizers, f, indent=2, ensure_ascii=False)
    with open(out_dir / "cohort_missing_slides.json", "w", encoding="utf-8") as f:
        json.dump(campaign_missing_slides, f, indent=2, ensure_ascii=False)
    with open(out_dir / "cohort_slides_available.json", "w", encoding="utf-8") as f:
        json.dump(campaign_slides_available, f, indent=2, ensure_ascii=False)
    with open(out_dir / "cohort_external_organizers.json", "w", encoding="utf-8") as f:
        json.dump(campaign_external_organizers, f, indent=2, ensure_ascii=False)
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

    with open(out_dir / "cohort_external_organizers.md", "w", encoding="utf-8") as f:
        f.write(f"# Cohort: External Conference Organizers ({len(campaign_external_organizers)} targets)\n\n")
        for c in campaign_external_organizers:
            f.write(f"### {c['recipient_name']} - {c['conference_name']} - {c['channel']}: {c['target']}\n\n")
            f.write("```\n" + c["message"] + "\n```\n\n---\n\n")

    summary = {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "counts": {
            "cohort_organizers": len(campaign_organizers),
            "cohort_missing_slides": len(campaign_missing_slides),
            "cohort_slides_available": len(campaign_slides_available),
            "cohort_external_organizers": len(campaign_external_organizers),
            "public_launch_post": 1,
            "suppressed_due_to_opt_out": suppressed_count,
            "suppressed_due_to_verification": suppressed_verification_count,
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
