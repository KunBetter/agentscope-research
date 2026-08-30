"""待办管理领域工具（业务相关，演示数据）。

``list_todos`` 只读；``add_todo`` 是写工具，注册为非只读，触发权限系统
的"需人工确认"分支（RequireUserConfirmEvent），确认后**真实写入**列表。

状态说明：待办列表是进程内演示状态（模块级 list，非持久化）。领域包在
引擎装配时调用 :func:`reset_todos` 恢复初始两条，保证每次装配（评测每条
任务、每次演示）互不影响。生产环境应替换为真实持久化存储。
"""

from __future__ import annotations

_INITIAL_TODOS = ["写周报", "复盘贵州茅台"]

_todos: list[str] = list(_INITIAL_TODOS)


def reset_todos() -> None:
    """恢复初始待办列表（引擎装配时调用，保证状态隔离）。"""
    _todos[:] = _INITIAL_TODOS


def list_todos() -> str:
    """返回当前待办列表（演示数据，只读工具）。"""
    if not _todos:
        return "当前没有待办（演示数据）"
    items = "; ".join(
        f"{index}. {item}" for index, item in enumerate(_todos, 1)
    )
    return f"当前待办（演示数据）: {items}"


def add_todo(text: str) -> str:
    """新增一条待办（写操作，需人工确认后才执行，演示实现）。"""
    _todos.append(text)
    return f"已添加待办: {text}（演示写入）"
