#!/usr/bin/env python3
"""Isolated PDF extraction and security screening worker.
Runs in a memory-bounded subprocess (RLIMIT_AS=512MB), enforces max page limit (120),
validates magic bytes (%PDF-), and scans for adversarial prompt injection patterns.
"""

import json
import os
import re
import sys

# Cross-platform resource limit guard (RLIMIT_AS=512MB)
if sys.platform != "win32":
    try:
        import resource
        limit_bytes = 512 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
    except Exception:
        pass

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt\s*:",
    r"<\s*system\s*>",
    r"you\s+are\s+now\s+(an?\s+)?(unrestricted|evil|admin)",
    r"override\s+system\s+directive",
    r"repeat\s+the\s+secret\s+key",
    r"disregard\s+(all\s+)?prior\s+prompts",
]


def extract_and_scan(pdf_path: str, max_pages: int = 120) -> dict:
    if not os.path.exists(pdf_path):
        return {"error": "File not found", "status": "quarantined"}

    # 1. Magic bytes validation (%PDF-)
    try:
        with open(pdf_path, "rb") as f:
            header = f.read(5)
            if header != b"%PDF-":
                return {
                    "error": "Invalid PDF magic bytes: file does not start with %PDF-",
                    "status": "quarantined",
                }
    except Exception as e:
        return {"error": f"Failed to read file header: {e}", "status": "quarantined"}

    if PdfReader is None:
        return {"error": "pypdf library is not installed", "status": "quarantined"}

    # 2. Extract text with page ceiling and no JS
    try:
        reader = PdfReader(pdf_path, strict=False)
        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)

        extracted_text = []
        for idx in range(pages_to_read):
            page = reader.pages[idx]
            text = page.extract_text() or ""
            extracted_text.append(text)

        full_text = "\n".join(extracted_text)
    except Exception as e:
        return {
            "error": f"PDF parsing error: {e}",
            "status": "quarantined",
        }

    # 3. Prompt Injection Heuristic Scan
    matched_patterns = []
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, full_text, flags=re.IGNORECASE):
            matched_patterns.append(pattern)

    risk_score = "critical" if len(matched_patterns) > 1 else ("warning" if len(matched_patterns) == 1 else "clean")
    text_yield = len(full_text.strip())

    return {
        "status": "quarantined" if risk_score == "critical" else "ok",
        "page_count": total_pages,
        "text_yield_chars": text_yield,
        "ocr_required": text_yield < 200,
        "injection_risk_score": risk_score,
        "injection_details": json.dumps(matched_patterns) if matched_patterns else None,
        "sample_text": full_text[:4000],
    }


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: extract_pdf_worker.py <path_to_pdf> [max_pages]\n")
        sys.exit(1)

    pdf_file = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 120

    res = extract_and_scan(pdf_file, max_pages=max_pages)
    print(json.dumps(res))
    if res.get("status") == "quarantined":
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
