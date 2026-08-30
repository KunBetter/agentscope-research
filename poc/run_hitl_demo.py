"""HITL 最小确认流演示（写工具 + 人工确认/拒绝）。

用法::

    # 默认 deny：add_todo 被拒绝，工具不执行
    poc/hello-agent/.venv/bin/python poc/run_hitl_demo.py

    # confirm：add_todo 自动确认并执行
    poc/hello-agent/.venv/bin/python poc/run_hitl_demo.py --confirm
"""

from __future__ import annotations

import argparse
import sys

from domains import load_domain
from engine.agent_engine import AgentEngine, EngineConfig
from engine.env_loader import MissingApiKeyError, default_env_files

QUESTION = "帮我加一条待办：周五复盘贵州茅台"


def main() -> int:
    parser = argparse.ArgumentParser(description="HITL 写工具确认流演示")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="自动确认写操作（默认 deny 拒绝）",
    )
    args = parser.parse_args()

    policy = "confirm" if args.confirm else "deny"
    try:
        engine = AgentEngine(
            load_domain("todo"),
            EngineConfig(env_files=default_env_files(), write_confirmation=policy),
        )
    except MissingApiKeyError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2
    print(f"策略: {policy} | 工具: {', '.join(engine.registry.tool_names)}")
    print(f"Q: {QUESTION}\n")

    result = engine.run_sync(QUESTION)

    print(f"A: {result.text}")
    if result.structured:
        print(f"   [结构化] {result.structured}")
    if result.tool_calls:
        for call in result.tool_calls:
            status = (
                f"confirmed={call.confirmed}"
                if call.confirmed is not None
                else "read-only"
            )
            print(f"   [工具] {call.name} {status} ({call.duration:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
