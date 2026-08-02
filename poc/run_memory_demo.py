"""文件型长期记忆演示（跨会话持久化）。

会话 1：让 Agent 记住偏好（AgenticMemoryMiddleware 通过 Write 工具写入
MEMORY.md）；会话 2：全新引擎 + 同一记忆目录，验证跨会话取回。

用法::

    poc/hello-agent/.venv/bin/python poc/run_memory_demo.py
    poc/hello-agent/.venv/bin/python poc/run_memory_demo.py --memory-dir poc/memory/stock_qa --reset
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from domains import load_domain
from engine.agent_engine import AgentEngine, EngineConfig

DEFAULT_ENV_FILES = [
    Path(__file__).parent / ".env",
    Path(__file__).parent / "hello-agent" / ".env",
]

DEFAULT_MEMORY_DIR = Path(__file__).parent / "memory" / "stock_qa"


def _engine(memory_dir: Path) -> AgentEngine:
    return AgentEngine(
        load_domain("stock_qa"),
        EngineConfig(env_files=DEFAULT_ENV_FILES, memory_dir=str(memory_dir)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="文件型长期记忆演示")
    parser.add_argument("--memory-dir", default=str(DEFAULT_MEMORY_DIR))
    parser.add_argument("--reset", action="store_true", help="清空记忆目录")
    args = parser.parse_args()
    memory_dir = Path(args.memory_dir)
    if args.reset:
        shutil.rmtree(memory_dir, ignore_errors=True)

    print(f"记忆目录: {memory_dir}\n")

    print("=== 会话 1（写入记忆） ===")
    session1 = _engine(memory_dir)
    result1 = session1.run_sync(
        "请记住：我的投资目标是长期持有 600519，不要频繁交易。",
    )
    print(f"Q: 请记住...\nA: {result1.text}")
    if result1.structured:
        print(f"   [结构化] {result1.structured.get('summary', '')[:120]}")
    result2 = session1.run_sync("我的投资目标是什么？")
    print(f"Q: 我的投资目标是什么？\nA: {result2.structured.get('summary', result2.text)[:160]}")

    print("\n=== 会话 2（全新引擎 + 同一记忆目录，跨会话取回） ===")
    session2 = _engine(memory_dir)
    result3 = session2.run_sync("我们上次聊过我的投资目标，还记得吗？")
    print(f"Q: 还记得吗？\nA: {result3.structured.get('summary', result3.text)[:160]}")

    memory_files = sorted(
        path.relative_to(memory_dir)
        for path in memory_dir.rglob("*")
        if path.is_file()
    )
    print(f"\n记忆文件: {[str(p) for p in memory_files] or '（无，保存未触发）'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
