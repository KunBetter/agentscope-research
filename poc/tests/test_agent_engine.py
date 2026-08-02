"""引擎装配离线测试：构造 Agent 但不发起模型调用。"""

import os

from pydantic import BaseModel

from domains import load_domain
from engine.agent_engine import AgentEngine, EngineConfig


def _build_engine(domain_name: str) -> AgentEngine:
    # 构造模型只需要格式合法的 key，不发网络请求
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    return AgentEngine(load_domain(domain_name), EngineConfig(env_files=()))


def test_engine_assembles_stock_qa() -> None:
    engine = _build_engine("stock_qa")
    assert engine.agent.name == "stock_qa"
    assert engine.domain.output_schema is not None
    assert issubclass(engine.domain.output_schema, BaseModel)
    assert "get_stock_price" in engine.registry.tool_names
    assert "get_stock_financials" in engine.registry.tool_names
    assert engine.toolkit is not None


def test_engine_assembles_weather() -> None:
    engine = _build_engine("weather")
    assert engine.agent.name == "weather"
    assert "get_city_weather" in engine.registry.tool_names
    assert engine.domain.output_schema is not None


def test_engine_has_no_shared_state_between_domains() -> None:
    stock = _build_engine("stock_qa")
    weather = _build_engine("weather")
    assert set(stock.registry.tool_names) != set(weather.registry.tool_names)
    assert stock.agent is not weather.agent
