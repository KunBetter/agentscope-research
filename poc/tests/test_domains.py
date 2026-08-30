"""领域包契约离线测试。"""

import os

from pydantic import BaseModel

from domains import DOMAIN_REGISTRY, list_domains, load_domain
from domains.todo.tools import add_todo, list_todos, reset_todos
from engine.agent_engine import AgentEngine, EngineConfig
from engine.tool_registry import ToolRegistry


def test_demo_domains_registered() -> None:
    assert "stock_qa" in DOMAIN_REGISTRY
    assert "weather" in DOMAIN_REGISTRY
    assert len(list_domains()) == len(DOMAIN_REGISTRY)


def test_every_domain_satisfies_contract() -> None:
    for name in list_domains():
        domain = load_domain(name)
        assert domain.name == name
        assert domain.description.strip()
        assert domain.system_prompt.strip()
        if domain.output_schema is not None:
            assert issubclass(domain.output_schema, BaseModel)


def test_stock_qa_registers_tools() -> None:
    domain = load_domain("stock_qa")
    registry = ToolRegistry()
    domain.register_tools(registry)
    assert set(registry.tool_names) == {
        "get_stock_price",
        "get_stock_financials",
    }
    assert all(spec.read_only for spec in registry.specs)


def test_weather_registers_tools() -> None:
    domain = load_domain("weather")
    registry = ToolRegistry()
    domain.register_tools(registry)
    assert registry.tool_names == ("get_city_weather",)
    assert registry.specs[0].read_only is True


def test_todo_registers_read_only_and_write_tools() -> None:
    domain = load_domain("todo")
    registry = ToolRegistry()
    domain.register_tools(registry)
    flags = {spec.func.__name__: spec.read_only for spec in registry.specs}
    assert flags == {"list_todos": True, "add_todo": False}


def test_todo_add_writes_and_list_reflects() -> None:
    reset_todos()
    add_todo("买牛奶")
    assert "买牛奶" in list_todos()
    reset_todos()  # 恢复，避免影响其他用例


def test_todo_engine_assembly_resets_state() -> None:
    # 每次装配（register_tools）重置状态：先污染，再装配，应回到初始两条
    reset_todos()
    add_todo("污染项")
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    AgentEngine(load_domain("todo"), EngineConfig(env_files=()))
    assert "污染项" not in list_todos()
    assert "写周报" in list_todos()
    assert "复盘贵州茅台" in list_todos()
