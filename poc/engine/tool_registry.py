"""工具注册表（业务无关）。

领域包通过 :class:`ToolRegistry` 声明工具（名称、描述、只读属性、工具组），
引擎统一转换为 AgentScope 的 ``FunctionTool`` / ``ToolGroup`` / ``Toolkit``。
引擎只理解 ``ToolSpec``，不感知具体业务函数。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from agentscope.tool import FunctionTool, ToolGroup, Toolkit


@dataclass
class ToolSpec:
    """一条工具注册声明。"""

    func: Callable
    name: str | None = None
    description: str | None = None
    read_only: bool = False
    concurrency_safe: bool = True
    group: str = "basic"
    """工具组名；非 basic 组必须提供 group_description。"""

    group_description: str | None = None


class ToolRegistry:
    """收集领域包的工具声明，统一构建 AgentScope Toolkit。"""

    def __init__(self) -> None:
        self._specs: list[ToolSpec] = []

    # ------------------------------------------------------------------
    # 注册
    # ------------------------------------------------------------------
    def register(
        self,
        func: Callable | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        read_only: bool = False,
        group: str = "basic",
        group_description: str | None = None,
    ) -> Callable:
        """注册一个工具，支持直接传函数或装饰器两种用法。

        示例::

            registry.register(get_stock_price, read_only=True)

            @registry.register(read_only=True, group="data", ...)
            def get_stock_price(symbol: str) -> str: ...
        """

        def _apply(f: Callable) -> Callable:
            if group != "basic" and not group_description:
                raise ValueError(
                    f"非 basic 工具组 '{group}' 必须提供 group_description",
                )
            self._specs.append(
                ToolSpec(
                    func=f,
                    name=name,
                    description=description,
                    read_only=read_only,
                    concurrency_safe=True,
                    group=group,
                    group_description=group_description,
                ),
            )
            return f

        if func is None:
            return _apply
        return _apply(func)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    @property
    def specs(self) -> tuple[ToolSpec, ...]:
        """已注册的工具声明（只读视图）。"""
        return tuple(self._specs)

    @property
    def tool_names(self) -> tuple[str, ...]:
        """已注册的工具名（未显式命名时取函数名）。"""
        return tuple(spec.name or spec.func.__name__ for spec in self._specs)

    # ------------------------------------------------------------------
    # 构建
    # ------------------------------------------------------------------
    def build_toolkit(
        self,
        extra_tools: list | None = None,
    ) -> Toolkit:
        """把注册声明转换为 AgentScope Toolkit（按工具组分组）。

        ``extra_tools`` 用于注入引擎级工具（如长期记忆所需的 Read/Write），
        挂到 basic 组。
        """
        groups: dict[str, list[FunctionTool]] = {}
        for spec in self._specs:
            tool = FunctionTool(
                spec.func,
                name=spec.name,
                description=spec.description,
                is_read_only=spec.read_only,
                is_concurrency_safe=spec.concurrency_safe,
            )
            groups.setdefault(spec.group, []).append(tool)

        basic_tools = groups.pop("basic", None)
        if extra_tools:
            basic_tools = list(basic_tools or []) + list(extra_tools)
        tool_groups = []
        for group_name, tools in groups.items():
            desc = next(
                (
                    s.group_description
                    for s in self._specs
                    if s.group == group_name and s.group_description
                ),
                None,
            )
            tool_groups.append(
                ToolGroup(
                    name=group_name,
                    description=desc or f"{group_name} 工具组",
                    tools=tools,
                ),
            )

        return Toolkit(tools=basic_tools, tool_groups=tool_groups)
