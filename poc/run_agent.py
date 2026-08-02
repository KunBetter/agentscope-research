"""CLI 入口：按领域包运行业务无关的 Agent 引擎。

用法::

    .venv/bin/python run_agent.py --list-domains
    .venv/bin/python run_agent.py --domain stock_qa
    .venv/bin/python run_agent.py --domain weather --question "北京天气怎么样？"

API Key 加载优先级：poc/.env > poc/hello-agent/.env > 环境变量
（与 hello_agent 保持一致，本地 .env 优先）。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from domains import DOMAIN_REGISTRY, list_domains, load_domain
from engine.agent_engine import AgentEngine, EngineConfig

DEFAULT_ENV_FILES = [
    Path(__file__).parent / ".env",
    Path(__file__).parent / "hello-agent" / ".env",
]

DEFAULT_QUESTIONS = {
    "stock_qa": "贵州茅台（600519）现在多少钱？顺便看一下它的 ROE。",
    "weather": "北京今天天气怎么样？",
    "todo": "现在有哪些待办？",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="业务无关 Agent 引擎演示（engine + domains + tools）",
    )
    parser.add_argument(
        "--domain",
        default="stock_qa",
        choices=sorted(DOMAIN_REGISTRY),
        help="业务领域包",
    )
    parser.add_argument("--question", help="用户问题（默认用该领域示例问题）")
    parser.add_argument(
        "--list-domains",
        action="store_true",
        help="列出可用领域包",
    )
    parser.add_argument(
        "--model",
        default="deepseek-v4-flash",
        help="模型名（默认 deepseek-v4-flash）",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=None,
        help="单轮 token 预算（启用 ReplyBudgetControlMiddleware，默认关闭）",
    )
    parser.add_argument(
        "--context-trigger-ratio",
        type=float,
        default=None,
        help="上下文压缩触发阈值（ContextConfig.trigger_ratio，默认 0.8）",
    )
    parser.add_argument(
        "--context-reserve-ratio",
        type=float,
        default=None,
        help="压缩时保留比例（ContextConfig.reserve_ratio，默认 0.1）",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help="模型调用重试次数（ModelConfig.max_retries）",
    )
    parser.add_argument(
        "--fallback-model",
        default=None,
        help="回退模型名（同凭据构建，如 deepseek-v4-pro）",
    )
    parser.add_argument(
        "--write-confirmation",
        choices=["deny", "confirm"],
        default="deny",
        help="写工具人工确认策略：deny 默认拒绝 / confirm 自动确认",
    )
    parser.add_argument(
        "--memory-dir",
        default=None,
        help="文件型长期记忆目录（启用 AgenticMemoryMiddleware）",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.list_domains:
        print("可用领域包：")
        for name in list_domains():
            print(f"  - {name}: {DOMAIN_REGISTRY[name].description}")
        return 0

    domain = load_domain(args.domain)
    context_config = None
    if (
        args.context_trigger_ratio is not None
        or args.context_reserve_ratio is not None
    ):
        from agentscope.agent import ContextConfig

        context_config = ContextConfig(
            trigger_ratio=(
                args.context_trigger_ratio
                if args.context_trigger_ratio is not None
                else 0.8
            ),
            reserve_ratio=(
                args.context_reserve_ratio
                if args.context_reserve_ratio is not None
                else 0.1
            ),
        )
    engine = AgentEngine(
        domain,
        EngineConfig(
            model_name=args.model,
            env_files=DEFAULT_ENV_FILES,
            token_budget=args.budget,
            context_config=context_config,
            max_retries=args.max_retries,
            fallback_model=args.fallback_model,
            write_confirmation=args.write_confirmation,
            memory_dir=args.memory_dir,
        ),
    )

    question = args.question or DEFAULT_QUESTIONS[args.domain]
    print(
        f"领域包: {domain.name} | "
        f"引擎工具: {', '.join(engine.registry.tool_names)}",
    )

    result = engine.run_sync(question)

    print(f"\n=== {domain.name} 回答 ===")
    print(result.text)
    if result.structured:
        print("\n=== 结构化输出 ===")
        for key, value in result.structured.items():
            print(f"  {key}: {value}")
    if result.usage:
        print(
            f"\n[token] input={result.usage.input_tokens} "
            f"output={result.usage.output_tokens}",
        )
    if result.tool_calls:
        parallel_count = sum(1 for call in result.tool_calls if call.parallel)
        calls = ", ".join(
            f"{call.name}({call.duration:.1f}s)"
            + ("*" if call.parallel else "")
            for call in result.tool_calls
        )
        print(f"[工具调用] {calls}" + (f"（并行 {parallel_count} 个）" if parallel_count else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
