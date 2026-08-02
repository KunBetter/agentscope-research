"""多轮会话演示（短期记忆验证）+ 上下文压缩演示。

同一个 ``AgentEngine`` 连续多次 ``run`` 即同一会话（AgentScope Agent 保留
上下文，即短期记忆）；``--compression-demo`` 用极低压缩阈值触发上下文压缩
并输出压缩日志，验证上下文管理配置生效。

用法::

    poc/hello-agent/.venv/bin/python poc/run_conversation.py --domain stock_qa
    poc/hello-agent/.venv/bin/python poc/run_conversation.py --domain weather --compression-demo
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from agentscope.agent import ContextConfig, InjectionConfig

from domains import list_domains, load_domain
from engine.agent_engine import AgentEngine, EngineConfig

DEFAULT_ENV_FILES = [
    Path(__file__).parent / ".env",
    Path(__file__).parent / "hello-agent" / ".env",
]

TURNS = {
    "stock_qa": [
        "贵州茅台（600519）现在多少钱？",
        "那它 2024 年的 ROE 是多少？",
        "我刚才问的是哪只股票？它现在的价格是多少？",
    ],
    "weather": [
        "北京今天天气怎么样？",
        "上海呢？",
        "我刚才问了哪两个城市？",
    ],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="多轮会话 / 上下文压缩演示")
    parser.add_argument("--domain", default="stock_qa", choices=sorted(TURNS))
    parser.add_argument(
        "--compression-demo",
        action="store_true",
        help="用低压缩阈值（0.04/0.02）验证上下文压缩生效",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    context_config = None
    if args.compression_demo:
        logging.basicConfig(level=logging.INFO)
        context_config = ContextConfig(
            trigger_ratio=0.04,
            reserve_ratio=0.02,
        )
        injection_config = InjectionConfig(context_buffer_ratio=0.02)
    else:
        injection_config = None

    engine = AgentEngine(
        load_domain(args.domain),
        EngineConfig(
            env_files=DEFAULT_ENV_FILES,
            context_config=context_config,
            injection_config=injection_config,
        ),
    )
    print(
        f"领域: {args.domain} | 会话: {engine.agent.state.session_id[:8]} "
        f"| 压缩: {'演示(trigger=0.04)' if context_config else '默认'}",
    )

    turns = TURNS[args.domain]
    if args.compression_demo:
        # 短问题上下文太小，重复三轮累计上下文，确保超过压缩阈值
        turns = turns * 3
    for index, question in enumerate(turns, 1):
        print(f"\n--- 第 {index} 轮 ---")
        print(f"Q: {question}")
        try:
            result = engine.run_sync(question)
            print(f"A: {result.text}")
            if result.structured:
                preview = result.structured.get("summary") or str(
                    result.structured,
                )
                print(f"   [结构化] {preview[:200]}")
            if result.usage:
                print(
                    f"[token] in={result.usage.input_tokens} "
                    f"out={result.usage.output_tokens}",
                )
        except Exception as exc:  # noqa: BLE001 - 演示脚本记录失败继续
            print(f"A: [失败] {type(exc).__name__}: {exc}")
            if args.compression_demo:
                print(
                    "   注: 压缩已触发，该轮结构化输出失败——已知限制："
                    "上下文压缩与结构化输出在 agentscope 2.0.5 + DeepSeek "
                    "组合下不稳定，详见 poc/README 已知问题。",
                )

    print("\n=== 短期记忆验证 ===")
    print(
        "同一引擎连续多轮 run = 同一会话（AgentState 保留上下文）；"
        "最后一轮能引用前几轮信息即验证通过。"
    )
    print("=== 新会话 ===")
    engine.reset()
    print(f"reset 后新会话: {engine.agent.state.session_id[:8]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
