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
            public_key=None,
            secret_key=None,
            host=None,
            env=None,
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
            backend=None,
            path=None,
        ),
    )


def test_graph_runs_in_order():
    order = []

    def _make_node(name):
        def _node(_state):
            order.append(name)
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

    app.invoke({"prompt": "hi"})

    assert order == ["llm", "mem0", "milvus", "mcp", "final"]
