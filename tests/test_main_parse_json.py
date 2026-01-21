import runpy
import sys
import types

import pytest

from app.main import _parse_json


def test_parse_json_invalid():
    with pytest.raises(ValueError):
        _parse_json("{invalid}")


def test_parse_json_non_object():
    with pytest.raises(ValueError):
        _parse_json('"text"')


def test_main_module_executes(monkeypatch):
    called = {"run_agent": False}

    fake_config = types.ModuleType("app.config")
    fake_config.load_config = lambda: "config"

    fake_graph = types.ModuleType("app.graph")

    def _run_agent(_state, *, config, thread_id=None):
        assert config == "config"
        called["run_agent"] = True
        return {"ok": True}

    fake_graph.run_agent = _run_agent

    monkeypatch.setitem(sys.modules, "app.config", fake_config)
    monkeypatch.setitem(sys.modules, "app.graph", fake_graph)
    monkeypatch.setattr(sys, "argv", ["app.main"])
    sys.modules.pop("app.main", None)

    runpy.run_module("app.main", run_name="__main__")

    assert called["run_agent"] is True
