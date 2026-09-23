#!/usr/bin/env python3
"""Deterministic Offline Contact Verification Engine for AGNTCon & MCPCon Europe 2026.

Zero-Cost Invariant: 100% offline heuristic validator using Python standard libraries
(difflib, re, json, urllib.parse). Strictly zero paid external API dependencies.

Key Heuristics:
1. Name-to-Slug Overlap: token intersection + first-initial vanity pattern matching (asoshnin -> Alexey Soshnin)
2. Generic Account Discard: filters out sched.com, admin, info, support, team, help, etc.
3. Duplicate URL Detection: detects shared social handles erroneously attached to distinct contacts.
4. Benchmark Evaluation Harness: evaluates against golden benchmark (tests/fixtures/contacts_benchmark_golden.json),
   achieving >= 95% precision and >= 90% recall.
5. Dual Verification Reporting: exports out/verification_report.json for existing AGNTCon and incoming KIMI contacts.
"""

import argparse
import datetime
import difflib
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HUB_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONTACTS = HUB_DIR / "data" / "contacts.json"
DEFAULT_EXTERNAL = HUB_DIR / "data" / "external_conferences.json"
DEFAULT_BENCHMARK = HUB_DIR / "tests" / "fixtures" / "contacts_benchmark_golden.json"
DEFAULT_REPORT = HUB_DIR / "out" / "verification_report.json"

logger = logging.getLogger("verify_contacts")

GENERIC_KEYWORDS = {
    "admin",
    "support",
    "info",
    "team",
    "help",
    "contact",
    "marketing",
    "hello",
    "office",
    "press",
    "speaker",
    "system",
    "service",
    "sales",
    "general",
    "staff",
    "events",
    "organizer",
    "organizers",
}

GENERIC_DOMAINS = {
    "sched.com",
    "sched.co",
}


def normalize_url(url: str | None) -> str:
    """Normalizes a social URL for duplicate tracking and pattern matching."""
    if not url:
        return ""
    u = url.strip()
    u = re.sub(r"^https?://", "", u, flags=re.I)
    u = re.sub(r"^www\.", "", u, flags=re.I)
    return u.split("?")[0].rstrip("/").lower()


def extract_slug(url: str | None) -> str:
    """Extracts username / profile slug from LinkedIn, Twitter/X, or Sched URLs."""
    if not url:
        return ""
    u = url.strip()
    if not u.startswith("http://") and not u.startswith("https://"):
        u = "https://" + u
    try:
        parsed = urlparse(u)
        path = parsed.path.strip("/")
        parts = [p for p in path.split("/") if p]
        if not parts:
            return ""
        # LinkedIn format: /in/<slug> or /company/<slug>
        if "linkedin.com" in parsed.netloc.lower():
            if len(parts) >= 2 and parts[0] in ("in", "company", "pub"):
                return parts[1].lower()
            return parts[-1].lower()
        # Twitter/X format: /<slug>
        if any(d in parsed.netloc.lower() for d in ("twitter.com", "x.com")):
            return parts[0].lower()
        # Sched format: /speaker/<slug>
        if "sched.com" in parsed.netloc.lower():
            return parts[-1].lower()
        return parts[-1].lower()
    except Exception:
        return ""


def clean_name_tokens(full_name: str) -> list[str]:
    """Cleans personal titles and splits name into lowercase alphanumeric tokens."""
    if not full_name:
        return []
    cleaned = re.sub(r"^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+", "", full_name.strip(), flags=re.I)
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", cleaned)
    tokens = [t.lower() for t in cleaned.split() if t]
    return tokens


def check_generic_account(url: str | None, slug: str) -> tuple[bool, str | None]:
    """Detects generic, non-personal organizational handles."""
    if not url:
        return False, None
    norm = normalize_url(url)

    # Check generic domains
    for gd in GENERIC_DOMAINS:
        if gd in norm:
            return True, f"generic_domain_{gd}"

    # Check generic keywords in slug or path components
    slug_parts = re.split(r"[-_.\s/]", slug.lower())
    for part in slug_parts:
        if part in GENERIC_KEYWORDS:
            return True, f"generic_keyword_{part}"

    if "/company/" in norm:
        return True, "company_page_not_personal"

    return False, None


def check_vanity_pattern(name_tokens: list[str], slug: str) -> bool:
    """Checks for standard vanity slug conventions like first initial + surname (e.g. asoshnin for Alexey Soshnin)."""
    if len(name_tokens) < 2 or not slug:
        return False

    first_init = name_tokens[0][0]
    last_name = name_tokens[-1]
    first_name = name_tokens[0]

    slug_clean = re.sub(r"[0-9]", "", slug).lower()
    slug_tokens = re.split(r"[-_.\s]", slug_clean)

    vanity_patterns = [
        f"{first_init}{last_name}",
        f"{first_init}_{last_name}",
        f"{first_init}-{last_name}",
        f"{last_name}{first_init}",
        f"{first_name}{last_name}",
        f"{last_name}{first_name}",
    ]

    for pat in vanity_patterns:
        if pat in slug_clean:
            return True
        for st in slug_tokens:
            if st.startswith(pat) or st == pat:
                return True

    return False


def compute_name_slug_similarity(full_name: str, url: str | None) -> tuple[float, list[str], list[str]]:
    """Calculates heuristic match confidence between a person's name and their profile URL.

    Returns:
        (confidence: float, flags: list[str], reasons: list[str])
    """
    if not url:
        return 0.0, ["missing_social_url"], ["No social profile URL provided"]

    slug = extract_slug(url)
    if not slug:
        return 0.0, ["unparseable_url"], ["Could not extract handle slug from URL"]

    flags: list[str] = []
    reasons: list[str] = []

    # Heuristic 1: Generic account detection
    is_generic, gen_reason = check_generic_account(url, slug)
    if is_generic:
        flags.append("generic_handle")
        reasons.append(f"Handle matches generic non-personal account ({gen_reason})")
        return 0.15, flags, reasons

    name_tokens = clean_name_tokens(full_name)
    if not name_tokens:
        flags.append("missing_name")
        reasons.append("Contact name is empty")
        return 0.0, flags, reasons

    slug_clean = re.sub(r"[0-9]", "", slug).lower()
    slug_tokens = [t for t in re.split(r"[-_.\s]", slug_clean) if t]

    # Heuristic 2: Vanity slug check (asoshnin -> Alexey Soshnin)
    if check_vanity_pattern(name_tokens, slug):
        reasons.append("Matches first-initial vanity slug pattern")
        return 0.90, flags, reasons

    # Heuristic 3: Token overlap
    matched_tokens = [t for t in name_tokens if t in slug_clean or any(t == st for st in slug_tokens)]
    token_overlap_ratio = len(matched_tokens) / len(name_tokens)

    if token_overlap_ratio == 1.0:
        reasons.append("All name tokens present in handle slug")
        return 0.95, flags, reasons

    if len(name_tokens) > 2 and len(matched_tokens) >= 2:
        reasons.append(f"Multiple name tokens ({', '.join(matched_tokens)}) present in handle slug")
        return 0.92, flags, reasons

    # Heuristic 4: Sequence similarity
    clean_name_str = "".join(name_tokens)
    clean_slug_str = "".join(slug_tokens)
    seq_ratio = difflib.SequenceMatcher(None, clean_name_str, clean_slug_str).ratio()

    if seq_ratio >= 0.80:
        reasons.append(f"High sequence similarity ({seq_ratio:.2f})")
        return max(0.85, seq_ratio), flags, reasons

    if token_overlap_ratio > 0.5:
        reasons.append(f"Partial name token match ({', '.join(matched_tokens)})")
        return 0.80, flags, reasons

    # If mismatch
    flags.append("slug_name_mismatch")
    reasons.append(f"Name '{full_name}' does not match handle slug '{slug}' (similarity {seq_ratio:.2f})")
    conf = min(0.40, max(0.10, seq_ratio))
    return conf, flags, reasons


def find_duplicate_urls(contacts: list[dict]) -> dict[str, list[str]]:
    """Identifies social URLs that are erroneously attached to multiple distinct contacts."""
    url_map: dict[str, list[str]] = {}
    for c in contacts:
        cid = c.get("id") or c.get("speaker_id") or c.get("name", "unknown")
        url = c.get("linkedin_url") or c.get("twitter_url") or c.get("social_url")
        if not url:
            continue
        norm = normalize_url(url)
        if norm:
            url_map.setdefault(norm, []).append(cid)

    # Filter to only duplicates across different contact IDs
    duplicates = {u: cids for u, cids in url_map.items() if len(set(cids)) > 1}
    return duplicates


def verify_single_contact(
    contact: dict,
    duplicate_urls: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Runs all offline heuristics on a single contact record.

    Returns a verification dict:
    {
        "status": "verified" | "suspect",
        "confidence": float,
        "flags": list[str],
        "reasons": list[str],
        "action": "approve" | "suppress_until_reviewed"
    }
    """
    name = contact.get("name", "")
    url = contact.get("linkedin_url") or contact.get("twitter_url") or contact.get("social_url")
    norm_url = normalize_url(url)

    # 1. Base name-to-slug verification
    confidence, flags, reasons = compute_name_slug_similarity(name, url)

    # 2. Duplicate URL check
    if duplicate_urls and norm_url in duplicate_urls:
        if "duplicate_url" not in flags:
            flags.append("duplicate_url")
        shared_with = duplicate_urls[norm_url]
        reasons.append(f"Social URL shared across {len(shared_with)} distinct contacts: {', '.join(shared_with)}")
        confidence = min(confidence, 0.20)

    # 3. Final classification
    # Suspect criteria: any anomaly flag, or confidence < 0.70
    is_suspect = (
        bool(flags)
        or confidence < 0.70
        or "generic_handle" in flags
        or "duplicate_url" in flags
        or "slug_name_mismatch" in flags
        or "missing_social_url" in flags
    )

    status = "suspect" if is_suspect else "verified"
    action = "suppress_until_reviewed" if is_suspect else "approve"

    return {
        "status": status,
        "confidence": round(confidence, 2),
        "flags": flags,
        "reasons": reasons,
        "action": action,
    }


def evaluate_contacts_checker(benchmark_path: Path | str = DEFAULT_BENCHMARK) -> dict[str, Any]:
    """Evaluates the heuristic validator against ground-truth golden benchmark.

    Benchmark Golden Test Requirements:
    - Precision >= 95%
    - Recall >= 90%
    """
    bpath = Path(benchmark_path)
    if not bpath.exists():
        raise FileNotFoundError(f"Benchmark golden file not found at {bpath}")

    with open(bpath, encoding="utf-8") as f:
        cases = json.load(f)

    duplicate_urls = find_duplicate_urls(cases)

    tp = 0  # Expected verified, predicted verified
    fp = 0  # Expected suspect, predicted verified
    fn = 0  # Expected verified, predicted suspect
    tn = 0  # Expected suspect, predicted suspect

    results_detail = []

    for c in cases:
        expected = c.get("expected_status", "verified")
        verif = verify_single_contact(c, duplicate_urls=duplicate_urls)
        predicted = verif["status"]

        if expected == "verified":
            if predicted == "verified":
                tp += 1
            else:
                fn += 1
        else:  # expected suspect
            if predicted == "verified":
                fp += 1
            else:
                tn += 1

        results_detail.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "category": c.get("category"),
            "expected": expected,
            "predicted": predicted,
            "confidence": verif["confidence"],
            "flags": verif["flags"],
            "correct": expected == predicted,
        })

    total = len(cases)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    accuracy = (tp + tn) / total if total > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    passed = (precision >= 0.95) and (recall >= 0.90) and (fp == 0)

    return {
        "total_cases": total,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "passed": passed,
        "details": results_detail,
    }


def verify_contacts(contacts_data: dict) -> dict[str, Any]:
    """Runs contact verification across all cohorts in contacts_data and mutates records in-place."""
    all_contacts: list[dict] = []
    speakers = contacts_data.get("speakers", [])
    organizers = contacts_data.get("organizers", [])
    external_orgs = contacts_data.get("external_organizers", [])

    all_contacts.extend(speakers)
    all_contacts.extend(organizers)
    all_contacts.extend(external_orgs)

    duplicate_urls = find_duplicate_urls(all_contacts)

    verified_count = 0
    suspect_count = 0
    anomalies: list[dict] = []

    for c in all_contacts:
        verif = verify_single_contact(c, duplicate_urls=duplicate_urls)
        c["verification_status"] = verif["status"]
        c["verification"] = verif

        if verif["status"] == "verified":
            verified_count += 1
        else:
            suspect_count += 1
            anomalies.append({
                "id": c.get("id", c.get("name")),
                "name": c.get("name"),
                "cohort": c.get("cohort", "unknown"),
                "flags": verif["flags"],
                "confidence": verif["confidence"],
                "reasons": verif["reasons"],
            })

    return {
        "total_contacts": len(all_contacts),
        "verified_count": verified_count,
        "suspect_count": suspect_count,
        "anomalies": anomalies,
    }


def run_full_verification(
    contacts_path: Path | str = DEFAULT_CONTACTS,
    external_path: Path | str = DEFAULT_EXTERNAL,
    benchmark_path: Path | str = DEFAULT_BENCHMARK,
    report_path: Path | str = DEFAULT_REPORT,
) -> dict[str, Any]:
    """Executes the dual verification process and writes out/verification_report.json."""
    contacts_path = Path(contacts_path)
    external_path = Path(external_path)
    benchmark_path = Path(benchmark_path)
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Run Golden Benchmark
    bench_result = evaluate_contacts_checker(benchmark_path)

    # 2. Run on Existing AGNTCon Contacts
    agntcon_result: dict[str, Any] = {"status": "not_found"}
    if contacts_path.exists():
        with open(contacts_path, encoding="utf-8") as f:
            agntcon_data = json.load(f)
        agntcon_result = verify_contacts(agntcon_data)
        # Update contacts.json on disk with verification statuses
        with open(contacts_path, "w", encoding="utf-8") as f:
            json.dump(agntcon_data, f, indent=2, ensure_ascii=False)

    # 3. Run on External Conferences KIMI Manifest
    external_result: dict[str, Any] = {"status": "not_found"}
    if external_path.exists():
        with open(external_path, encoding="utf-8") as f:
            ext_data = json.load(f)
        ext_contacts: list[dict] = []
        for conf in ext_data.get("conferences", []):
            conf_name = conf.get("name", "")
            for org in conf.get("organizers", []):
                org_copy = dict(org)
                org_copy["conference_name"] = conf_name
                org_copy["cohort"] = "cohort_external_organizers"
                ext_contacts.append(org_copy)
        if ext_contacts:
            external_result = verify_contacts({"external_organizers": ext_contacts})

    full_report = {
        "evaluated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "benchmark": bench_result,
        "agntcon_contacts": agntcon_result,
        "external_conferences": external_result,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)

    return full_report


def main():
    parser = argparse.ArgumentParser(description="Deterministic Offline Contact Verification Engine")
    parser.add_argument("--contacts", default=str(DEFAULT_CONTACTS), help="Path to contacts.json")
    parser.add_argument("--external", default=str(DEFAULT_EXTERNAL), help="Path to external_conferences.json")
    parser.add_argument("--benchmark", default=str(DEFAULT_BENCHMARK), help="Path to golden benchmark fixture")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Path to output verification_report.json")
    args = parser.parse_args()

    report = run_full_verification(
        contacts_path=args.contacts,
        external_path=args.external,
        benchmark_path=args.benchmark,
        report_path=args.report,
    )
    bench = report["benchmark"]
    print(f"Benchmark Results: Total={bench['total_cases']}, Precision={bench['precision']:.2%}, Recall={bench['recall']:.2%}, Passed={bench['passed']}")
    print(f"AGNTCon Contacts: Total={report['agntcon_contacts'].get('total_contacts')}, Verified={report['agntcon_contacts'].get('verified_count')}, Suspect={report['agntcon_contacts'].get('suspect_count')}")
    print(f"Report exported to: {args.report}")


if __name__ == "__main__":
    main()
