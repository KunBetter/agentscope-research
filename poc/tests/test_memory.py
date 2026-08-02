"""文件型长期记忆装配离线测试（不调用模型 API）。"""

import os

from agentscope.middleware import AgenticMemoryMiddleware

from domains import load_domain
from engine.agent_engine import AgentEngine, EngineConfig


def _build_engine(tmp_path, **overrides: object) -> AgentEngine:
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    defaults: dict = {"env_files": (), "memory_dir": str(tmp_path)}
    defaults.update(overrides)
    return AgentEngine(load_domain("stock_qa"), EngineConfig(**defaults))


def _basic_tool_names(engine: AgentEngine) -> set[str]:
    return {tool.name for tool in engine.toolkit.tool_groups[0].tools}


def test_memory_middleware_and_tools_attached(tmp_path) -> None:
    engine = _build_engine(tmp_path)
    assert engine.memory_root == tmp_path
    assert engine.memory_root.exists()
    assert any(
        isinstance(mw, AgenticMemoryMiddleware)
        for mw in engine.agent._reply_middlewares
    )
    tool_names = _basic_tool_names(engine)
    assert {"Read", "Write"} <= tool_names


def test_memory_write_allow_rule_added(tmp_path) -> None:
    engine = _build_engine(tmp_path)
    rules = engine.agent.state.permission_context.allow_rules.get(
        "Write",
        [],
    )
    assert len(rules) == 1
    assert str(tmp_path) in rules[0].rule_content


def test_memory_disabled_by_default(tmp_path) -> None:
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    engine = AgentEngine(load_domain("stock_qa"), EngineConfig(env_files=()))
    assert engine.memory_root is None
    assert "Write" not in _basic_tool_names(engine)
    assert "Read" not in _basic_tool_names(engine)


def test_memory_dir_is_created(tmp_path) -> None:
    target = tmp_path / "nested" / "memory"
    _build_engine(target)
    assert target.is_dir()
