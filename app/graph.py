from __future__ import annotations

from typing import Any, Callable, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.config import AppConfig, CheckpointConfig
from app.nodes.llm import run_llm_node
from app.nodes.mem0 import run_mem0_node
from app.nodes.milvus import run_milvus_node
from app.nodes.mcp import run_mcp_node
from app.observability.langfuse import (
    clear_langfuse_trace,
    end_langfuse_span,
    ensure_langfuse_trace,
    extract_thread_id,
    get_langfuse_trace,
    start_langfuse_span,
    start_langfuse_trace,
)


DEFAULT_VECTOR = [0.1, 0.2, 0.3]
DEFAULT_MEM0_QUERY = "What did the user say?"


class AgentState(TypedDict, total=False):
    prompt: str
    mem0_query: str
    milvus_vector: list[float]
    milvus_query_vector: list[float]
    mcp_tool_args: dict[str, Any]
    llm: dict[str, Any]
    mem0: dict[str, Any]
    milvus: dict[str, Any]
    mcp: dict[str, Any]
    result: dict[str, Any]


def _get_override(
    overrides: Optional[dict[str, Callable[[AgentState], dict[str, Any]]]],
    name: str,
    default: Callable[[AgentState], dict[str, Any]],
) -> Callable[[AgentState], dict[str, Any]]:
    if overrides and name in overrides:
        return overrides[name]
    return default


def build_graph(
    config: AppConfig,
    *,
    node_overrides: Optional[dict[str, Callable[[AgentState], dict[str, Any]]]] = None,
    langfuse_trace: Optional[object] = None,
) -> StateGraph:
    app_config = config

    def _wrap_with_span(
        name: str,
        node_fn: Callable[[AgentState], dict[str, Any]],
    ) -> Callable[[AgentState], dict[str, Any]]:
        def _wrapped(state: AgentState, config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
            active_trace = langfuse_trace or get_langfuse_trace()
            if active_trace is None:
                active_trace, _ = ensure_langfuse_trace(
                    config=app_config.langfuse,
                    trace_name="agent-run",
                    metadata={"thread_id": extract_thread_id(config)},
                )
            span = start_langfuse_span(
                active_trace,
                span_name=name,
                metadata={"node": name},
            )
            try:
                return node_fn(state)
            finally:
                end_langfuse_span(span)
                if langfuse_trace is None and name == "final":
                    clear_langfuse_trace()

        return _wrapped

    def _llm_node(state: AgentState) -> dict[str, Any]:
        prompt = state.get("prompt", "")
        return {"llm": run_llm_node(prompt, config=config.llm)}

    def _mem0_node(state: AgentState) -> dict[str, Any]:
        content = ""
        if isinstance(state.get("llm"), dict):
            content = state["llm"].get("output_text") or ""
        content = content or state.get("prompt", "")
        query = state.get("mem0_query", DEFAULT_MEM0_QUERY)
        return {"mem0": run_mem0_node(content, query, config=config.mem0)}

    def _milvus_node(state: AgentState) -> dict[str, Any]:
        vector = state.get("milvus_vector", DEFAULT_VECTOR)
        query_vector = state.get("milvus_query_vector")
        return {
            "milvus": run_milvus_node(
                vector,
                config=config.milvus,
                query_vector=query_vector,
            )
        }

    def _mcp_node(state: AgentState) -> dict[str, Any]:
        tool_args = state.get("mcp_tool_args", {})
        return {"mcp": run_mcp_node(tool_args, config=config.mcp)}

    def _final_node(state: AgentState) -> dict[str, Any]:
        return {
            "result": {
                "llm": state.get("llm"),
                "mem0": state.get("mem0"),
                "milvus": state.get("milvus"),
                "mcp": state.get("mcp"),
            }
        }

    graph = StateGraph(AgentState)
    graph.add_node(
        "llm",
        _wrap_with_span("llm", _get_override(node_overrides, "llm", _llm_node)),
    )
    graph.add_node(
        "mem0",
        _wrap_with_span("mem0", _get_override(node_overrides, "mem0", _mem0_node)),
    )
    graph.add_node(
        "milvus",
        _wrap_with_span("milvus", _get_override(node_overrides, "milvus", _milvus_node)),
    )
    graph.add_node(
        "mcp",
        _wrap_with_span("mcp", _get_override(node_overrides, "mcp", _mcp_node)),
    )
    graph.add_node(
        "final",
        _wrap_with_span("final", _get_override(node_overrides, "final", _final_node)),
    )
    graph.set_entry_point("llm")
    graph.add_edge("llm", "mem0")
    graph.add_edge("mem0", "milvus")
    graph.add_edge("milvus", "mcp")
    graph.add_edge("mcp", "final")
    graph.add_edge("final", END)
    return graph


def build_checkpointer(config: CheckpointConfig):
    backend = (config.backend or "memory").lower()
    if backend in {"memory", ""}:
        return MemorySaver()
    if backend == "sqlite":
        if not config.path:
            raise ValueError("CHECKPOINT_PATH is required for sqlite")
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
        except ImportError as exc:
            raise RuntimeError(
                "SQLite checkpointer is unavailable; install a langgraph sqlite checkpoint package."
            ) from exc
        return SqliteSaver(config.path)
    raise ValueError(f"Unsupported checkpoint backend: {config.backend!r}")


def run_agent(
    initial_state: dict[str, Any],
    *,
    config: AppConfig,
    thread_id: Optional[str] = None,
    node_overrides: Optional[dict[str, Callable[[AgentState], dict[str, Any]]]] = None,
    checkpointer: Optional[object] = None,
) -> dict[str, Any]:
    effective_thread_id = thread_id or "default"
    trace = start_langfuse_trace(
        config=config.langfuse,
        trace_name="agent-run",
        metadata={"thread_id": effective_thread_id},
    )
    graph = build_graph(
        config,
        node_overrides=node_overrides,
        langfuse_trace=trace,
    )
    active_checkpointer = checkpointer or build_checkpointer(config.checkpoint)
    app = graph.compile(checkpointer=active_checkpointer)
    run_config = None
    if active_checkpointer is not None:
        run_config = {"configurable": {"thread_id": effective_thread_id}}
    result_state = app.invoke(initial_state, config=run_config)
    if isinstance(result_state, dict):
        return result_state.get("result", {})
    return {}
