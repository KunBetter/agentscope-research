"""股票问答领域结构化输出契约（业务相关）。"""

from pydantic import BaseModel, Field


class StockReport(BaseModel):
    """一份简版投研问答报告。"""

    symbol: str = Field(description="股票代码")
    name: str = Field(description="股票名称")
    price: str | None = Field(default=None, description="当前价格（工具返回原文）")
    financials: dict[str, str] | None = Field(
        default=None,
        description="财务指标（工具返回原文）",
    )
    summary: str = Field(description="基于工具数据的简要分析")
    source: str = Field(default="mock-data", description="数据来源")
    disclaimer: str = Field(
        default="演示数据，不构成投资建议",
        description="免责声明",
    )
