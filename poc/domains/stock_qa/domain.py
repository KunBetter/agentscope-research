"""A 股投研问答领域包：演示引擎层与业务领域层的分工。"""

from __future__ import annotations

from engine.domain import DomainPackage
from engine.tool_registry import ToolRegistry

from .prompts import SYSTEM_PROMPT
from .schemas import StockReport
from .tools import get_stock_financials, get_stock_price


class StockQaDomain(DomainPackage):
    """投研问答：实时价格 + 财务指标，输出结构化研报。"""

    name = "stock_qa"
    description = "A 股投研问答：价格 + 财务指标，结构化研报输出"
    system_prompt = SYSTEM_PROMPT
    output_schema = StockReport

    def register_tools(self, registry: ToolRegistry) -> None:
        registry.register(
            get_stock_price,
            read_only=True,
            group="data",
            group_description="A 股行情与财务数据查询（只读）",
        )
        registry.register(
            get_stock_financials,
            read_only=True,
            group="data",
            group_description="A 股行情与财务数据查询（只读）",
        )
