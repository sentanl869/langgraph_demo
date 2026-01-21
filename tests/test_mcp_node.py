from app.config import MCPConfig
from app.nodes.mcp import run_mcp_node


def test_mcp_node_success(monkeypatch):
    expected = {}

    def _fake_call(tool_name, tool_args, config):
        expected["tool_name"] = tool_name
        expected["tool_args"] = tool_args
        expected["config"] = config
        return {"ok": True}

    monkeypatch.setattr("app.nodes.mcp._call_mcp_tool", _fake_call)

    config = MCPConfig(
        transport="stdio",
        server_url="http://mcp.local",
        tool_name="echo",
        api_key="mcp_key",
        command="python",
        args=["-m", "server"],
    )

    result = run_mcp_node({"text": "hi"}, config=config)

    assert expected["tool_name"] == "echo"
    assert expected["tool_args"] == {"text": "hi"}
    assert expected["config"] == config
    assert result == {
        "status": "success",
        "tool_name": "echo",
        "tool_result": {"ok": True},
    }


def test_mcp_node_failure(monkeypatch):
    def _fake_call(*_args, **_kwargs):
        raise RuntimeError("mcp down")

    monkeypatch.setattr("app.nodes.mcp._call_mcp_tool", _fake_call)

    config = MCPConfig(
        transport="stdio",
        server_url="http://mcp.local",
        tool_name="echo",
        api_key="mcp_key",
        command="python",
        args=["-m", "server"],
    )

    result = run_mcp_node({"text": "hi"}, config=config)

    assert result["status"] == "failed"
    assert result["tool_name"] == "echo"
    assert result["tool_result"] is None
    assert "mcp down" in result["error"]
