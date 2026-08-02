"""城市天气查询领域包：第二个领域包，证明引擎业务无关、可插拔。"""

from __future__ import annotations

from engine.domain import DomainPackage
from engine.tool_registry import ToolRegistry

from .prompts import SYSTEM_PROMPT
from .schemas import WeatherReport
from .tools import get_city_weather


class WeatherDomain(DomainPackage):
    """天气查询：单只读工具 + 结构化报告输出。"""

    name = "weather"
    description = "城市天气查询：单只读工具 + 结构化报告输出"
    system_prompt = SYSTEM_PROMPT
    output_schema = WeatherReport

    def register_tools(self, registry: ToolRegistry) -> None:
        registry.register(get_city_weather, read_only=True)
