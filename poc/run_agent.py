"""CLI 入口：按领域包运行业务无关的 Agent 引擎。

用法::

    .venv/bin/python run_agent.py --list-domains
    .venv/bin/python run_agent.py --domain stock_qa
    .venv/bin/python run_agent.py --domain weather --question "北京天气怎么样？"

API Key 加载优先级：poc/.env > poc/hello-agent/.env > ~/git/StockRec/.env
> 环境变量（与 hello_agent 保持一致，本地 .env 优先）。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from domains import DOMAIN_REGISTRY, list_domains, load_domain
from engine.agent_engine import AgentEngine, EngineConfig

DEFAULT_ENV_FILES = [
    Path(__file__).parent / ".env",
    Path(__file__).parent / "hello-agent" / ".env",
    Path.home() / "git" / "StockRec" / ".env",
]

DEFAULT_QUESTIONS = {
    "stock_qa": "贵州茅台（600519）现在多少钱？顺便看一下它的 ROE。",
    "weather": "北京今天天气怎么样？",
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
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.list_domains:
        print("可用领域包：")
        for name in list_domains():
            print(f"  - {name}: {DOMAIN_REGISTRY[name].description}")
        return 0

    domain = load_domain(args.domain)
    engine = AgentEngine(
        domain,
        EngineConfig(
            model_name=args.model,
            env_files=DEFAULT_ENV_FILES,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
