import pytest

from app.config import load_config


def test_load_config_reads_env(monkeypatch):
    monkeypatch.setenv("MILVUS_HOST", "127.0.0.1")
    monkeypatch.setenv("MILVUS_PORT", "19530")
    monkeypatch.setenv("MILVUS_USERNAME", "test_user")
    monkeypatch.setenv("MILVUS_PASSWORD", "")
    monkeypatch.setenv("MILVUS_COLLECTION", "agent_vectors")
    monkeypatch.setenv("MILVUS_PARTITION", "")
    monkeypatch.setenv("MILVUS_DB_NAME", "default")

    monkeypatch.setenv("MEM0_SERVER_URL", "http://localhost:8888")
    monkeypatch.setenv("MEM0_API_KEY", "mem0_key")
    monkeypatch.setenv("MEM0_USER_ID", "user_001")

    monkeypatch.setenv("LLM_API_KEY", "llm_key")
    monkeypatch.setenv("LLM_ENDPOINT", "http://llm.local")
    monkeypatch.setenv("LLM_MODEL", "gpt-test")
    monkeypatch.setenv("LLM_TIMEOUT", "45")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.2")

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "lf_pub")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "lf_sec")
    monkeypatch.setenv("LANGFUSE_HOST", "http://langfuse.local")
    monkeypatch.setenv("LANGFUSE_ENV", "test")

    monkeypatch.setenv("MCP_TRANSPORT", "stdio")
    monkeypatch.setenv("MCP_SERVER_URL", "http://mcp.local")
    monkeypatch.setenv("MCP_TOOL_NAME", "echo")
    monkeypatch.setenv("MCP_API_KEY", "mcp_key")
    monkeypatch.setenv("MCP_COMMAND", "python")
    monkeypatch.setenv("MCP_ARGS", "--foo bar --baz=1")

    monkeypatch.setenv("CHECKPOINT_BACKEND", "memory")
    monkeypatch.setenv("CHECKPOINT_PATH", "/tmp/checkpoints")

    config = load_config()

    assert config.milvus.host == "127.0.0.1"
    assert config.milvus.port == 19530
    assert config.milvus.username == "test_user"
    assert config.milvus.password is None
    assert config.milvus.collection == "agent_vectors"
    assert config.milvus.partition is None
    assert config.milvus.db_name == "default"

    assert config.mem0.server_url == "http://localhost:8888"
    assert config.mem0.api_key == "mem0_key"
    assert config.mem0.user_id == "user_001"

    assert config.llm.api_key == "llm_key"
    assert config.llm.endpoint == "http://llm.local"
    assert config.llm.model == "gpt-test"
    assert config.llm.timeout == 45
    assert config.llm.temperature == 0.2

    assert config.langfuse.public_key == "lf_pub"
    assert config.langfuse.secret_key == "lf_sec"
    assert config.langfuse.host == "http://langfuse.local"
    assert config.langfuse.env == "test"

    assert config.mcp.transport == "stdio"
    assert config.mcp.server_url == "http://mcp.local"
    assert config.mcp.tool_name == "echo"
    assert config.mcp.api_key == "mcp_key"
    assert config.mcp.command == "python"
    assert config.mcp.args == ["--foo", "bar", "--baz=1"]

    assert config.checkpoint.backend == "memory"
    assert config.checkpoint.path == "/tmp/checkpoints"


def test_get_env_invalid_cast(monkeypatch):
    from app import config as config_module

    monkeypatch.setenv("BAD_INT", "nope")

    with pytest.raises(ValueError):
        config_module._get_env("BAD_INT", cast=int)


def test_parse_args_handles_none():
    from app import config as config_module

    assert config_module._parse_args(None) == []
