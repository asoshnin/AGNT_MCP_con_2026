"""
Unit & Integration Tests for Assistant Resilience, Gateway Timeouts and UX Hardening.
Tests DOM-01, DOM-02, SEC-01, CLA-01 invariants.
"""
import inspect
import json
import pytest
import os
import sys

# Ensure 02_public_hub is in path
HUB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HUB_DIR not in sys.path:
    sys.path.insert(0, HUB_DIR)

import mcp_server


def test_gateway_per_provider_timeout_budget():
    """Verify that per-provider timeout in mcp_server is <= 20.0s (DOM-01)."""
    source = inspect.getsource(mcp_server.tool_answer_conference)
    assert "timeout=18.0" in source or "timeout=20.0" in source, "Per-provider timeout must be bounded to <= 20s"


def test_fallback_citations_precomputed_for_evaluation_query():
    """Verify that tool_search_talks retrieves relevant talks for evals query."""
    res = mcp_server.tool_search_talks("evals and benchmarking", limit=3)
    assert len(res) > 0, "Should match conference talks on evaluations"
    first = res[0]
    assert "id" in first
    assert "title" in first
    assert "sched_url" in first


def test_defensive_frontend_script_contains_resilience_card():
    """Verify that app.js contains defensive JSON parsing and resilience card."""
    app_js_path = os.path.join(HUB_DIR, "site", "assets", "app.js")
    with open(app_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "renderResilienceCard" in content, "Must implement renderResilienceCard"
    assert "retryLastChatQuestion" in content, "Must implement retryLastChatQuestion"
    assert "lastSubmittedQuestion" in content, "Must store lastSubmittedQuestion state"
    assert "JSON.parse(rawText)" in content, "Must safely parse rawText"
    assert "Is serve.py running?" not in content, "Must not display confusing dev error"
