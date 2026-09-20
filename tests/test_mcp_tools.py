"""Deterministic tests for all 8 Model Context Protocol (MCP) tools."""

import asyncio

import httpx
from mcp_server import (
    tool_answer_conference,
    tool_get_conference_profile,
    tool_get_page,
    tool_get_queue_status,
    tool_get_talk,
    tool_list_concepts,
    tool_list_talks,
    tool_search_talks,
)


def test_tool_01_search_talks():
    res = tool_search_talks("agent", limit=5)
    assert isinstance(res, list)
    assert len(res) > 0
    assert "id" in res[0]
    assert "title" in res[0]

def test_tool_02_get_page():
    # Source page test
    src = tool_get_page("source", "2RBBJ")
    if "error" not in src:
        assert src["name"] == "2RBBJ"
        assert "content" in src
        assert "sched_url" in src

    # Concept page test
    concept = tool_get_page("concept", "mcp")
    if "error" not in concept:
        assert "content" in concept

    # Invalid page type error handling
    invalid = tool_get_page("unknown_type", "2RBBJ")
    assert "error" in invalid

def test_tool_03_answer_conference_offline_fallback(monkeypatch):
    # Test answer_conference without network calls (deterministic offline verification)
    # Clear gateway keys for deterministic offline capacity response
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("KILOCODE_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    res = asyncio.run(tool_answer_conference("What is MCP?", breadth="focused"))
    assert isinstance(res, dict)
    assert res.get("error") == "gateway_busy"
    assert "citations" in res
    assert len(res["citations"]) > 0
    assert "sched_url" in res["citations"][0]

def test_tool_03_answer_conference_mocked_success(monkeypatch):
    # Test answer_conference when a free endpoint succeeds
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock_free_key")

    class MockResponse:
        status_code = 200
        def json(self):
            return {
                "choices": [{
                    "message": {
                        "content": "MCP (Model Context Protocol) is the open standard [2RBBJ] for AI tools."
                    }
                }]
            }

    async def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    res = asyncio.run(tool_answer_conference("What is MCP?", breadth="focused"))
    assert isinstance(res, dict)
    assert "error" not in res
    assert "MCP" in res.get("answer", "")
    assert len(res.get("citations", [])) > 0

def test_tool_04_get_talk():
    # Known talk
    talk = tool_get_talk("2RBBJ")
    if "error" not in talk:
        assert talk["id"] == "2RBBJ"
        assert "title" in talk
        assert "speakers" in talk

    # Non-existent talk
    missing = tool_get_talk("NON_EXISTENT_ID_999")
    assert "error" in missing

def test_tool_05_list_talks():
    talks = tool_list_talks(limit=10, offset=0)
    assert isinstance(talks, list)
    assert len(talks) <= 10
    if len(talks) > 0:
        assert "id" in talks[0]
        assert "title" in talks[0]

    # Test pagination
    talks_p2 = tool_list_talks(limit=5, offset=5)
    assert isinstance(talks_p2, list)

def test_tool_06_list_concepts():
    concepts = tool_list_concepts()
    assert isinstance(concepts, list)
    if len(concepts) > 0:
        assert "slug" in concepts[0]
        assert "title" in concepts[0]
        assert "path" in concepts[0]

def test_tool_07_get_conference_profile():
    prof = tool_get_conference_profile()
    assert isinstance(prof, dict)
    assert "conference_name" in prof
    assert "AGNTCon" in prof["conference_name"]

def test_tool_08_get_queue_status():
    status = tool_get_queue_status()
    assert isinstance(status, dict)
    assert "active_tasks" in status
    assert "waiting_tasks" in status
    assert "max_concurrent" in status
    assert status["max_concurrent"] == 2
    assert status["status"] in ("ready", "busy")
