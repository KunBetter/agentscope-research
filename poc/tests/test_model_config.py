"""模型重试/回退配置离线测试（构造模型不发网络请求）。"""

import os

from agentscope.agent import ModelConfig
from agentscope.credential import DeepSeekCredential
from agentscope.model import DeepSeekChatModel

from domains import load_domain
from engine.agent_engine import AgentEngine, EngineConfig


def _build_engine(**overrides: object) -> AgentEngine:
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    defaults: dict = {"env_files": ()}
    defaults.update(overrides)
    return AgentEngine(load_domain("stock_qa"), EngineConfig(**defaults))


def test_max_retries_shorthand() -> None:
    engine = _build_engine(max_retries=3)
    assert engine.agent.model_config.max_retries == 3


def test_fallback_model_shorthand() -> None:
    engine = _build_engine(fallback_model="deepseek-v4-pro")
    fallback = engine.agent.model_config.fallback_model
    assert fallback is not None
    assert fallback.model == "deepseek-v4-pro"


def test_full_model_config_passthrough() -> None:
    fallback = DeepSeekChatModel(
        credential=DeepSeekCredential(api_key="test-key"),
        model="deepseek-v4-pro",
    )
    engine = _build_engine(
        model_config=ModelConfig(max_retries=2, fallback_model=fallback),
    )
    assert engine.agent.model_config.max_retries == 2
    assert engine.agent.model_config.fallback_model is fallback


def test_default_model_config() -> None:
    engine = _build_engine()
    assert engine.agent.model_config.max_retries == 0
    assert engine.agent.model_config.fallback_model is None


def test_negative_retries_rejected() -> None:
    try:
        _build_engine(model_config=ModelConfig(max_retries=-1))
    except ValueError:
        pass
    else:
        raise AssertionError("max_retries < 0 应被 pydantic 拒绝")
