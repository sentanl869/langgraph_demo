from __future__ import annotations

import logging
from typing import Optional

from openai import OpenAI

from app.config import LLMConfig


logger = logging.getLogger(__name__)


def _build_messages(prompt: str, system_prompt: Optional[str]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return messages


def run_llm_node(
    prompt: str,
    *,
    config: LLMConfig,
    system_prompt: Optional[str] = None,
) -> dict[str, Optional[str]]:
    logger.info("LLM node started")
    try:
        client_kwargs: dict[str, object] = {"api_key": config.api_key}
        if config.endpoint:
            client_kwargs["base_url"] = config.endpoint
        if config.timeout is not None:
            client_kwargs["timeout"] = config.timeout

        client = OpenAI(**client_kwargs)

        create_kwargs: dict[str, object] = {
            "model": config.model,
            "messages": _build_messages(prompt, system_prompt),
        }
        if config.temperature is not None:
            create_kwargs["temperature"] = config.temperature

        response = client.chat.completions.create(**create_kwargs)
        output_text = response.choices[0].message.content
        logger.info("LLM node succeeded")
        return {
            "status": "success",
            "model": config.model,
            "output_text": output_text,
        }
    except Exception as exc:  # noqa: BLE001 - want node to surface errors as data.
        logger.exception("LLM node failed")
        return {
            "status": "failed",
            "model": config.model,
            "output_text": None,
            "error": str(exc),
        }
