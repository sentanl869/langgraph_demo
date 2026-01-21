from __future__ import annotations

from app.config import load_config
from app.graph import build_graph


_config = load_config()
_graph = build_graph(_config)
graph = _graph.compile()
