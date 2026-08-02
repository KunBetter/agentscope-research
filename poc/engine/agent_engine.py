"""Agent 引擎（业务无关）：领域包 → 模型 + 工具 + Agent 的装配与执行。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentscope.agent import Agent
from agentscope.credential import DeepSeekCredential
from agentscope.event import ModelCallEndEvent
from agentscope.message import Msg, UserMsg
from agentscope.model import DeepSeekChatModel

from .domain import DomainPackage
from .env_loader import load_api_key
from .tool_registry import ToolRegistry


@dataclass
class EngineConfig:
    """引擎装配参数（业务无关，可按环境覆盖）。"""

    model_name: str = "deepseek-v4-flash"
    api_key_env_var: str = "DEEPSEEK_API_KEY"
    env_files: tuple[str | Path, ...] = ()
    """按优先级排列的 .env 文件路径（先出现者优先）。"""
    thinking_enable: bool = True
    max_tokens: int = 2000
    stream: bool = True
    token_budget: float | None = None
    """单轮 token 预算；None 表示不启用预算控制（2.0.5 用
    ``ReplyBudgetControlMiddleware``）。"""

    def __post_init__(self) -> None:
        self.env_files = tuple(Path(p) for p in self.env_files)


@dataclass
class AgentResult:
    """一轮问答的结果。"""

    text: str
    structured: dict | None = None
    usage: Any | None = None


@dataclass
class TokenUsage:
    """一轮问答消耗的 token（从模型调用事件聚合，结构化输出模式下也有值）。"""

    input_tokens: int
    output_tokens: int


class AgentEngine:
    """把 :class:`DomainPackage` 装配为可运行的 Agent。

    装配顺序：
    1. 领域包向 ToolRegistry 注册工具（业务注入）；
    2. 引擎把注册表构建为 Toolkit（统一转换）；
    3. 引擎装配模型与 Agent（业务无关）。
    """

    def __init__(
        self,
        domain: DomainPackage,
        config: EngineConfig | None = None,
    ) -> None:
        self.domain = domain
        self.config = config or EngineConfig()
        self.registry = ToolRegistry()
        domain.register_tools(self.registry)
        self.toolkit = self.registry.build_toolkit()
        self.model = self._build_model()
        middlewares: list = []
        if self.config.token_budget is not None:
            from agentscope.middleware import ReplyBudgetControlMiddleware

            middlewares.append(
                ReplyBudgetControlMiddleware(
                    token_budget=self.config.token_budget,
                ),
            )
        self.agent = Agent(
            name=domain.name,
            system_prompt=domain.system_prompt,
            model=self.model,
            toolkit=self.toolkit,
            middlewares=middlewares,
        )

    def _build_model(self) -> DeepSeekChatModel:
        api_key = load_api_key(
            env_var=self.config.api_key_env_var,
            env_files=self.config.env_files,
        )
        return DeepSeekChatModel(
            credential=DeepSeekCredential(api_key=api_key),
            model=self.config.model_name,
            parameters=DeepSeekChatModel.Parameters(
                thinking_enable=self.config.thinking_enable,
                max_tokens=self.config.max_tokens,
            ),
            stream=self.config.stream,
        )

    async def run(self, user_input: str) -> AgentResult:
        """异步执行一轮问答；若领域包声明了 output_schema 则启用结构化输出。"""
        input_tokens = 0
        output_tokens = 0
        final_msg: Msg | None = None
        async for event in self.agent.reply_stream(
            UserMsg(name="user", content=user_input),
            structured_schema=self.domain.output_schema,
            yield_final_msg=True,
        ):
            if isinstance(event, ModelCallEndEvent):
                input_tokens += event.input_tokens
                output_tokens += event.output_tokens
            elif isinstance(event, Msg):
                final_msg = event
        if final_msg is None:
            raise RuntimeError("Agent 未产生最终回复")
        usage = (
            TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            if (input_tokens or output_tokens)
            else None
        )
        return AgentResult(
            text=final_msg.get_text_content(),
            structured=final_msg.structured_output,
            usage=usage,
        )

    def run_sync(self, user_input: str) -> AgentResult:
        """同步执行一轮问答（内部 asyncio.run）。"""
        return asyncio.run(self.run(user_input))
