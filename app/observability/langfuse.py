from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any, Optional, Tuple

from langfuse import Langfuse

from app.config import LangfuseConfig


logger = logging.getLogger(__name__)
_LANGFUSE_TRACE: ContextVar[Optional[object]] = ContextVar("langfuse_trace", default=None)


def _merge_metadata(env: Optional[str], metadata: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    merged: dict[str, Any] = {}
    if env:
        merged["env"] = env
    if metadata:
        merged.update(metadata)
    return merged or None


def get_langfuse_trace() -> Optional[object]:
    return _LANGFUSE_TRACE.get()


def clear_langfuse_trace() -> None:
    _LANGFUSE_TRACE.set(None)


def _is_enabled(config: LangfuseConfig) -> bool:
    return bool(config.public_key and config.secret_key and config.host)


def _create_client(config: LangfuseConfig) -> Optional[Langfuse]:
    if not _is_enabled(config):
        logger.info("langfuse disabled: missing config")
        return None
    return Langfuse(
        public_key=config.public_key,
        secret_key=config.secret_key,
        host=config.host,
    )


def start_langfuse_trace(
    *,
    config: LangfuseConfig,
    trace_name: str,
    metadata: Optional[dict[str, Any]] = None,
) -> Optional[object]:
    logger.info("langfuse trace start requested")
    try:
        client = _create_client(config)
        if client is None:
            return None
        return client.trace(
            name=trace_name,
            metadata=_merge_metadata(config.env, metadata),
        )
    except Exception:  # noqa: BLE001 - surface as non-fatal for the agent run.
        logger.exception("langfuse trace start failed")
        return None


def start_langfuse_span(
    trace: Optional[object],
    *,
    span_name: str,
    metadata: Optional[dict[str, Any]] = None,
) -> Optional[object]:
    if trace is None:
        return None
    try:
        span_method = getattr(trace, "span", None)
        if span_method is None:
            return None
        return span_method(
            name=span_name,
            metadata=metadata or None,
        )
    except Exception:  # noqa: BLE001 - keep agent running if langfuse fails.
        logger.exception("langfuse span start failed")
        return None


def end_langfuse_span(span: Optional[object]) -> None:
    if span is None:
        return
    end_method = getattr(span, "end", None)
    if end_method is None:
        return
    try:
        end_method()
    except Exception:  # noqa: BLE001 - keep agent running if langfuse fails.
        logger.exception("langfuse span end failed")
        return


def extract_thread_id(config: Optional[dict[str, Any]]) -> str:
    if not config:
        return "default"
    configurable = config.get("configurable")
    if isinstance(configurable, dict):
        thread_id = configurable.get("thread_id")
        if isinstance(thread_id, str) and thread_id:
            return thread_id
    return "default"


def ensure_langfuse_trace(
    *,
    config: LangfuseConfig,
    trace_name: str,
    metadata: Optional[dict[str, Any]] = None,
) -> Tuple[Optional[object], bool]:
    current = get_langfuse_trace()
    if current is not None:
        return current, False
    if not _is_enabled(config):
        return None, False
    trace = start_langfuse_trace(
        config=config,
        trace_name=trace_name,
        metadata=metadata,
    )
    if trace is None:
        return None, False
    _LANGFUSE_TRACE.set(trace)
    return trace, True


def run_langfuse_trace(
    *,
    config: LangfuseConfig,
    trace_name: str,
    span_name: str,
    metadata: Optional[dict[str, Any]] = None,
    span_metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Optional[str]]:
    logger.info("langfuse trace started")
    try:
        client = _create_client(config)
        if client is None:
            return {
                "status": "skipped",
                "trace_id": None,
                "span_id": None,
            }
        trace = client.trace(
            name=trace_name,
            metadata=_merge_metadata(config.env, metadata),
        )
        span = trace.span(
            name=span_name,
            metadata=span_metadata or None,
        )
        end_langfuse_span(span)
        logger.info("langfuse trace succeeded")
        return {
            "status": "success",
            "trace_id": getattr(trace, "id", None),
            "span_id": getattr(span, "id", None),
        }
    except Exception as exc:  # noqa: BLE001 - want node to surface errors as data.
        logger.exception("langfuse trace failed")
        return {
            "status": "failed",
            "trace_id": None,
            "span_id": None,
            "error": str(exc),
        }
