"""待办管理领域包：验证写工具 + HITL 人工确认流。"""

from __future__ import annotations

from engine.domain import DomainPackage
from engine.tool_registry import ToolRegistry

from .prompts import SYSTEM_PROMPT
from .schemas import TodoReport
from .tools import add_todo, list_todos


class TodoDomain(DomainPackage):
    """待办管理：只读查询 + 写操作（需确认）。"""

    name = "todo"
    description = "待办管理：只读查询 + 写操作（HITL 确认流验证）"
    system_prompt = SYSTEM_PROMPT
    output_schema = TodoReport

    def register_tools(self, registry: ToolRegistry) -> None:
        registry.register(list_todos, read_only=True)
        registry.register(
            add_todo,
            read_only=False,  # 写工具：触发权限系统需人工确认
            group="write",
            group_description="待办写操作（需人工确认）",
        )
