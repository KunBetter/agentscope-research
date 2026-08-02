"""领域包契约：引擎层与业务领域层之间的唯一接口。

引擎只依赖 ``DomainPackage`` 暴露的四个业务出口：

1. ``name / description`` —— 领域标识（Agent 名、注册表展示）；
2. ``register_tools(registry)`` —— 业务工具注入；
3. ``system_prompt`` —— 角色设定与行为约束；
4. ``output_schema`` —— 结构化输出契约（可选）。

业务领域包只需要实现这四个出口，引擎本身不感知任何业务。
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel

    from .tool_registry import ToolRegistry


class DomainPackage(ABC):
    """业务领域包（领域层必须实现的契约）。"""

    name: str = ""
    """领域唯一标识（同时作为 Agent 名）。"""

    description: str = ""
    """领域一句话描述（CLI / 注册表展示用）。"""

    system_prompt: str = ""
    """角色设定与行为约束（业务相关）。"""

    output_schema: type["BaseModel"] | None = None
    """结构化输出 Pydantic 模型；``None`` 表示不要求结构化输出。"""

    def __init__(self) -> None:
        for attr in ("name", "description", "system_prompt"):
            value = getattr(self, attr)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(
                    f"{type(self).__name__} 必须定义非空 {attr}（str）",
                )

        if self.output_schema is not None:
            from pydantic import BaseModel

            if not (
                isinstance(self.output_schema, type)
                and issubclass(self.output_schema, BaseModel)
            ):
                raise TypeError(
                    f"{type(self).__name__}.output_schema 必须是 "
                    "Pydantic BaseModel 子类或 None",
                )

    def register_tools(self, registry: "ToolRegistry") -> None:
        """业务领域向引擎注册工具（业务相关）。

        引擎在装配时调用；领域包按需覆写，默认不注册任何工具。
        """
