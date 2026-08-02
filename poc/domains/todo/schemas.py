"""待办管理领域结构化输出契约（业务相关）。"""

from pydantic import BaseModel, Field


class TodoReport(BaseModel):
    """一份待办操作报告。"""

    todos: list[str] = Field(default_factory=list, description="当前待办列表")
    action: str = Field(
        description="本次动作: query / add / denied",
    )
    summary: str = Field(description="操作结果简要说明")
    report_time: str = Field(
        description="报告生成时间（YYYY-MM-DD）",
    )
