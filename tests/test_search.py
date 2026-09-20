"""Tests for conference talk search and retrieval."""

from mcp_server import tool_search_talks


def test_search_talks_by_keyword():
    results = tool_search_talks("agent", limit=10)
    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert "id" in first
    assert "title" in first
    assert "sched_url" in first
    assert "speakers" in first

def test_search_talks_only_with_slides():
    all_results = tool_search_talks("orchestration", only_with_slides=False, limit=50)
    slides_results = tool_search_talks("orchestration", only_with_slides=True, limit=50)
    assert len(slides_results) <= len(all_results)
    for r in slides_results:
        assert r.get("has_slides") is True

def test_search_talks_by_topic():
    results = tool_search_talks("", topic="mcp", limit=10)
    assert len(results) > 0
    for r in results:
        concepts = [c.lower() for c in r.get("concepts", [])]
        assert "mcp" in concepts

def test_search_talks_non_existent():
    results = tool_search_talks("xyz999nonexistentgibberishterm12345", limit=10)
    assert isinstance(results, list)
    assert len(results) == 0

def test_search_talks_empty_query():
    results = tool_search_talks("", limit=5)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_ranking_relevance():
    results = tool_search_talks("security red teaming", limit=5)
    assert len(results) > 0
    # Top results should have positive hybrid score
    assert results[0]["hybrid_score"] > 0
