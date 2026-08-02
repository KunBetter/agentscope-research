"""预算中间件装配 + 权限判定离线测试（不调用模型 API）。"""

import asyncio
import os

from agentscope.permission import (
    PermissionBehavior,
    PermissionContext,
    PermissionEngine,
)

from domains import load_domain
from engine.agent_engine import AgentEngine, EngineConfig
from engine.tool_registry import ToolRegistry


def _read_data(text: str) -> str:
    """只读查询。"""
    return f"数据: {text}"


def _write_data(text: str) -> str:
    """写操作（演示，应被默认权限策略拦截/要求确认）。"""
    return f"写入: {text}"


def test_budget_middleware_attached() -> None:
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    engine = AgentEngine(
        load_domain("stock_qa"),
        EngineConfig(env_files=(), token_budget=1000),
    )
    # ReplyBudgetControlMiddleware 实现 on_reply，应出现在 Agent 的回复中间件链
    assert len(engine.agent._reply_middlewares) == 1


def test_no_budget_by_default() -> None:
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    engine = AgentEngine(load_domain("stock_qa"), EngineConfig(env_files=()))
    assert engine.agent._reply_middlewares == []


def test_default_mode_allows_read_only_tool() -> None:
    registry = ToolRegistry()
    registry.register(_read_data, read_only=True)
    registry.register(_write_data, read_only=False)
    toolkit = registry.build_toolkit()
    basic = toolkit.tool_groups[0]
    tools = {tool.name: tool for tool in basic.tools}

    engine = PermissionEngine(PermissionContext())  # 默认 DEFAULT 模式
    read_decision = asyncio.run(
        engine.check_permission(tools["_read_data"], {"text": "x"}),
    )
    write_decision = asyncio.run(
        engine.check_permission(tools["_write_data"], {"text": "x"}),
    )

    # 只读工具走快速放行；写工具默认不允许直接执行（需人工确认）
    assert read_decision.behavior == PermissionBehavior.ALLOW
    assert write_decision.behavior != PermissionBehavior.ALLOW


def test_registry_preserves_read_only_flag_for_permission() -> None:
    registry = ToolRegistry()
    registry.register(_read_data, read_only=True)
    registry.register(_write_data, read_only=False)
    toolkit = registry.build_toolkit()
    basic = toolkit.tool_groups[0]
    flags = {tool.name: tool.is_read_only for tool in basic.tools}
    assert flags == {"_read_data": True, "_write_data": False}
