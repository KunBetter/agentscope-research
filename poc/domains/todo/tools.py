"""待办管理领域工具（业务相关，演示数据）。

``list_todos`` 只读；``add_todo`` 是写工具，注册为非只读，触发权限系统
的"需人工确认"分支（RequireUserConfirmEvent）。
"""

from __future__ import annotations

_MOCK_TODOS = ["写周报", "复盘贵州茅台"]


def list_todos() -> str:
    """返回当前待办列表（演示数据，只读工具）。"""
    if not _MOCK_TODOS:
        return "当前没有待办（演示数据）"
    items = "; ".join(
        f"{index}. {item}" for index, item in enumerate(_MOCK_TODOS, 1)
    )
    return f"当前待办（演示数据）: {items}"


def add_todo(text: str) -> str:
    """新增一条待办（写操作，需人工确认后才执行，演示实现）。"""
    return f"已添加待办: {text}（演示写入）"
