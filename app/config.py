from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class MilvusConfig:
    host: Optional[str]
    port: Optional[int]
    username: Optional[str]
    password: Optional[str]
    collection: Optional[str]
    partition: Optional[str]
    db_name: Optional[str]


@dataclass
class Mem0Config:
    server_url: Optional[str]
    api_key: Optional[str]
    user_id: Optional[str]


@dataclass
class LLMConfig:
    api_key: Optional[str]
    endpoint: Optional[str]
    model: Optional[str]
    timeout: Optional[int]
    temperature: Optional[float]


@dataclass
class LangfuseConfig:
    public_key: Optional[str]
    secret_key: Optional[str]
    host: Optional[str]
    env: Optional[str]


@dataclass
class MCPConfig:
    transport: Optional[str]
    server_url: Optional[str]
    tool_name: Optional[str]
    api_key: Optional[str]
    command: Optional[str]
    args: list[str]


@dataclass
class CheckpointConfig:
    backend: Optional[str]
    path: Optional[str]


@dataclass
class AppConfig:
    milvus: MilvusConfig
    mem0: Mem0Config
    llm: LLMConfig
    langfuse: LangfuseConfig
    mcp: MCPConfig
    checkpoint: CheckpointConfig


def _normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if value.strip() == "":
        return None
    return value


def _get_env(name: str, cast=None) -> Optional[object]:
    value = _normalize(os.getenv(name))
    if value is None:
        return None
    if cast is None:
        return value
    try:
        return cast(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid value for {name}: {value!r}") from exc


def _parse_args(value: Optional[str]) -> list[str]:
    value = _normalize(value)
    if value is None:
        return []
    return shlex.split(value)


def load_config() -> AppConfig:
    load_dotenv(override=False)

    milvus = MilvusConfig(
        host=_get_env("MILVUS_HOST"),
        port=_get_env("MILVUS_PORT", cast=int),
        username=_get_env("MILVUS_USERNAME"),
        password=_get_env("MILVUS_PASSWORD"),
        collection=_get_env("MILVUS_COLLECTION"),
        partition=_get_env("MILVUS_PARTITION"),
        db_name=_get_env("MILVUS_DB_NAME"),
    )
    mem0 = Mem0Config(
        server_url=_get_env("MEM0_SERVER_URL"),
        api_key=_get_env("MEM0_API_KEY"),
        user_id=_get_env("MEM0_USER_ID"),
    )
    llm = LLMConfig(
        api_key=_get_env("LLM_API_KEY"),
        endpoint=_get_env("LLM_ENDPOINT"),
        model=_get_env("LLM_MODEL"),
        timeout=_get_env("LLM_TIMEOUT", cast=int),
        temperature=_get_env("LLM_TEMPERATURE", cast=float),
    )
    langfuse = LangfuseConfig(
        public_key=_get_env("LANGFUSE_PUBLIC_KEY"),
        secret_key=_get_env("LANGFUSE_SECRET_KEY"),
        host=_get_env("LANGFUSE_HOST"),
        env=_get_env("LANGFUSE_ENV"),
    )
    mcp = MCPConfig(
        transport=_get_env("MCP_TRANSPORT"),
        server_url=_get_env("MCP_SERVER_URL"),
        tool_name=_get_env("MCP_TOOL_NAME"),
        api_key=_get_env("MCP_API_KEY"),
        command=_get_env("MCP_COMMAND"),
        args=_parse_args(os.getenv("MCP_ARGS")),
    )
    checkpoint = CheckpointConfig(
        backend=_get_env("CHECKPOINT_BACKEND"),
        path=_get_env("CHECKPOINT_PATH"),
    )

    return AppConfig(
        milvus=milvus,
        mem0=mem0,
        llm=llm,
        langfuse=langfuse,
        mcp=mcp,
        checkpoint=checkpoint,
    )
