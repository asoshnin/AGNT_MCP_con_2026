"""Unit tests for sandboxed subprocess PDF extractor worker."""

import json
import subprocess
import sys

from pypdf import PdfWriter


def create_minimal_pdf(dest_path: str, text: str = "Hello world from AGNTCon 2026 slides."):
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    # PyPDF blank page is valid PDF
    with open(dest_path, "wb") as f:
        writer.write(f)


def test_extract_worker_invalid_magic_bytes(tmp_path):
    fake_pdf = tmp_path / "bad.pdf"
    fake_pdf.write_bytes(b"NOT_A_PDF_FILE")

    cmd = [sys.executable, "02_public_hub/scripts/extract_pdf_worker.py", str(fake_pdf)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 2
    res = json.loads(proc.stdout)
    assert res["status"] == "quarantined"
    assert "Invalid PDF magic bytes" in res["error"]


def test_extract_worker_valid_pdf(tmp_path):
    valid_pdf = tmp_path / "valid.pdf"
    create_minimal_pdf(str(valid_pdf), "Safe conference presentation text")

    cmd = [sys.executable, "02_public_hub/scripts/extract_pdf_worker.py", str(valid_pdf)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    res = json.loads(proc.stdout)
    assert res["status"] == "ok"
    assert res["page_count"] == 1
    assert res["injection_risk_score"] == "clean"
