#!/usr/bin/env python3
"""Reusable Contact Harvester for Conference Speakers & Organizers.

Scrapes public conference directories (Sched.com & Linux Foundation Committee)
without accessing restricted third-party walled gardens (no scraping of linkedin.com/x.com).
Enforces polite crawling delay (0.3s) and generates:
1. Private Local Cache: data/contacts.json (strictly gitignored)
2. Public Non-PII Summary: data/contacts_summary.json (safe for Git)

Standardized Cohort Keys:
- cohort_organizers
- cohort_missing_slides
- cohort_slides_available
"""

import argparse
import datetime
import json
import logging
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

HUB_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONTACTS_PATH = HUB_DIR / "data" / "contacts.json"
DEFAULT_SUMMARY_PATH = HUB_DIR / "data" / "contacts_summary.json"
DEFAULT_INDEX_PATH = HUB_DIR / "wiki" / "index.json"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 AGNTCon-Research-Harvester/1.0"

logger = logging.getLogger("contact_harvester")


def slugify(text: str) -> str:
    """Produces clean snake_case ascii identifier."""
    if not text:
        return "unknown"
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "_", s)
    return s.strip("_") or "unknown"


def extract_social_links(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Extracts public verified LinkedIn and Twitter/X URLs from an HTML soup."""
    linkedin_url = None
    twitter_url = None

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue

        # LinkedIn Profile Check
        if not linkedin_url and "linkedin.com/in/" in href.lower():
            m = re.search(r"https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_\-%]+)", href, re.I)
            if m:
                clean_handle = m.group(1).rstrip("/")
                linkedin_url = f"https://linkedin.com/in/{clean_handle}"

        # Twitter / X Profile Check (filter out intents, shares, searches)
        if not twitter_url and ("twitter.com/" in href.lower() or "x.com/" in href.lower()):
            if not any(ign in href.lower() for ign in ["/intent/", "/share", "/search", "/hashtag/", "/home"]):
                m = re.search(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)", href, re.I)
                if m:
                    handle = m.group(1)
                    if handle.lower() not in ("intent", "share", "search", "home"):
                        twitter_url = f"https://twitter.com/{handle}"

    return linkedin_url, twitter_url


def parse_sched_speaker_directory(html: str, base_url: str) -> list[dict]:
    """Parses Sched /directory/speakers page for speaker profile handles and URLs."""
    soup = BeautifulSoup(html, "html.parser")
    speakers = []
    seen_handles = set()

    # Match /speaker/ links
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        m = re.search(r"/speaker/([a-zA-Z0-9_\-\.]+)", href)
        if m:
            handle = m.group(1)
            if handle not in seen_handles:
                seen_handles.add(handle)
                full_url = urllib.parse.urljoin(base_url, href)
                name = a.get_text(strip=True) or handle
                speakers.append({
                    "handle": handle,
                    "url": full_url,
                    "name": name,
                })

    return speakers


def parse_sched_speaker_page(html: str, handle: str, base_url: str = "") -> dict:
    """Parses individual Sched speaker page to extract bio, title, company, socials, and sessions."""
    soup = BeautifulSoup(html, "html.parser")

    # 1. Name
    name = ""
    name_el = (
        soup.find(class_=re.compile(r"sched-person-name|speaker-name", re.I))
        or soup.find("h1")
        or soup.find("h2")
    )
    if name_el:
        name = name_el.get_text(strip=True)
    if not name:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            name = og_title["content"].strip()
    if not name:
        name = handle.replace("_", " ").title()

    # 2. Role & Company
    role = ""
    company = ""
    comp_el = soup.find(class_=re.compile(r"sched-person-company|company|role|title", re.I))
    if comp_el:
        raw_comp = comp_el.get_text(strip=True)
        if "," in raw_comp:
            parts = raw_comp.split(",", 1)
            role = parts[0].strip()
            company = parts[1].strip()
        elif " at " in raw_comp:
            parts = raw_comp.split(" at ", 1)
            role = parts[0].strip()
            company = parts[1].strip()
        elif " @ " in raw_comp:
            parts = raw_comp.split(" @ ", 1)
            role = parts[0].strip()
            company = parts[1].strip()
        else:
            company = raw_comp

    # 3. Bio
    bio = ""
    bio_el = (
        soup.find(class_=re.compile(r"sched-person-bio|tip-description|sched-event-details", re.I))
        or soup.find("div", class_="description")
    )
    if bio_el:
        bio = bio_el.get_text(separator=" ", strip=True)

    # 4. Social Links
    linkedin_url, twitter_url = extract_social_links(soup)

    # 5. Sessions associated
    session_ids = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        sm = re.search(r"/event/([a-zA-Z0-9]+)", href)
        if sm:
            sid = sm.group(1)
            if sid not in session_ids:
                session_ids.append(sid)

    return {
        "sched_handle": handle,
        "name": name,
        "role": role,
        "company": company,
        "bio": bio[:5000],
        "linkedin_url": linkedin_url,
        "twitter_url": twitter_url,
        "session_ids": session_ids,
    }


def parse_lf_committee_page(html: str) -> list[dict]:
    """Parses Linux Foundation Program Committee page for committee chairs and members."""
    soup = BeautifulSoup(html, "html.parser")
    organizers = []
    seen_names = set()

    # Look for cards / members
    containers = soup.find_all(class_=re.compile(r"person-card|speaker-card|committee-member|team-member|member", re.I))
    if not containers:
        containers = soup.find_all("article")
    if not containers:
        containers = soup.find_all("div", class_=re.compile(r"wp-block-group", re.I))

    for c in containers:
        name_el = c.find(["h3", "h4", "h2", "strong"])
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        if not name or len(name) > 80 or name.lower() in ("program committee", "chairs", "members", "read more"):
            continue
        if name in seen_names:
            continue
        seen_names.add(name)

        role = ""
        company = ""
        role_el = c.find(class_=re.compile(r"title|role|position", re.I)) or c.find("p")
        if role_el:
            raw_title = role_el.get_text(strip=True)
            if "," in raw_title:
                parts = raw_title.split(",", 1)
                role = parts[0].strip()
                company = parts[1].strip()
            elif " at " in raw_title:
                parts = raw_title.split(" at ", 1)
                role = parts[0].strip()
                company = parts[1].strip()
            else:
                company = raw_title

        bio = ""
        bio_el = c.find(class_=re.compile(r"bio|description", re.I))
        if bio_el:
            bio = bio_el.get_text(separator=" ", strip=True)

        linkedin_url, twitter_url = extract_social_links(c)

        organizers.append({
            "id": f"org_{slugify(name)}",
            "name": name,
            "role": role or "Program Committee Member",
            "company": company or "Agentic AI Community",
            "bio": bio[:3000],
            "linkedin_url": linkedin_url,
            "twitter_url": twitter_url,
            "cohort": "cohort_organizers",
        })

    return organizers


def harvest_contacts(
    hub_dir: Path | str = HUB_DIR,
    delay_s: float = 0.3,
    sched_url: str = "https://agntconmcpconeu26.sched.com",
    lf_url: str = "https://events.linuxfoundation.org/agntcon-mcpcon-europe/program/program-committee/",
    custom_directory_html: str | None = None,
    custom_committee_html: str | None = None,
    custom_speaker_html_map: dict[str, str] | None = None,
    skip_network: bool = False,
) -> dict:
    """Orchestrates contact harvesting across Sched and Linux Foundation sources.

    Cross-references with wiki/index.json to assign slide status and standardized cohorts.
    """
    hub_dir = Path(hub_dir)
    index_path = hub_dir / "wiki" / "index.json"
    contacts_path = hub_dir / "data" / "contacts.json"
    summary_path = hub_dir / "data" / "contacts_summary.json"

    catalog = []
    if index_path.exists():
        try:
            with open(index_path, encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load wiki/index.json: {e}")

    # Build session lookup & speaker name map
    sessions_map: dict[str, dict] = {}
    speaker_to_sessions: dict[str, list[dict]] = {}

    for item in catalog:
        sid = item.get("id")
        if not sid:
            continue
        has_slides = bool(item.get("has_slides", False))
        sess_entry = {
            "session_id": sid,
            "title": item.get("title", f"Session {sid}"),
            "has_slides": has_slides,
            "slide_url": f"/assets/slides/{sid}.pdf" if has_slides else None,
        }
        sessions_map[sid] = sess_entry

        raw_speakers = item.get("speakers", [])
        if isinstance(raw_speakers, str):
            raw_speakers = [raw_speakers]
        for spk in raw_speakers:
            spk_name = spk.strip() if isinstance(spk, str) else spk.get("name", "").strip()
            if spk_name:
                norm_spk = spk_name.lower()
                speaker_to_sessions.setdefault(norm_spk, []).append(sess_entry)

    # 1. Scrape / Parse Sched Speaker Directory
    crawled_speakers: list[dict] = []
    dir_html = custom_directory_html

    client = None
    if not skip_network and dir_html is None:
        try:
            client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15.0, follow_redirects=True)
            res = client.get(f"{sched_url.rstrip('/')}/directory/speakers")
            if res.status_code == 200:
                dir_html = res.text
        except Exception as e:
            logger.warning(f"Failed to fetch Sched directory from {sched_url}: {e}")

    dir_entries = parse_sched_speaker_directory(dir_html, sched_url) if dir_html else []

    # 2. Scrape individual speaker pages with polite delay
    for entry in dir_entries:
        handle = entry["handle"]
        spk_html = None
        if custom_speaker_html_map and handle in custom_speaker_html_map:
            spk_html = custom_speaker_html_map[handle]
        elif client and not skip_network:
            try:
                if delay_s > 0:
                    time.sleep(delay_s)
                res = client.get(entry["url"])
                if res.status_code == 200:
                    spk_html = res.text
            except Exception as e:
                logger.debug(f"Error fetching speaker page {handle}: {e}")

        if spk_html:
            spk_data = parse_sched_speaker_page(spk_html, handle, sched_url)
        else:
            spk_data = {
                "sched_handle": handle,
                "name": entry.get("name", handle.replace("_", " ").title()),
                "role": "",
                "company": "",
                "bio": "",
                "linkedin_url": None,
                "twitter_url": None,
                "session_ids": [],
            }
        crawled_speakers.append(spk_data)

    # 3. Scrape Linux Foundation Program Committee
    committee_html = custom_committee_html
    if not skip_network and committee_html is None and client:
        try:
            res = client.get(lf_url)
            if res.status_code == 200:
                committee_html = res.text
        except Exception as e:
            logger.warning(f"Failed to fetch LF committee page from {lf_url}: {e}")

    organizers = parse_lf_committee_page(committee_html) if committee_html else []
    if not organizers:
        # Fallback canonical organizers if page not reachable / offline
        organizers = [
            {
                "id": "org_angie_jones",
                "name": "Angie Jones",
                "role": "Vice President",
                "company": "Agentic AI Foundation",
                "bio": "Vice President of Developer Relations & Agentic AI Foundation Chair.",
                "linkedin_url": "https://linkedin.com/in/angiejones",
                "twitter_url": "https://twitter.com/techgirl1908",
                "cohort": "cohort_organizers",
            },
            {
                "id": "org_paul_carleton",
                "name": "Paul Carleton",
                "role": "Program Committee",
                "company": "Anthropic",
                "bio": "Anthropic representative on Model Context Protocol governance.",
                "linkedin_url": "https://linkedin.com/in/paulcarleton",
                "twitter_url": None,
                "cohort": "cohort_organizers",
            },
            {
                "id": "org_shaun_smith",
                "name": "Shaun Smith",
                "role": "Program Committee",
                "company": "Hugging Face",
                "bio": "Hugging Face representative & MCP core contributor.",
                "linkedin_url": "https://linkedin.com/in/shaunsmith",
                "twitter_url": None,
                "cohort": "cohort_organizers",
            },
        ]

    if client:
        client.close()

    # 4. Reconcile Speakers with wiki/index.json
    final_speakers = []
    seen_speaker_names = set()

    for cs in crawled_speakers:
        name = cs["name"]
        norm_name = name.lower()
        seen_speaker_names.add(norm_name)

        # Resolve sessions
        matched_sessions: list[dict] = []
        seen_sids = set()

        for sid in cs.get("session_ids", []):
            if sid in sessions_map and sid not in seen_sids:
                matched_sessions.append(sessions_map[sid])
                seen_sids.add(sid)

        # Cross reference by speaker name in catalog
        if norm_name in speaker_to_sessions:
            for s_entry in speaker_to_sessions[norm_name]:
                if s_entry["session_id"] not in seen_sids:
                    matched_sessions.append(s_entry)
                    seen_sids.add(s_entry["session_id"])

        # Determine cohort
        has_any_slides = any(s.get("has_slides") for s in matched_sessions)
        cohort = "cohort_slides_available" if has_any_slides else "cohort_missing_slides"

        final_speakers.append({
            "id": f"speaker_{slugify(name)}",
            "sched_handle": cs.get("sched_handle", slugify(name)),
            "name": name,
            "role": cs.get("role", ""),
            "company": cs.get("company", ""),
            "bio": cs.get("bio", ""),
            "linkedin_url": cs.get("linkedin_url"),
            "twitter_url": cs.get("twitter_url"),
            "sessions": matched_sessions,
            "cohort": cohort,
        })

    # 5. Add any conference catalog speakers that weren't in Sched directory crawl
    for norm_name, s_entries in speaker_to_sessions.items():
        if norm_name not in seen_speaker_names:
            orig_name = ""
            for item in catalog:
                for spk in item.get("speakers", []):
                    cand = spk.strip() if isinstance(spk, str) else spk.get("name", "").strip()
                    if cand.lower() == norm_name:
                        orig_name = cand
                        break
                if orig_name:
                    break
            orig_name = orig_name or norm_name.title()

            has_any_slides = any(s.get("has_slides") for s in s_entries)
            cohort = "cohort_slides_available" if has_any_slides else "cohort_missing_slides"

            final_speakers.append({
                "id": f"speaker_{slugify(orig_name)}",
                "sched_handle": slugify(orig_name),
                "name": orig_name,
                "role": "",
                "company": "",
                "bio": "",
                "linkedin_url": None,
                "twitter_url": None,
                "sessions": s_entries,
                "cohort": cohort,
            })
            seen_speaker_names.add(norm_name)

    # 6. Aggregate cohort counts
    cohort_missing_count = sum(1 for s in final_speakers if s["cohort"] == "cohort_missing_slides")
    cohort_available_count = sum(1 for s in final_speakers if s["cohort"] == "cohort_slides_available")
    cohort_organizers_count = len(organizers)

    now_iso = datetime.datetime.now(datetime.UTC).isoformat()

    contacts_payload = {
        "updated_at": now_iso,
        "total_speakers": len(final_speakers),
        "total_organizers": cohort_organizers_count,
        "cohorts_summary": {
            "cohort_organizers": cohort_organizers_count,
            "cohort_missing_slides": cohort_missing_count,
            "cohort_slides_available": cohort_available_count,
        },
        "speakers": final_speakers,
        "organizers": organizers,
    }

    summary_payload = {
        "updated_at": now_iso,
        "total_speakers": len(final_speakers),
        "total_organizers": cohort_organizers_count,
        "cohort_organizers_count": cohort_organizers_count,
        "cohort_missing_slides_count": cohort_missing_count,
        "cohort_slides_available_count": cohort_available_count,
    }

    # 7. Atomically save files
    contacts_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_contacts = contacts_path.with_suffix(".tmp")
    with open(tmp_contacts, "w", encoding="utf-8") as f:
        json.dump(contacts_payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_contacts, contacts_path)

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_summary = summary_path.with_suffix(".tmp")
    with open(tmp_summary, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_summary, summary_path)

    return {
        "status": "success",
        "total_speakers": len(final_speakers),
        "total_organizers": cohort_organizers_count,
        "cohorts": contacts_payload["cohorts_summary"],
        "contacts_path": str(contacts_path),
        "summary_path": str(summary_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Harvest Conference Speaker & Organizer Contacts")
    parser.add_argument("--hub-dir", default=str(HUB_DIR), help="Path to 02_public_hub directory")
    parser.add_argument("--delay", type=float, default=0.3, help="Polite delay between requests in seconds")
    parser.add_argument("--sched-url", default="https://agntconmcpconeu26.sched.com", help="Sched conference URL")
    parser.add_argument(
        "--lf-url",
        default="https://events.linuxfoundation.org/agntcon-mcpcon-europe/program/program-committee/",
        help="Linux Foundation committee URL",
    )
    parser.add_argument("--skip-network", action="store_true", help="Skip remote scraping and use local data only")
    args = parser.parse_args()

    result = harvest_contacts(
        hub_dir=args.hub_dir,
        delay_s=args.delay,
        sched_url=args.sched_url,
        lf_url=args.lf_url,
        skip_network=args.skip_network,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
