"""Agent 引擎（业务无关）：领域包 → 模型 + 工具 + Agent 的装配与执行。"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentscope.agent import Agent, ContextConfig, InjectionConfig, ModelConfig
from agentscope.credential import DeepSeekCredential
from agentscope.event import (
    ModelCallEndEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
)
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
    context_config: ContextConfig | None = None
    """上下文压缩配置；None 表示使用框架默认（trigger_ratio=0.8）。"""
    injection_config: InjectionConfig | None = None
    """运行时状态注入配置（时间/上下文占用）；None 使用框架默认。"""
    model_config: ModelConfig | None = None
    """完整模型配置（重试/回退）；与 max_retries/fallback_model 二选一。"""
    max_retries: int | None = None
    """模型调用重试次数简写（转成 ModelConfig.max_retries）。"""
    fallback_model: str | None = None
    """回退模型名简写（同凭据构建，转成 ModelConfig.fallback_model）。"""

    def __post_init__(self) -> None:
        self.env_files = tuple(Path(p) for p in self.env_files)


@dataclass
class AgentResult:
    """一轮问答的结果。"""

    text: str
    structured: dict | None = None
    usage: Any | None = None
    tool_calls: list["ToolCallRecord"] | None = None


@dataclass
class TokenUsage:
    """一轮问答消耗的 token（从模型调用事件聚合，结构化输出模式下也有值）。"""

    input_tokens: int
    output_tokens: int


@dataclass
class ToolCallRecord:
    """一次工具调用的记录（名称、耗时、是否与其他调用并行）。"""

    name: str
    call_id: str
    started_at: float
    ended_at: float | None = None
    duration: float = 0.0
    parallel: bool = False


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
        self.agent = self._build_agent()

    def _build_agent(self) -> Agent:
        middlewares: list = []
        if self.config.token_budget is not None:
            from agentscope.middleware import ReplyBudgetControlMiddleware

            middlewares.append(
                ReplyBudgetControlMiddleware(
                    token_budget=self.config.token_budget,
                ),
            )
        return Agent(
            name=self.domain.name,
            system_prompt=self.domain.system_prompt,
            model=self.model,
            toolkit=self.toolkit,
            middlewares=middlewares,
            context_config=self.config.context_config,
            injection_config=self.config.injection_config,
            model_config=self._model_config,
        )

    def reset(self) -> None:
        """开启全新会话：重建 Agent（新 AgentState），模型与工具不变。"""
        self.agent = self._build_agent()

    def _build_model(self) -> DeepSeekChatModel:
        api_key = load_api_key(
            env_var=self.config.api_key_env_var,
            env_files=self.config.env_files,
        )
        credential = DeepSeekCredential(api_key=api_key)
        parameters = DeepSeekChatModel.Parameters(
            thinking_enable=self.config.thinking_enable,
            max_tokens=self.config.max_tokens,
        )
        self._model_config = self.config.model_config
        if self._model_config is None and (
            self.config.max_retries is not None
            or self.config.fallback_model
        ):
            model_config_kwargs: dict[str, Any] = {}
            if self.config.max_retries is not None:
                model_config_kwargs["max_retries"] = self.config.max_retries
            if self.config.fallback_model:
                model_config_kwargs["fallback_model"] = DeepSeekChatModel(
                    credential=credential,
                    model=self.config.fallback_model,
                    parameters=parameters,
                    stream=self.config.stream,
                )
            self._model_config = ModelConfig(**model_config_kwargs)
        return DeepSeekChatModel(
            credential=credential,
            model=self.config.model_name,
            parameters=parameters,
            stream=self.config.stream,
        )

    async def run(self, user_input: str) -> AgentResult:
        """异步执行一轮问答；若领域包声明了 output_schema 则启用结构化输出。"""
        input_tokens = 0
        output_tokens = 0
        final_msg: Msg | None = None
        tool_calls: list[ToolCallRecord] = []
        call_starts: dict[str, ToolCallRecord] = {}
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
            elif isinstance(event, ToolCallStartEvent):
                record = ToolCallRecord(
                    name=event.tool_call_name,
                    call_id=event.tool_call_id,
                    started_at=time.monotonic(),
                )
                call_starts[event.tool_call_id] = record
                tool_calls.append(record)
            elif isinstance(event, ToolCallEndEvent):
                record = call_starts.get(event.tool_call_id)
                if record is not None:
                    record.ended_at = time.monotonic()
                    record.duration = record.ended_at - record.started_at
        if final_msg is None:
            raise RuntimeError("Agent 未产生最终回复")
        for record in tool_calls:
            if record.ended_at is None:
                continue
            record.parallel = any(
                other is not record
                and other.ended_at is not None
                and record.started_at < other.ended_at
                and other.started_at < record.ended_at
                for other in tool_calls
            )
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
            tool_calls=tool_calls or None,
        )

    def run_sync(self, user_input: str) -> AgentResult:
        """同步执行一轮问答（内部 asyncio.run）。"""
        return asyncio.run(self.run(user_input))
