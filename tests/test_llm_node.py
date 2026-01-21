from types import SimpleNamespace

import pytest

from app.config import LLMConfig
from app.nodes.llm import run_llm_node


class FakeOpenAI:
    def __init__(self, expected, response, api_key=None, base_url=None, timeout=None):
        expected["api_key"] = api_key
        expected["base_url"] = base_url
        expected["timeout"] = timeout
        self._expected = expected
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )
        self._response = response

    def _create(self, **kwargs):
        self._expected["create_kwargs"] = kwargs
        return self._response


def test_llm_node_success(monkeypatch):
    expected = {}
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))]
    )

    def _fake_openai(*args, **kwargs):
        return FakeOpenAI(expected, response, *args, **kwargs)

    monkeypatch.setattr("app.nodes.llm.OpenAI", _fake_openai)

    config = LLMConfig(
        api_key="llm_key",
        endpoint="http://llm.local",
        model="gpt-test",
        timeout=30,
        temperature=0.2,
    )
    result = run_llm_node("Say hi", config=config)

    assert expected["api_key"] == "llm_key"
    assert expected["base_url"] == "http://llm.local"
    assert expected["timeout"] == 30
    assert expected["create_kwargs"]["model"] == "gpt-test"
    assert expected["create_kwargs"]["temperature"] == 0.2
    assert expected["create_kwargs"]["messages"] == [
        {"role": "user", "content": "Say hi"}
    ]
    assert result == {
        "status": "success",
        "model": "gpt-test",
        "output_text": "hello",
    }


def test_llm_node_system_prompt(monkeypatch):
    expected = {}
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))]
    )

    def _fake_openai(*args, **kwargs):
        return FakeOpenAI(expected, response, *args, **kwargs)

    monkeypatch.setattr("app.nodes.llm.OpenAI", _fake_openai)

    config = LLMConfig(
        api_key="llm_key",
        endpoint=None,
        model="gpt-test",
        timeout=None,
        temperature=None,
    )
    run_llm_node("Say hi", config=config, system_prompt="system")

    assert expected["create_kwargs"]["messages"] == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "Say hi"},
    ]


def test_llm_node_failure(monkeypatch):
    def _fake_openai(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.nodes.llm.OpenAI", _fake_openai)

    config = LLMConfig(
        api_key="llm_key",
        endpoint="http://llm.local",
        model="gpt-test",
        timeout=30,
        temperature=0.2,
    )

    result = run_llm_node("Say hi", config=config)

    assert result["status"] == "failed"
    assert result["model"] == "gpt-test"
    assert "boom" in result["error"]
