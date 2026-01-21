import asyncio
import sys
import types

import pytest

from app.config import MCPConfig
from app.nodes import mcp as mcp_module


def test_build_headers():
    assert mcp_module._build_headers(None) == {}
    assert mcp_module._build_headers("key") == {"Authorization": "Bearer key"}


def test_run_async_returns_value():
    async def _coro():
        return "ok"

    assert mcp_module._run_async(_coro()) == "ok"


@pytest.mark.anyio
async def test_run_async_rejects_running_loop():
    coro = asyncio.sleep(0)
    with pytest.raises(RuntimeError):
        mcp_module._run_async(coro)
    coro.close()


def test_load_clients():
    stdio = mcp_module._load_stdio_client()
    sse = mcp_module._load_sse_client()
    http = mcp_module._load_http_client()

    assert len(stdio) == 3
    assert len(sse) == 2
    assert len(http) == 2


def test_load_sse_client_import_error(monkeypatch):
    fake_sse = types.ModuleType("mcp.client.sse")
    monkeypatch.setitem(sys.modules, "mcp.client.sse", fake_sse)

    with pytest.raises(RuntimeError):
        mcp_module._load_sse_client()


def test_load_sse_client_fallback_error(monkeypatch):
    fake_sse = types.ModuleType("mcp.client.sse")
    monkeypatch.setitem(sys.modules, "mcp.client.sse", fake_sse)

    fake_sse_client = types.ModuleType("mcp.client.sse_client")

    def _dummy_client(*_args, **_kwargs):
        return None

    fake_sse_client.sse_client = _dummy_client
    monkeypatch.setitem(sys.modules, "mcp.client.sse_client", fake_sse_client)

    with pytest.raises(RuntimeError):
        mcp_module._load_sse_client()


def test_load_http_client_import_error(monkeypatch):
    fake_streamable = types.ModuleType("mcp.client.streamable_http")
    monkeypatch.setitem(sys.modules, "mcp.client.streamable_http", fake_streamable)

    with pytest.raises(RuntimeError):
        mcp_module._load_http_client()


def test_load_http_client_fallback(monkeypatch):
    fake_streamable = types.ModuleType("mcp.client.streamable_http")
    monkeypatch.setitem(sys.modules, "mcp.client.streamable_http", fake_streamable)

    fake_http = types.ModuleType("mcp.client.http")

    def _dummy_http_client(*_args, **_kwargs):
        return None

    fake_http.http_client = _dummy_http_client
    monkeypatch.setitem(sys.modules, "mcp.client.http", fake_http)

    client_session, http_client = mcp_module._load_http_client()
    assert http_client is _dummy_http_client


def test_call_mcp_tool_async_stdio(monkeypatch):
    seen = {}

    class FakeParams:
        def __init__(self, command, args):
            seen["params"] = {"command": command, "args": args}

    class FakeSession:
        def __init__(self, _read, _write):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def initialize(self):
            seen["init"] = True

        async def call_tool(self, name, args):
            return {"name": name, "args": args}

    class FakeClient:
        def __init__(self, _params):
            pass

        async def __aenter__(self):
            return ("read", "write")

        async def __aexit__(self, exc_type, exc, tb):
            return None

    def _fake_stdio_client(params):
        return FakeClient(params)

    monkeypatch.setattr(
        mcp_module,
        "_load_stdio_client",
        lambda: (FakeSession, FakeParams, _fake_stdio_client),
    )

    config = MCPConfig(
        transport="stdio",
        server_url=None,
        tool_name="echo",
        api_key=None,
        command="python",
        args=["-m", "server"],
    )

    result = asyncio.run(
        mcp_module._call_mcp_tool_async("echo", {"text": "hi"}, config)
    )

    assert seen["params"] == {"command": "python", "args": ["-m", "server"]}
    assert result == {"name": "echo", "args": {"text": "hi"}}


def test_call_mcp_tool_async_http(monkeypatch):
    seen = {}

    class FakeSession:
        def __init__(self, _read, _write):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def initialize(self):
            seen["init"] = True

        async def call_tool(self, name, args):
            return {"name": name, "args": args}

    class FakeClient:
        def __init__(self, _url, headers=None):
            seen["headers"] = headers

        async def __aenter__(self):
            return ("read", "write")

        async def __aexit__(self, exc_type, exc, tb):
            return None

    def _fake_client(url, headers=None):
        return FakeClient(url, headers=headers)

    monkeypatch.setattr(
        mcp_module,
        "_load_http_client",
        lambda: (FakeSession, _fake_client),
    )

    config = MCPConfig(
        transport="http",
        server_url="http://mcp.local",
        tool_name="echo",
        api_key="token",
        command=None,
        args=[],
    )

    result = asyncio.run(
        mcp_module._call_mcp_tool_async("echo", {"text": "hi"}, config)
    )

    assert seen["headers"] == {"Authorization": "Bearer token"}
    assert result["name"] == "echo"


def test_call_mcp_tool_async_sse(monkeypatch):
    class FakeSession:
        def __init__(self, _read, _write):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def initialize(self):
            return None

        async def call_tool(self, name, args):
            return {"name": name, "args": args}

    class FakeClient:
        def __init__(self, _url, headers=None):
            pass

        async def __aenter__(self):
            return ("read", "write")

        async def __aexit__(self, exc_type, exc, tb):
            return None

    def _fake_client(url, headers=None):
        return FakeClient(url, headers=headers)

    monkeypatch.setattr(
        mcp_module,
        "_load_sse_client",
        lambda: (FakeSession, _fake_client),
    )

    config = MCPConfig(
        transport="sse",
        server_url="http://mcp.local",
        tool_name="echo",
        api_key=None,
        command=None,
        args=[],
    )

    result = asyncio.run(
        mcp_module._call_mcp_tool_async("echo", {"text": "hi"}, config)
    )

    assert result["args"] == {"text": "hi"}


def test_call_mcp_tool_async_errors():
    config = MCPConfig(
        transport="stdio",
        server_url=None,
        tool_name="echo",
        api_key=None,
        command=None,
        args=[],
    )
    with pytest.raises(ValueError):
        asyncio.run(mcp_module._call_mcp_tool_async("echo", {}, config))

    config = MCPConfig(
        transport="http",
        server_url=None,
        tool_name="echo",
        api_key=None,
        command=None,
        args=[],
    )
    with pytest.raises(ValueError):
        asyncio.run(mcp_module._call_mcp_tool_async("echo", {}, config))

    config = MCPConfig(
        transport="unknown",
        server_url=None,
        tool_name="echo",
        api_key=None,
        command=None,
        args=[],
    )
    with pytest.raises(ValueError):
        asyncio.run(mcp_module._call_mcp_tool_async("echo", {}, config))


def test_call_mcp_tool_uses_run_async(monkeypatch):
    seen = {}

    def _fake_run_async(coro):
        coro.close()
        seen["called"] = True
        return "ok"

    monkeypatch.setattr(mcp_module, "_run_async", _fake_run_async)

    config = MCPConfig(
        transport="http",
        server_url="http://mcp.local",
        tool_name="echo",
        api_key=None,
        command=None,
        args=[],
    )

    assert mcp_module._call_mcp_tool("echo", {"text": "hi"}, config) == "ok"
    assert seen["called"] is True


def test_run_mcp_node_missing_name():
    config = MCPConfig(
        transport="http",
        server_url="http://mcp.local",
        tool_name=None,
        api_key=None,
        command=None,
        args=[],
    )

    result = mcp_module.run_mcp_node({}, config=config)

    assert result["status"] == "failed"
    assert "tool_name is required" in result["error"]
