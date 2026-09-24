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


def test_corpus_driven_compound_word_segmentation():
    """Verify that segment_compound_term splits redteaming into ['red', 'teaming']."""
    vocab = mcp_server.CONFERENCE_VOCAB
    assert len(vocab) > 500, "Corpus vocab should contain >500 terms"
    assert "red" in vocab
    assert "teaming" in vocab
    
    seg = mcp_server.segment_compound_term("redteaming", vocab)
    assert seg == ["red", "teaming"], f"Expected ['red', 'teaming'] but got {seg}"


def test_tool_search_talks_matches_redteaming_compound_term():
    """Verify that search query 'redteaming' matches talk 2RBBJ."""
    results = mcp_server.tool_search_talks("redteaming", limit=5)
    matched_ids = [r["id"] for r in results]
    assert "2RBBJ" in matched_ids, f"2RBBJ should be found in {matched_ids}"
    # Top match should be 2RBBJ
    assert results[0]["id"] == "2RBBJ", f"2RBBJ should be top match, got {results[0]['id']}"


def test_system_prompt_softened_rule_3():
    """Verify that system_prompt does not contain the rigid binary refusal."""
    source = inspect.getsource(mcp_server.tool_answer_conference)
    assert 'analyze closely related architectural, security' in source
    assert 'If the topic was not discussed in the provided excerpts, state: "This topic was not covered' not in source


def test_app_js_session_persistence_and_target_blank():
    """Verify that app.js implements sessionStorage persistence and target=_blank."""
    app_js_path = os.path.join(HUB_DIR, "site", "assets", "app.js")
    with open(app_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "agntcon_chat_history_v2" in content
    assert "saveChatToSession" in content
    assert "restoreChatFromSession" in content
    assert 'a.target = "_blank"' in content
    assert 'a.rel = "noopener noreferrer"' in content
