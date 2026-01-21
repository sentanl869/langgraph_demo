import pytest

from app.config import load_config
from app.nodes.llm import run_llm_node


def test_llm_node_e2e():
    config = load_config().llm
    if not config.api_key or not config.endpoint or not config.model:
        pytest.skip("LLM e2e requires LLM_API_KEY, LLM_ENDPOINT, and LLM_MODEL")

    result = run_llm_node("ping", config=config)

    assert result["status"] == "success"
    assert result["model"] == config.model
    assert result["output_text"]
