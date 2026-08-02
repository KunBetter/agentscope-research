"""领域包契约离线测试。"""

from pydantic import BaseModel

from domains import DOMAIN_REGISTRY, list_domains, load_domain
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
