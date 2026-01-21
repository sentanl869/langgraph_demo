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


def test_graph_returns_structured_result():
    llm_result = {"status": "success", "model": "m1", "output_text": "ok"}
    mem0_result = {"status": "success", "memory_id": "m1", "query_result": {}}
    milvus_result = {"status": "success", "write_id": "v1", "query_result": {}}
    mcp_result = {"status": "success", "tool_name": "echo", "tool_result": {}}

    graph = build_graph(
        _config(),
        node_overrides={
            "llm": lambda _state: {"llm": llm_result},
            "mem0": lambda _state: {"mem0": mem0_result},
            "milvus": lambda _state: {"milvus": milvus_result},
            "mcp": lambda _state: {"mcp": mcp_result},
        },
    )
    app = graph.compile()

    state = app.invoke({"prompt": "hi"})

    assert state["result"] == {
        "llm": llm_result,
        "mem0": mem0_result,
        "milvus": milvus_result,
        "mcp": mcp_result,
    }
