from types import SimpleNamespace

from app.config import (
    AppConfig,
    CheckpointConfig,
    LangfuseConfig,
    LLMConfig,
    MCPConfig,
    Mem0Config,
    MilvusConfig,
)
from app.graph import run_agent


def _config():
    return AppConfig(
        milvus=MilvusConfig(
            host=None,
            port=None,
            username=None,
            password=None,
            collection="test_collection",
            partition=None,
            db_name=None,
        ),
        mem0=Mem0Config(
            server_url=None,
            api_key=None,
            user_id="user-1",
        ),
        llm=LLMConfig(
            api_key=None,
            endpoint=None,
            model="gpt-test",
            timeout=None,
            temperature=None,
        ),
        langfuse=LangfuseConfig(
            public_key="pk",
            secret_key="sk",
            host="http://langfuse.local",
            env="test",
        ),
        mcp=MCPConfig(
            transport=None,
            server_url=None,
            tool_name="echo",
            api_key=None,
            command=None,
            args=[],
        ),
        checkpoint=CheckpointConfig(
            backend="memory",
            path=None,
        ),
    )


def test_run_agent_creates_langfuse_trace_and_spans(monkeypatch):
    calls: dict[str, object] = {"spans": []}

    class FakeSpan(SimpleNamespace):
        def end(self, **_kwargs):
            return None

    class FakeTrace:
        id = "trace-123"

        def span(self, **kwargs):
            calls["spans"].append(kwargs)
            return FakeSpan(id=f"span-{len(calls['spans'])}")

    class FakeLangfuse:
        def __init__(self, public_key, secret_key, host):
            calls["init"] = {
                "public_key": public_key,
                "secret_key": secret_key,
                "host": host,
            }

        def trace(self, **kwargs):
            calls["trace"] = kwargs
            return FakeTrace()

    monkeypatch.setattr("app.observability.langfuse.Langfuse", FakeLangfuse)

    llm_result = {"status": "success", "model": "m1", "output_text": "ok"}
    mem0_result = {"status": "success", "memory_id": "m1", "query_result": {}}
    milvus_result = {"status": "success", "write_id": "v1", "query_result": {}}
    mcp_result = {"status": "success", "tool_name": "echo", "tool_result": {}}

    result = run_agent(
        {"prompt": "hi"},
        config=_config(),
        thread_id="t1",
        node_overrides={
            "llm": lambda _state: {"llm": llm_result},
            "mem0": lambda _state: {"mem0": mem0_result},
            "milvus": lambda _state: {"milvus": milvus_result},
            "mcp": lambda _state: {"mcp": mcp_result},
        },
    )

    assert calls["init"] == {
        "public_key": "pk",
        "secret_key": "sk",
        "host": "http://langfuse.local",
    }
    assert calls["trace"] == {
        "name": "agent-run",
        "metadata": {"env": "test", "thread_id": "t1"},
    }

    span_names = [span["name"] for span in calls["spans"]]
    assert span_names[:4] == ["llm", "mem0", "milvus", "mcp"]
    for span in calls["spans"]:
        assert span["metadata"]["node"] in {"llm", "mem0", "milvus", "mcp", "final"}

    assert result == {
        "llm": llm_result,
        "mem0": mem0_result,
        "milvus": milvus_result,
        "mcp": mcp_result,
    }
