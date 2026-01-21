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


def test_graph_default_nodes_use_state(monkeypatch):
    seen = {}

    def _fake_llm(prompt, *, config, system_prompt=None):
        seen["llm"] = {"prompt": prompt, "config": config, "system": system_prompt}
        return {"status": "success", "output_text": "llm-output"}

    def _fake_mem0(content, query, *, config):
        seen["mem0"] = {"content": content, "query": query, "config": config}
        return {"status": "success", "memory_id": "m1", "query_result": {}}

    def _fake_milvus(vector, *, config, query_vector=None, top_k=3):
        seen["milvus"] = {
            "vector": vector,
            "query_vector": query_vector,
            "config": config,
            "top_k": top_k,
        }
        return {"status": "success", "write_id": "v1", "query_result": {}}

    def _fake_mcp(tool_args, *, config, tool_name=None):
        seen["mcp"] = {"tool_args": tool_args, "config": config, "tool_name": tool_name}
        return {"status": "success", "tool_name": "echo", "tool_result": {}}

    monkeypatch.setattr("app.graph.run_llm_node", _fake_llm)
    monkeypatch.setattr("app.graph.run_mem0_node", _fake_mem0)
    monkeypatch.setattr("app.graph.run_milvus_node", _fake_milvus)
    monkeypatch.setattr("app.graph.run_mcp_node", _fake_mcp)

    app = build_graph(_config()).compile()
    state = app.invoke(
        {
            "prompt": "hello",
            "mem0_query": "what was said?",
            "milvus_query_vector": [0.9, 0.1],
            "mcp_tool_args": {"text": "hi"},
        }
    )

    assert seen["llm"]["prompt"] == "hello"
    assert seen["mem0"]["content"] == "llm-output"
    assert seen["mem0"]["query"] == "what was said?"
    assert seen["milvus"]["vector"] == [0.1, 0.2, 0.3]
    assert seen["milvus"]["query_vector"] == [0.9, 0.1]
    assert seen["mcp"]["tool_args"] == {"text": "hi"}
    assert state["result"]["llm"]["output_text"] == "llm-output"
