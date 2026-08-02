"""上下文管理配置 + 会话重置离线测试（不调用模型 API）。"""

import os

import pytest
from agentscope.agent import ContextConfig, InjectionConfig

from domains import load_domain
from engine.agent_engine import AgentEngine, EngineConfig


def _build_engine(**overrides: object) -> AgentEngine:
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    defaults: dict = {"env_files": ()}
    defaults.update(overrides)
    return AgentEngine(load_domain("stock_qa"), EngineConfig(**defaults))


def test_context_config_propagates_to_agent() -> None:
    engine = _build_engine(
        context_config=ContextConfig(trigger_ratio=0.5, reserve_ratio=0.2),
    )
    assert engine.agent.context_config.trigger_ratio == 0.5
    assert engine.agent.context_config.reserve_ratio == 0.2


def test_default_context_config_used_when_none() -> None:
    engine = _build_engine()
    # 未显式配置时使用框架默认 trigger_ratio=0.8
    assert engine.agent.context_config.trigger_ratio == 0.8


def test_invalid_context_config_raises() -> None:
    # reserve_ratio >= trigger_ratio 时 Agent 配置校验会拒绝
    with pytest.raises(ValueError):
        _build_engine(
            context_config=ContextConfig(
                trigger_ratio=0.1,
                reserve_ratio=0.5,
            ),
        )


def test_injection_config_propagates_to_agent() -> None:
    engine = _build_engine(
        injection_config=InjectionConfig(
            inject_runtime_state=False,
            context_buffer_ratio=0.02,
        ),
    )
    assert engine.agent.injection_config.inject_runtime_state is False
    assert engine.agent.injection_config.context_buffer_ratio == 0.02


def test_reset_starts_new_session() -> None:
    engine = _build_engine()
    first_session = engine.agent.state.session_id
    engine.reset()
    second_session = engine.agent.state.session_id
    assert first_session != second_session
    assert engine.model is not None
    assert engine.toolkit is not None
