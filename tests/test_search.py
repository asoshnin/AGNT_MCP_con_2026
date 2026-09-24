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


def test_search_speaker_entity_boosting():
    # Conversational natural query asking for a speaker's presentation
    results = tool_search_talks("what's your takeaway from Dylan Ratcliffe's presentation?", limit=5)
    assert len(results) > 0
    # Dylan Ratcliffe (2RB8Y) MUST be the #1 result
    assert results[0]["id"] == "2RB8Y"
    assert "Dylan Ratcliffe" in results[0]["speakers"]


def test_search_session_id_boosting():
    results = tool_search_talks("tell me about 2RB8Y", limit=5)
    assert len(results) > 0
    assert results[0]["id"] == "2RB8Y"


def test_search_conversational_stop_words_fallback():
    # If a query is only stop words, fallback gracefully without crash
    results = tool_search_talks("what is it", limit=5)
    assert isinstance(results, list)
    assert len(results) > 0

