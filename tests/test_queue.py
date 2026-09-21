"""Tests for active FIFO semaphore queue, telemetry, and capacity boundaries."""

import asyncio
import threading
import time

import httpx
import pytest
import serve
from serve import HubHTTPRequestHandler, ThreadingHTTPServer

TEST_PORT = 8997
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"

@pytest.fixture(scope="module")
def queue_test_server():
    """Spins up a lightweight ThreadingHTTPServer instance for testing."""
    server = ThreadingHTTPServer(("127.0.0.1", TEST_PORT), HubHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.3)
    yield BASE_URL
    server.shutdown()
    server.server_close()

def test_queue_telemetry_endpoint(queue_test_server):
    with httpx.Client() as client:
        res = client.get(f"{queue_test_server}/api/queue-status")
        assert res.status_code == 200
        data = res.json()
        assert "active_tasks" in data
        assert "waiting_tasks" in data
        assert "max_concurrent" in data
        assert data["max_concurrent"] == 2
        assert data["status"] in ("ready", "busy")

def test_queue_capacity_limit_rejection(queue_test_server):
    # Artificially saturate waiting queue
    with serve.QUEUE_LOCK:
        old_waiting = serve.WAITING_TASKS
        serve.WAITING_TASKS = 10

    try:
        with httpx.Client() as client:
            res = client.post(f"{queue_test_server}/api/chat", json={"question": "Burst test"})
            assert res.status_code == 429
            assert res.headers.get("Retry-After") == "15"
            data = res.json()
            assert data.get("error") == "queue_full"
    finally:
        with serve.QUEUE_LOCK:
            serve.WAITING_TASKS = old_waiting

def test_queue_concurrent_semaphore_execution(monkeypatch, queue_test_server):
    # Mock tool_answer_conference with a 0.3s sleep
    async def mock_tool(q, breadth="auto", only_with_slides=False, user_context=None):
        await asyncio.sleep(0.3)
        return {"answer": f"Mock answer for {q}", "citations": []}

    monkeypatch.setattr(serve, "tool_answer_conference", mock_tool)
    import mcp_server
    monkeypatch.setattr(mcp_server, "tool_answer_conference", mock_tool)

    results = []
    def worker(idx):
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{queue_test_server}/api/chat", json={"question": f"Q{idx}"})
            results.append((idx, r.status_code))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 4
    for _idx, status in results:
        assert status == 200
