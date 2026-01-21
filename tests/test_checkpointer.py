import importlib.util

import pytest

from app.config import CheckpointConfig
from app.graph import build_checkpointer


def test_build_checkpointer_memory():
    checkpointer = build_checkpointer(
        CheckpointConfig(backend="memory", path=None)
    )

    assert checkpointer.__class__.__name__ in {"MemorySaver", "InMemorySaver"}


def test_build_checkpointer_sqlite():
    if importlib.util.find_spec("langgraph.checkpoint.sqlite") is None:
        with pytest.raises(RuntimeError):
            build_checkpointer(
                CheckpointConfig(backend="sqlite", path="/tmp/checkpoints.db")
            )
        return

    checkpointer = build_checkpointer(
        CheckpointConfig(backend="sqlite", path="/tmp/checkpoints.db")
    )
    assert checkpointer.__class__.__name__ == "SqliteSaver"


def test_build_checkpointer_sqlite_requires_path():
    with pytest.raises(ValueError):
        build_checkpointer(CheckpointConfig(backend="sqlite", path=None))


def test_build_checkpointer_sqlite_module_present(monkeypatch):
    import sys
    import types

    fake_module = types.ModuleType("langgraph.checkpoint.sqlite")

    class DummySaver:
        def __init__(self, path):
            self.path = path

    fake_module.SqliteSaver = DummySaver

    monkeypatch.setitem(sys.modules, "langgraph.checkpoint.sqlite", fake_module)

    checkpointer = build_checkpointer(
        CheckpointConfig(backend="sqlite", path="/tmp/checkpoints.db")
    )

    assert isinstance(checkpointer, DummySaver)
    assert checkpointer.path == "/tmp/checkpoints.db"


def test_build_checkpointer_unknown():
    with pytest.raises(ValueError):
        build_checkpointer(CheckpointConfig(backend="nope", path=None))
