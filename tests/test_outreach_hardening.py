"""Unit and Integration Tests for Sprint 19: Outreach Hardening, Contact Verification & Cross-Conference Expansion.

Tests:
1. Mathematical <= 280-char bound across Templates A, B, C, D.
2. format_short_title truncation guardrail at 25 chars.
3. Compact URL scheme (agntcon-demo.vwoosh.com/c?t={token}).
4. Honest toy demo & free LLM disclosure ("Apologies if misdirected!").
5. Fortified CSV formula injection defense.
6. Golden benchmark fixture evaluation (>= 95% precision, >= 90% recall).
7. Deterministic offline verification heuristics (vanity slug, generic discard, duplicate detector).
8. Admin contacts export endpoint (CSV / JSON) with auth guard.
9. Short-link redirect route (/c?t={token}).
10. Cross-conference manifest validation and ingestion.
"""

import csv
import io
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import serve
from scripts.generate_outreach_campaign import (
    clamp_note_length,
    format_short_title,
    generate_campaign,
    render_external_organizer_template,
    render_missing_slides_template,
    render_organizer_template,
    render_slides_available_template,
)
from scripts.import_external_conferences import (
    import_external_conferences,
    validate_conference_manifest,
)
from scripts.verify_contacts import (
    compute_name_slug_similarity,
    evaluate_contacts_checker,
    find_duplicate_urls,
    verify_contacts,
    verify_single_contact,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
GOLDEN_BENCHMARK_PATH = FIXTURES_DIR / "contacts_benchmark_golden.json"


# =========================================================================
# 1. Title Formatting & Length Truncation Guardrail
# =========================================================================
def test_format_short_title():
    # Below max_chars
    assert format_short_title("Short Title", 25) == "Short Title"
    # Exactly max_chars
    assert format_short_title("A" * 25, 25) == "A" * 25
    # Above max_chars
    truncated = format_short_title("An Orchestra of Agents: What I Learned Running MAS", 25)
    assert len(truncated) == 25
    assert truncated.endswith("...")
    assert truncated == "An Orchestra of Agents..."

    # Handles quotes and whitespace
    assert format_short_title('  "Quoted Talk Title"  ', 25) == "'Quoted Talk Title'"
    # Handles empty / None
    assert format_short_title("", 25) == ""
    assert format_short_title(None, 25) == ""


# =========================================================================
# 2. Mathematical <= 280 Character Bound & Honest Demo Disclosures
# =========================================================================
@pytest.mark.parametrize(
    "first_name,title,session_id,token,conf_name",
    [
        ("Anushka-Priya", "An Orchestra of Agents: What I Learned Running MAS", "2RB8M", "2RB8t.1791234567.a1b2c3d4e5f67890123", "AI Engineer World's Fair 2026"),
        ("Muhammad", "Building Deterministic Agents With MCP Tooling", "2RB9X", "tok_35_chars_long_hmac_test_1234567", "MCP DevCon Europe 2026"),
        ("Alexey", "Production FastEmbed RAG", "2RB1A", "token_standard_length_123456789012", "PyCon Europe 2026"),
        ("A" * 15, "B" * 60, "2RB99", "C" * 35, "D" * 50),
    ],
)
def test_campaign_templates_mathematical_length_bound(first_name, title, session_id, token, conf_name):
    # Template A: Presenters WITH slides
    note_a = render_slides_available_template(first_name, title, session_id)
    assert len(note_a) <= 280
    assert "toy demo" in note_a or "free" in note_a
    assert "Apologies if misdirected!" in note_a
    assert f"#session-{session_id}" in note_a

    # Template B: Presenters WITHOUT slides
    note_b = render_missing_slides_template(first_name, title, token)
    assert len(note_b) <= 280
    assert "agntcon-demo.vwoosh.com/c?t=" in note_b
    assert "Apologies if misdirected!" in note_b
    assert "toy demo" in note_b or "free" in note_b

    # Template C: AGNTCon Organizers
    _, body_c = render_organizer_template(first_name)
    assert len(body_c) <= 280
    assert "toy demo" in body_c or "free" in body_c
    assert "Apologies if misdirected!" in body_c

    # Template D: External Conference Organizers
    _, body_d = render_external_organizer_template(first_name, conf_name)
    assert len(body_d) <= 280
    assert "toy demo" in body_d or "free" in body_d
    assert "Apologies if misdirected!" in body_d


def test_clamp_note_length_safeguard():
    # Under limit
    short_text = "Hello world! Apologies if misdirected!"
    assert clamp_note_length(short_text, 280) == short_text

    # Massive text over 350 chars
    massive_text = "A" * 350 + " Apologies if misdirected!"
    clamped = clamp_note_length(massive_text, 280)
    assert len(clamped) <= 280
    assert clamped.endswith(" Apologies if misdirected!")


# =========================================================================
# 3. Fortified CSV Formula Injection Defense
# =========================================================================
@pytest.mark.parametrize(
    "raw_input,expected_output",
    [
        ("=1+1", "'=1+1"),
        ("   =CMD('calc')", "'   =CMD('calc')"),
        ("+44123456", "'+44123456"),
        ("-999", "'-999"),
        ("@evil_macro", "'@evil_macro"),
        ("\tcmd.exe", "'\tcmd.exe"),
        ("\r\n+SUM(A1:A5)", "'\r\n+SUM(A1:A5)"),
        ("\n=DDE('foo')", "'\n=DDE('foo')"),
        ("Normal text", "Normal text"),
        ("Alexey Soshnin", "Alexey Soshnin"),
        ("", ""),
        (None, ""),
    ],
)
def test_sanitize_csv_cell_formula_injection(raw_input, expected_output):
    assert serve.sanitize_csv_cell(raw_input) == expected_output


# =========================================================================
# 4. Golden Benchmark Fixture & Precision/Recall Gate
# =========================================================================
def test_contacts_verification_golden_benchmark():
    assert GOLDEN_BENCHMARK_PATH.exists(), "Benchmark fixture must exist"

    results = evaluate_contacts_checker(GOLDEN_BENCHMARK_PATH)

    assert results["total_cases"] == 30
    assert results["precision"] >= 0.95, f"Precision {results['precision']:.2%} is below 95%"
    assert results["recall"] >= 0.90, f"Recall {results['recall']:.2%} is below 90%"
    assert results["fp"] == 0, "No false positives (suspect classified as verified) allowed"
    assert results["passed"] is True


# =========================================================================
# 5. Deterministic Offline Heuristics Unit Tests
# =========================================================================
def test_name_slug_clean_and_vanity_matching():
    # Clean full name match
    conf, flags, _ = compute_name_slug_similarity("Sam Morrow", "https://linkedin.com/in/sammorrow")
    assert conf >= 0.90
    assert not flags

    # Vanity slug: first initial + surname (asoshnin -> Alexey Soshnin)
    conf_v, flags_v, reasons_v = compute_name_slug_similarity("Alexey Soshnin", "https://linkedin.com/in/asoshnin")
    assert conf_v >= 0.85
    assert not flags_v
    assert any("vanity" in r.lower() for r in reasons_v)

    # Vanity slug: John Smith -> jsmith
    conf_j, flags_j, _ = compute_name_slug_similarity("John Smith", "https://linkedin.com/in/jsmith")
    assert conf_j >= 0.85
    assert not flags_j

    # Deliberate mismatch: John Doe -> jane-smith-accountant
    conf_m, flags_m, _ = compute_name_slug_similarity("John Doe", "https://linkedin.com/in/jane-smith-accountant")
    assert conf_m < 0.50
    assert "slug_name_mismatch" in flags_m

    # Generic account discard: Sched Support -> sched.com/speaker/support
    conf_g, flags_g, _ = compute_name_slug_similarity("Sched Support", "https://sched.com/speaker/support")
    assert conf_g <= 0.30
    assert "generic_handle" in flags_g


def test_duplicate_social_url_detection():
    contacts = [
        {"id": "spk_1", "name": "Alice", "linkedin_url": "https://linkedin.com/in/shared-handle"},
        {"id": "spk_2", "name": "Bob", "linkedin_url": "https://linkedin.com/in/shared-handle"},
        {"id": "spk_3", "name": "Charlie", "linkedin_url": "https://linkedin.com/in/unique-handle"},
    ]
    dupes = find_duplicate_urls(contacts)
    assert "linkedin.com/in/shared-handle" in dupes
    assert len(dupes["linkedin.com/in/shared-handle"]) == 2

    # Verify single contact flags duplicate
    v1 = verify_single_contact(contacts[0], duplicate_urls=dupes)
    assert v1["status"] == "suspect"
    assert "duplicate_url" in v1["flags"]
    assert v1["confidence"] <= 0.20

    v3 = verify_single_contact(contacts[2], duplicate_urls=dupes)
    assert "duplicate_url" not in v3["flags"]


# =========================================================================
# 6. Admin Contacts Export API Endpoint
# =========================================================================
class MockServerHandler(serve.HubHTTPRequestHandler):
    """Mock handler that intercepts HTTP response headers and body without opening sockets."""

    def __init__(self, path: str, headers: dict | None = None):
        self.path = path
        self.headers = headers or {}
        self.rfile = io.BytesIO()
        self.wfile = io.BytesIO()
        self._response_code = 0
        self._response_headers = {}

    def send_response(self, code, message=None):
        self._response_code = code

    def send_header(self, keyword, value):
        self._response_headers[keyword] = value

    def end_headers(self):
        pass


def test_api_admin_contacts_export_unauthorized():
    handler = MockServerHandler("/api/admin/contacts/export?cohort=cohort_organizers")
    handler.do_GET()
    assert handler._response_code == 401
    body = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert body["error"] == "Unauthorized"


def test_api_admin_contacts_export_csv_and_injection_defense(tmp_path, monkeypatch):
    # Set up mock contacts file with formula injection attempt
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    contacts_file = data_dir / "contacts.json"
    mock_contacts = {
        "organizers": [
            {
                "name": "=CMD('calc')",
                "role": "Lead Organizer",
                "company": "Tech Corp",
                "conference_name": "AGNTCon Europe 2026",
                "linkedin_url": "https://linkedin.com/in/techorganizer",
                "cohort": "cohort_organizers",
                "verification_status": "verified",
            },
            {
                "name": "Jane Smith",
                "role": "Program Committee",
                "company": "AI Labs",
                "conference_name": "AGNTCon Europe 2026",
                "linkedin_url": "https://linkedin.com/in/janesmith",
                "cohort": "cohort_organizers",
                "verification_status": "verified",
            },
        ],
        "external_organizers": [
            {
                "name": "Swyx",
                "role": "Organizer",
                "company": "Smol AI",
                "conference_name": "AI Engineer World's Fair 2026",
                "linkedin_url": "https://linkedin.com/in/swyx",
                "cohort": "cohort_external_organizers",
                "verification_status": "verified",
            }
        ],
    }
    with open(contacts_file, "w", encoding="utf-8") as f:
        json.dump(mock_contacts, f)

    monkeypatch.setattr(serve, "HUB_DIR", str(tmp_path))

    # Test authorized CSV export for cohort_organizers
    token = serve.ADMIN_SESSION_TOKEN
    handler = MockServerHandler(
        f"/api/admin/contacts/export?cohort=cohort_organizers&format=csv&token={token}"
    )
    handler.do_GET()

    assert handler._response_code == 200
    assert "text/csv" in handler._response_headers["Content-Type"]
    assert "cohort_organizers.csv" in handler._response_headers["Content-Disposition"]

    csv_text = handler.wfile.getvalue().decode("utf-8")
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)

    # Header check
    assert rows[0] == ["Name", "Role", "Company", "Conference", "Social_URL", "Slide_Status", "Verification_Status"]
    assert len(rows) == 3  # Header + 2 organizers

    # Formula injection defense check: leading quote on '=CMD('calc')'
    assert rows[1][0] == "'=CMD('calc')"
    assert rows[2][0] == "Jane Smith"

    # Test JSON export for external organizers
    handler_json = MockServerHandler(
        f"/api/admin/contacts/export?cohort=cohort_external_organizers&format=json&token={token}"
    )
    handler_json.do_GET()

    assert handler_json._response_code == 200
    assert "application/json" in handler_json._response_headers["Content-Type"]
    json_data = json.loads(handler_json.wfile.getvalue().decode("utf-8"))
    assert len(json_data) == 1
    assert json_data[0]["Name"] == "Swyx"
    assert json_data[0]["Conference"] == "AI Engineer World's Fair 2026"


def test_short_link_c_route_redirect():
    handler = MockServerHandler("/c?t=2RB8t.1791234567.a1b2c3d4e5f6")
    handler.do_GET()
    assert handler._response_code == 302
    assert handler._response_headers["Location"] == "/contribute?token=2RB8t.1791234567.a1b2c3d4e5f6"

    handler_no_token = MockServerHandler("/c")
    handler_no_token.do_GET()
    assert handler_no_token._response_code == 302
    assert handler_no_token._response_headers["Location"] == "/contribute"


# =========================================================================
# 7. Cross-Conference Manifest Validation & Ingestion
# =========================================================================
def test_validate_conference_manifest():
    valid_manifest = {
        "conferences": [
            {
                "name": "AI Summit 2026",
                "dates": "2026-10-01",
                "city": "Berlin",
                "website": "https://example.com",
                "schedule_url": "https://example.com/sched",
                "organizers": [{"name": "Organizer 1"}],
            }
        ]
    }
    assert validate_conference_manifest(valid_manifest) == []

    invalid_manifest = {"conferences": [{"name": "Missing Fields Conf"}]}
    errors = validate_conference_manifest(invalid_manifest)
    assert len(errors) >= 3


def test_import_external_conferences(tmp_path):
    manifest_file = tmp_path / "external_conferences.json"
    contacts_file = tmp_path / "contacts.json"
    summary_file = tmp_path / "contacts_summary.json"
    db_file = tmp_path / "outreach_private.sqlite"

    mock_manifest = {
        "conferences": [
            {
                "name": "MCP DevCon Europe 2026",
                "dates": "2026-11-04 - 2026-11-05",
                "city": "London, UK",
                "website": "https://mcpdevcon.org",
                "schedule_url": "https://mcpdevcon2026.sched.com",
                "organizers": [
                    {
                        "name": "Marcus Sterling",
                        "role": "Program Chair",
                        "company": "Agent Systems Lab",
                        "linkedin_url": "https://linkedin.com/in/marcussterling",
                    }
                ],
            }
        ]
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(mock_manifest, f)

    res = import_external_conferences(
        input_path=manifest_file,
        contacts_path=contacts_file,
        summary_path=summary_file,
        db_path=db_file,
    )

    assert res["status"] == "success"
    assert res["newly_imported"] == 1
    assert res["total_external_organizers"] == 1

    with open(contacts_file, encoding="utf-8") as f:
        cdata = json.load(f)
    ext_org = cdata["external_organizers"][0]
    assert ext_org["name"] == "Marcus Sterling"
    assert ext_org["cohort"] == "cohort_external_organizers"
    assert ext_org["source"] == "kimi_swarm"
    assert ext_org["legal_basis"] == "legitimate_interest_opensource_peer"
    assert ext_org["verification_status"] == "verified"


# =========================================================================
# 8. Full Campaign Generation with Verification Suppression
# =========================================================================
def test_campaign_generation_suppresses_suspect_contacts(tmp_path):
    contacts_file = tmp_path / "contacts.json"
    db_file = tmp_path / "outreach_private.sqlite"
    out_dir = tmp_path / "out" / "campaigns"

    mock_contacts = {
        "organizers": [
            {
                "id": "org_verified",
                "name": "Elena Rostova",
                "company": "AI Foundation",
                "linkedin_url": "https://linkedin.com/in/elena-rostova",
                "cohort": "cohort_organizers",
                "verification_status": "verified",
            },
            {
                "id": "org_suspect",
                "name": "Conference Admin",
                "company": "Admin Team",
                "linkedin_url": "https://linkedin.com/in/admin",
                "cohort": "cohort_organizers",
                "verification_status": "suspect",
            },
        ],
        "speakers": [
            {
                "id": "spk_verified",
                "name": "Sam Morrow",
                "cohort": "cohort_missing_slides",
                "linkedin_url": "https://linkedin.com/in/sammorrow",
                "sessions": [{"session_id": "2RB8M", "title": "Building MCP Agents", "has_slides": False}],
                "verification_status": "verified",
            },
            {
                "id": "spk_suspect_no_url",
                "name": "Anonymous Speaker",
                "cohort": "cohort_missing_slides",
                "linkedin_url": None,
                "sessions": [{"session_id": "2RB99", "title": "Secret Talk", "has_slides": False}],
                "verification_status": "suspect",
            },
        ],
        "external_organizers": [
            {
                "id": "org_ext_swyx",
                "name": "Shawn Wang",
                "company": "Smol AI",
                "conference_name": "AI Engineer World's Fair 2026",
                "linkedin_url": "https://linkedin.com/in/swyx",
                "cohort": "cohort_external_organizers",
                "verification_status": "verified",
            }
        ],
    }
    with open(contacts_file, "w", encoding="utf-8") as f:
        json.dump(mock_contacts, f)

    summary = generate_campaign(
        contacts_path=contacts_file,
        db_path=db_file,
        out_dir=out_dir,
        base_url="https://agntcon-demo.vwoosh.com",
    )

    # 1 verified organizer, 1 suspect suppressed
    assert summary["counts"]["cohort_organizers"] == 1
    # 1 verified speaker missing slides, 1 suspect suppressed
    assert summary["counts"]["cohort_missing_slides"] == 1
    # 1 verified external organizer
    assert summary["counts"]["cohort_external_organizers"] == 1
    # 2 total contacts suppressed due to suspect verification
    assert summary["counts"]["suppressed_due_to_verification"] == 2

    # Check that generated files exist
    assert (out_dir / "cohort_organizers.json").exists()
    assert (out_dir / "cohort_missing_slides.json").exists()
    assert (out_dir / "cohort_external_organizers.json").exists()
    assert (out_dir / "cohort_external_organizers.md").exists()
