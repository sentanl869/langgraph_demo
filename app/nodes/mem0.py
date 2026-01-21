from __future__ import annotations

import logging
from typing import Any, Optional

import requests

from app.config import Mem0Config


logger = logging.getLogger(__name__)


def _build_headers(api_key: Optional[str]) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Token {api_key}" if api_key else "",
    }


def _build_url(server_url: Optional[str], path: str) -> str:
    base = server_url or ""
    return f"{base.rstrip('/')}{path}"


def run_mem0_node(
    content: str,
    query: str,
    *,
    config: Mem0Config,
) -> dict[str, Any]:
    logger.info("mem0 node started")
    try:
        headers = _build_headers(config.api_key)

        add_payload = {
            "messages": [{"role": "user", "content": content}],
            "user_id": config.user_id,
        }
        add_response = requests.post(
            _build_url(config.server_url, "/memories/"),
            json=add_payload,
            headers=headers,
        )
        add_response.raise_for_status()
        add_data = add_response.json()
        memory_id = add_data.get("id") if isinstance(add_data, dict) else None

        search_payload = {
            "query": query,
            "user_id": config.user_id,
        }
        search_response = requests.post(
            _build_url(config.server_url, "/search/"),
            json=search_payload,
            headers=headers,
        )
        search_response.raise_for_status()
        search_data = search_response.json()

        logger.info("mem0 node succeeded")
        return {
            "status": "success",
            "memory_id": memory_id,
            "query_result": search_data,
        }
    except Exception as exc:  # noqa: BLE001 - want node to surface errors as data.
        logger.exception("mem0 node failed")
        return {
            "status": "failed",
            "memory_id": None,
            "query_result": None,
            "error": str(exc),
        }
