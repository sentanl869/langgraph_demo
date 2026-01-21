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
            backend="memory",
            path=None,
        ),
    )


def test_run_agent_returns_empty_for_non_dict(monkeypatch):
    class DummyApp:
        def invoke(self, _state, config=None):
            return ["not-a-dict"]

    class DummyGraph:
        def compile(self, checkpointer=None):
            return DummyApp()

    monkeypatch.setattr("app.graph.build_graph", lambda *_args, **_kwargs: DummyGraph())
    monkeypatch.setattr("app.graph.build_checkpointer", lambda _cfg: None)

    result = run_agent({"prompt": "hi"}, config=_config(), thread_id="t1")

    assert result == {}
