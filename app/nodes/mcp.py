from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import requests

from app.config import MCPConfig


logger = logging.getLogger(__name__)
_JSONRPC_TIMEOUT_SECONDS = 10


def _build_headers(api_key: Optional[str]) -> dict[str, str]:
    if not api_key:
        return {}
    return {"Authorization": f"Bearer {api_key}"}


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise RuntimeError("run_mcp_node cannot be called from a running event loop")


def _load_stdio_client():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    return ClientSession, StdioServerParameters, stdio_client


def _load_sse_client():
    from mcp import ClientSession

    try:
        from mcp.client.sse import sse_client
    except ImportError as exc:
        try:
            from mcp.client.sse_client import sse_client  # type: ignore
        except ImportError as inner_exc:
            raise RuntimeError("mcp sse client is not available") from inner_exc
        raise RuntimeError("mcp sse client is not available") from exc

    return ClientSession, sse_client


def _load_http_client():
    from mcp import ClientSession

    try:
        from mcp.client.streamable_http import streamable_http_client

        return ClientSession, streamable_http_client
    except ImportError:
        try:
            from mcp.client.http import http_client
        except ImportError as exc:
            raise RuntimeError("mcp http client is not available") from exc
    return ClientSession, http_client


def _jsonrpc_request(
    session: requests.Session,
    server_url: str,
    method: str,
    params: Optional[dict[str, Any]],
    request_id: int,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "method": method,
        "id": request_id,
    }
    if params is not None:
        payload["params"] = params
    response = session.post(server_url, json=payload, timeout=_JSONRPC_TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("MCP JSON-RPC response is not an object")
    if "error" in data:
        raise RuntimeError(f"MCP JSON-RPC error: {data['error']}")
    return data


def _call_mcp_tool_jsonrpc(
    tool_name: str,
    tool_args: dict[str, Any],
    config: MCPConfig,
) -> Any:
    if not config.server_url:
        raise ValueError("MCP_SERVER_URL is required for jsonrpc transport")

    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    session.headers.update(_build_headers(config.api_key))

    _jsonrpc_request(
        session,
        config.server_url,
        "initialize",
        {
            "protocolVersion": "0.1.0",
            "clientInfo": {"name": "langgraph-demo", "version": "1.0.0"},
        },
        request_id=1,
    )
    _jsonrpc_request(session, config.server_url, "tools/list", None, request_id=2)
    result = _jsonrpc_request(
        session,
        config.server_url,
        "tools/call",
        {"name": tool_name, "arguments": tool_args},
        request_id=3,
    )
    return result.get("result")


async def _call_mcp_tool_async(
    tool_name: str,
    tool_args: dict[str, Any],
    config: MCPConfig,
) -> Any:
    transport = (config.transport or "").lower()
    if transport == "stdio":
        if not config.command:
            raise ValueError("MCP_COMMAND is required for stdio transport")
        client_session, params_cls, stdio_client = _load_stdio_client()
        params = params_cls(command=config.command, args=config.args or [])
        async with stdio_client(params) as (read, write):
            async with client_session(read, write) as session:
                await session.initialize()
                return await session.call_tool(tool_name, tool_args)

    if transport in {"http", "sse"}:
        if not config.server_url:
            raise ValueError("MCP_SERVER_URL is required for http/sse transport")
        headers = _build_headers(config.api_key)
        if transport == "sse":
            client_session, client_factory = _load_sse_client()
        else:
            client_session, client_factory = _load_http_client()
        async with client_factory(config.server_url, headers=headers) as (read, write):
            async with client_session(read, write) as session:
                await session.initialize()
                return await session.call_tool(tool_name, tool_args)

    raise ValueError(f"Unsupported MCP transport: {config.transport!r}")


def _call_mcp_tool(
    tool_name: str,
    tool_args: dict[str, Any],
    config: MCPConfig,
) -> Any:
    transport = (config.transport or "").lower()
    if transport == "stdio" and not config.command and config.server_url:
        logger.warning(
            "mcp transport stdio missing MCP_COMMAND; falling back to jsonrpc with MCP_SERVER_URL"
        )
        transport = "jsonrpc"
    if transport in {"jsonrpc", "http-jsonrpc", "rpc"}:
        return _call_mcp_tool_jsonrpc(tool_name, tool_args, config)
    return _run_async(_call_mcp_tool_async(tool_name, tool_args, config))


def run_mcp_node(
    tool_args: Optional[dict[str, Any]],
    *,
    config: MCPConfig,
    tool_name: Optional[str] = None,
) -> dict[str, Any]:
    logger.info("mcp node started")
    name = tool_name or config.tool_name
    try:
        if not name:
            raise ValueError("tool_name is required")
        result = _call_mcp_tool(name, tool_args or {}, config)
        logger.info("mcp node succeeded")
        return {
            "status": "success",
            "tool_name": name,
            "tool_result": result,
        }
    except Exception as exc:  # noqa: BLE001 - want node to surface errors as data.
        logger.exception("mcp node failed")
        return {
            "status": "failed",
            "tool_name": name,
            "tool_result": None,
            "error": str(exc),
        }
