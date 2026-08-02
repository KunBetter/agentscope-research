"""评测基线：按任务集运行领域包，自动比对结构化输出关键字段。

用法::

    poc/hello-agent/.venv/bin/python poc/eval/run_eval.py --domain stock_qa
    poc/hello-agent/.venv/bin/python poc/eval/run_eval.py --domain weather --limit 3
    poc/hello-agent/.venv/bin/python poc/eval/run_eval.py --domain stock_qa --real

- 默认 mock 模式：设置 ``STOCK_TOOLS_MOCK=1``，结果确定，可精确打分；
- ``--real``：使用真实数据源（若可用），只输出结果不计分（数据会变化）；
- 退出码：mock 模式准确率低于阈值（默认 0.8）时返回 1。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # poc/
sys.path.insert(0, str(ROOT))

from domains import load_domain  # noqa: E402
from engine.agent_engine import AgentEngine, EngineConfig  # noqa: E402

DEFAULT_TASKS = {
    "stock_qa": ROOT / "eval" / "tasks" / "stock_qa.jsonl",
    "weather": ROOT / "eval" / "tasks" / "weather.jsonl",
}
ENV_FILES = [
    ROOT / ".env",
    ROOT / "hello-agent" / ".env",
    Path.home() / "git" / "StockRec" / ".env",
]


def _lookup(data: object, path: list[str]) -> list[object]:
    """按路径取结构化输出；``*`` 表示取 dict 全部值。"""
    current = data
    for key in path:
        if isinstance(current, dict):
            if key == "*":
                current = list(current.values())
            else:
                current = current.get(key)
        elif isinstance(current, list):
            current = [
                item.get(key) if isinstance(item, dict) else None
                for item in current
            ]
        else:
            return []
    if isinstance(current, list):
        return current
    return [current]


def _check_pass(check: dict, text: str, structured: dict | None) -> bool:
    """单条检查：字段路径（或 @text）的值包含期望子串（大小写不敏感）。

    支持 ``contains``（单个子串）或 ``any_of``（任一子串命中即通过，
    用于容忍 LLM 对错误场景的不同措辞）。
    """
    path = check["path"]
    expected_list = check.get("any_of") or [check["contains"]]
    expected_list = [str(item).lower() for item in expected_list]
    if path[0] == "@text":
        values = [text]
    else:
        values = _lookup(structured, path) if structured else []
    return any(
        isinstance(value, str)
        and any(expected in value.lower() for expected in expected_list)
        for value in values
    )


def load_tasks(path: Path) -> list[dict]:
    tasks = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks


async def run_tasks(
    domain_name: str,
    tasks: list[dict],
    real_mode: bool,
    budget: float | None,
) -> list[dict]:
    if not real_mode:
        os.environ["STOCK_TOOLS_MOCK"] = "1"
    config = EngineConfig(env_files=ENV_FILES, token_budget=budget)
    results = []
    total = len(tasks)
    for index, task in enumerate(tasks, 1):
        started = time.monotonic()
        engine = AgentEngine(load_domain(domain_name), config)
        try:
            result = await engine.run(task["question"])
            checks = task.get("check", [])
            check_results = [
                _check_pass(check, result.text, result.structured)
                for check in checks
            ]
            passed = None if real_mode else all(check_results)
            entry = {
                "id": task["id"],
                "question": task["question"],
                "passed": passed,
                "checks": check_results,
                "text": result.text,
                "structured": result.structured,
                "usage": (
                    {
                        "input": result.usage.input_tokens,
                        "output": result.usage.output_tokens,
                    }
                    if result.usage
                    else None
                ),
                "seconds": round(time.monotonic() - started, 2),
            }
        except Exception as exc:  # noqa: BLE001 - 单任务失败要记录继续跑
            entry = {
                "id": task["id"],
                "question": task["question"],
                "passed": False,
                "checks": [],
                "error": f"{type(exc).__name__}: {exc}",
                "seconds": round(time.monotonic() - started, 2),
            }
        results.append(entry)
        status = (
            "✓" if entry["passed"] else "✗" if entry["passed"] is False else "~"
        )
        print(
            f"[{index}/{total}] {status} {entry['id']} "
            f"{entry['seconds']}s",
            flush=True,
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent 评测基线")
    parser.add_argument("--domain", default="stock_qa", choices=sorted(DEFAULT_TASKS))
    parser.add_argument("--tasks-file", help="自定义任务集 JSONL（覆盖默认）")
    parser.add_argument("--limit", type=int, help="只跑前 N 条")
    parser.add_argument("--budget", type=float, help="单轮 token 预算")
    parser.add_argument("--real", action="store_true", help="真实数据模式（不计分）")
    parser.add_argument("--threshold", type=float, default=0.8, help="通过率阈值")
    parser.add_argument("--out-dir", default=ROOT / "eval" / "results")
    args = parser.parse_args()

    tasks_file = Path(args.tasks_file) if args.tasks_file else DEFAULT_TASKS[args.domain]
    tasks = load_tasks(tasks_file)
    if args.limit:
        tasks = tasks[: args.limit]

    print(
        f"评测: domain={args.domain} tasks={len(tasks)} "
        f"mode={'real' if args.real else 'mock'}",
    )
    results = asyncio.run(
        run_tasks(args.domain, tasks, real_mode=args.real, budget=args.budget),
    )

    scored = [r for r in results if r["passed"] is not None]
    passed = sum(1 for r in scored if r["passed"])
    total_tokens = sum(
        (r.get("usage") or {}).get("input", 0)
        + (r.get("usage") or {}).get("output", 0)
        for r in results
    )
    print(
        f"\n通过: {passed}/{len(scored)}"
        + (f" | 准确率: {passed / len(scored):.1%}" if scored else "")
        + f" | token 合计: {total_tokens}",
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"{args.domain}_{'real' if args.real else 'mock'}_{stamp}.json"
    out_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"结果已保存: {out_path}")

    if scored and not args.real:
        return 0 if passed / len(scored) >= args.threshold else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
