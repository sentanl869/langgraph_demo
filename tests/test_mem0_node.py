from app.config import Mem0Config
from app.nodes.mem0 import run_mem0_node


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_mem0_node_success(monkeypatch):
    calls = []

    def _fake_post(url, json, headers):
        calls.append({"url": url, "json": json, "headers": headers})
        if url.endswith("/memories/"):
            return FakeResponse({"id": "mem-123"})
        if url.endswith("/search/"):
            return FakeResponse({"results": ["hotpot"]})
        raise AssertionError(f"Unexpected url: {url}")

    monkeypatch.setattr("app.nodes.mem0.requests.post", _fake_post)

    config = Mem0Config(
        server_url="http://mem0.local",
        api_key="mem0_key",
        user_id="user-1",
    )

    result = run_mem0_node(
        "I love hotpot on Fridays",
        "What do I love?",
        config=config,
    )

    assert calls == [
        {
            "url": "http://mem0.local/memories/",
            "json": {
                "messages": [{"role": "user", "content": "I love hotpot on Fridays"}],
                "user_id": "user-1",
            },
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Token mem0_key",
            },
        },
        {
            "url": "http://mem0.local/search/",
            "json": {
                "query": "What do I love?",
                "user_id": "user-1",
            },
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Token mem0_key",
            },
        },
    ]
    assert result == {
        "status": "success",
        "memory_id": "mem-123",
        "query_result": {"results": ["hotpot"]},
    }


def test_mem0_node_failure(monkeypatch):
    def _fake_post(*_args, **_kwargs):
        raise RuntimeError("mem0 down")

    monkeypatch.setattr("app.nodes.mem0.requests.post", _fake_post)

    config = Mem0Config(
        server_url="http://mem0.local",
        api_key="mem0_key",
        user_id="user-1",
    )

    result = run_mem0_node(
        "I love hotpot on Fridays",
        "What do I love?",
        config=config,
    )

    assert result["status"] == "failed"
    assert result["memory_id"] is None
    assert result["query_result"] is None
    assert "mem0 down" in result["error"]
