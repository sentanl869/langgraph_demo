from app.config import (
    AppConfig,
    CheckpointConfig,
    LangfuseConfig,
    LLMConfig,
    MCPConfig,
    Mem0Config,
    MilvusConfig,
)
from app.graph import build_graph
from app.observability.langfuse import get_langfuse_trace


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
            env="dev",
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


def test_langgraph_dev_trace_created_from_config(monkeypatch):
    calls: dict[str, object] = {}

    def _fake_start_trace(*, config, trace_name, metadata):
        calls["trace_args"] = {
            "config": config,
            "trace_name": trace_name,
            "metadata": metadata,
        }
        return "trace-obj"

    monkeypatch.setattr("app.observability.langfuse.start_langfuse_trace", _fake_start_trace)

    def _make_node(name):
        def _node(_state):
            calls.setdefault("trace_in_node", get_langfuse_trace())
            if name == "final":
                return {"result": {"status": "success"}}
            return {name: {"status": "success"}}

        return _node

    graph = build_graph(
        _config(),
        node_overrides={
            "llm": _make_node("llm"),
            "mem0": _make_node("mem0"),
            "milvus": _make_node("milvus"),
            "mcp": _make_node("mcp"),
            "final": _make_node("final"),
        },
    )
    app = graph.compile()
    app.invoke({"prompt": "hi"}, config={"configurable": {"thread_id": "dev-1"}})

    assert calls["trace_args"]["trace_name"] == "agent-run"
    assert calls["trace_args"]["metadata"] == {"thread_id": "dev-1"}
    assert calls["trace_in_node"] == "trace-obj"
    assert get_langfuse_trace() is None
