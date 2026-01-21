import json

from app.config import (
    AppConfig,
    CheckpointConfig,
    LangfuseConfig,
    LLMConfig,
    MCPConfig,
    Mem0Config,
    MilvusConfig,
)
from app.main import main


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


def test_main_invokes_run_agent(monkeypatch):
    called = {}

    def _fake_run_agent(initial_state, *, config, thread_id=None):
        called["state"] = initial_state
        called["config"] = config
        called["thread_id"] = thread_id
        return {"ok": True}

    monkeypatch.setattr("app.main.load_config", _config)
    monkeypatch.setattr("app.main.run_agent", _fake_run_agent)

    result = main(
        [
            "--prompt",
            "hello",
            "--mem0-query",
            "what did I say?",
            "--mcp-args",
            json.dumps({"text": "hi"}),
        ]
    )

    assert called["state"]["prompt"] == "hello"
    assert called["state"]["mem0_query"] == "what did I say?"
    assert called["state"]["mcp_tool_args"] == {"text": "hi"}
    assert result == {"ok": True}
