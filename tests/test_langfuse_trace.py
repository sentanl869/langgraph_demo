from types import SimpleNamespace

from app.config import LangfuseConfig
from app.observability.langfuse import run_langfuse_trace


def test_langfuse_trace_success(monkeypatch):
    expected = {}
    span = SimpleNamespace(id="span-123")

    class FakeTrace:
        id = "trace-456"

        def span(self, **kwargs):
            expected["span"] = kwargs
            return span

    class FakeLangfuse:
        def __init__(self, public_key, secret_key, host):
            expected["init"] = {
                "public_key": public_key,
                "secret_key": secret_key,
                "host": host,
            }

        def trace(self, **kwargs):
            expected["trace"] = kwargs
            return FakeTrace()

    monkeypatch.setattr("app.observability.langfuse.Langfuse", FakeLangfuse)

    config = LangfuseConfig(
        public_key="pk",
        secret_key="sk",
        host="http://langfuse.local",
        env="test",
    )

    result = run_langfuse_trace(
        config=config,
        trace_name="agent-run",
        span_name="milvus",
        metadata={"run_id": "r1"},
        span_metadata={"node": "milvus"},
    )

    assert expected["init"] == {
        "public_key": "pk",
        "secret_key": "sk",
        "host": "http://langfuse.local",
    }
    assert expected["trace"] == {
        "name": "agent-run",
        "metadata": {"env": "test", "run_id": "r1"},
    }
    assert expected["span"] == {
        "name": "milvus",
        "metadata": {"node": "milvus"},
    }
    assert result == {
        "status": "success",
        "trace_id": "trace-456",
        "span_id": "span-123",
    }


def test_langfuse_trace_failure(monkeypatch):
    def _fake_langfuse(*_args, **_kwargs):
        raise RuntimeError("langfuse down")

    monkeypatch.setattr("app.observability.langfuse.Langfuse", _fake_langfuse)

    config = LangfuseConfig(
        public_key="pk",
        secret_key="sk",
        host="http://langfuse.local",
        env=None,
    )

    result = run_langfuse_trace(
        config=config,
        trace_name="agent-run",
        span_name="milvus",
    )

    assert result["status"] == "failed"
    assert result["trace_id"] is None
    assert result["span_id"] is None
    assert "langfuse down" in result["error"]
