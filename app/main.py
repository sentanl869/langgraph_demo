from __future__ import annotations

import argparse
import json
import uuid
from typing import Any, Optional

from app.config import load_config
from app.graph import run_agent


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the langgraph agent.")
    parser.add_argument("--prompt", default="ping", help="Prompt for the LLM node.")
    parser.add_argument(
        "--mem0-query",
        default="What did the user say?",
        help="Query used for mem0 search.",
    )
    parser.add_argument(
        "--mcp-args",
        default="{}",
        help="JSON payload passed to the MCP tool.",
    )
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Thread id for langgraph checkpointing.",
    )
    return parser.parse_args(argv)


def _parse_json(value: str) -> dict[str, Any]:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON for --mcp-args") from exc
    if not isinstance(data, dict):
        raise ValueError("--mcp-args must be a JSON object")
    return data


def main(argv: Optional[list[str]] = None) -> dict[str, Any]:
    args = _parse_args(argv)
    config = load_config()
    initial_state = {
        "prompt": args.prompt,
        "mem0_query": args.mem0_query,
        "mcp_tool_args": _parse_json(args.mcp_args),
    }
    thread_id = args.thread_id or uuid.uuid4().hex
    result = run_agent(
        initial_state,
        config=config,
        thread_id=thread_id,
    )
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
