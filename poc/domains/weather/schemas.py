"""天气查询领域结构化输出契约（业务相关）。"""

from pydantic import BaseModel, Field


class WeatherReport(BaseModel):
    """一份简版天气报告。"""

    city: str = Field(description="城市")
    condition: str = Field(description="天气状况")
    temperature: str = Field(description="温度")
    wind: str = Field(default="", description="风向风力")
    summary: str = Field(description="基于工具数据的简要描述")
    source: str = Field(default="mock-data", description="数据来源")
    disclaimer: str = Field(
        default="演示数据，仅作架构验证",
        description="免责声明",
    )
    report_time: str = Field(
        description="报告生成时间（YYYY-MM-DD）",
    )
