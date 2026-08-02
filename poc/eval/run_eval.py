"""评测基线：按任务集运行领域包，自动比对结构化输出关键字段。

用法::

    poc/hello-agent/.venv/bin/python poc/eval/run_eval.py --domain stock_qa
    poc/hello-agent/.venv/bin/python poc/eval/run_eval.py --domain weather --limit 3

- 数据层为确定性 mock，结果可精确打分、可回归对比；
- 退出码：准确率低于阈值（默认 0.8）时返回 1。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # poc/
sys.path.insert(0, str(ROOT))

from domains import load_domain  # noqa: E402
from engine.agent_engine import AgentEngine, EngineConfig  # noqa: E402

DEFAULT_TASKS = {
    "stock_qa": ROOT / "eval" / "tasks" / "stock_qa.jsonl",
    "todo": ROOT / "eval" / "tasks" / "todo.jsonl",
    "weather": ROOT / "eval" / "tasks" / "weather.jsonl",
}
ENV_FILES = [
    ROOT / ".env",
    ROOT / "hello-agent" / ".env",
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
            if key == "*":
                current = list(current)
            else:
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
    用于容忍 LLM 对错误场景的不同措辞）；``paths``（多个字段路径，
    任一字段命中即通过，用于模型把错误信息放不同字段的情况）。
    """
    expected_list = check.get("any_of") or [check["contains"]]
    expected_list = [str(item).lower() for item in expected_list]

    paths = check.get("paths") or [check["path"]]
    for path in paths:
        if path[0] == "@text":
            values = [text]
        else:
            values = _lookup(structured, path) if structured else []
        if any(
            isinstance(value, str)
            and any(expected in value.lower() for expected in expected_list)
            for value in values
        ):
            return True
    return False


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
    budget: float | None,
) -> list[dict]:
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
            entry = {
                "id": task["id"],
                "question": task["question"],
                "passed": all(check_results),
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
        status = "✓" if entry["passed"] else "✗"
        print(
            f"[{index}/{total}] {status} {entry['id']} "
            f"{entry['seconds']}s",
            flush=True,
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent 评测基线（mock 数据）")
    parser.add_argument(
        "--domain",
        default="stock_qa",
        choices=sorted(DEFAULT_TASKS),
    )
    parser.add_argument("--tasks-file", help="自定义任务集 JSONL（覆盖默认）")
    parser.add_argument("--limit", type=int, help="只跑前 N 条")
    parser.add_argument("--budget", type=float, help="单轮 token 预算")
    parser.add_argument("--threshold", type=float, default=0.8, help="通过率阈值")
    parser.add_argument("--out-dir", default=ROOT / "eval" / "results")
    parser.add_argument(
        "--baseline",
        help="对比上次结果 JSON：输出 修复/回归/新增 差异，有回归则退出码 1",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="跑全部领域并输出汇总表（跨领域一致性对比）",
    )
    args = parser.parse_args()

    if args.all:
        summary = []
        any_fail = False
        for domain_name in sorted(DEFAULT_TASKS):
            tasks = load_tasks(DEFAULT_TASKS[domain_name])
            print(f"\n=== {domain_name} ===")
            results = asyncio.run(
                run_tasks(domain_name, tasks, budget=args.budget),
            )
            passed_n = sum(1 for r in results if r["passed"])
            accuracy = passed_n / len(results)
            tokens = sum(
                (r.get("usage") or {}).get("input", 0)
                + (r.get("usage") or {}).get("output", 0)
                for r in results
            )
            summary.append(
                (domain_name, passed_n, len(results), accuracy, tokens),
            )
            stamp = time.strftime("%Y%m%d-%H%M%S")
            out_path = Path(args.out_dir) / f"{domain_name}_mock_{stamp}.json"
            out_path.write_text(
                json.dumps(results, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            if accuracy < args.threshold:
                any_fail = True
        print("\n=== 跨领域汇总 ===")
        print(f"{'领域':<10}{'通过':<8}{'准确率':<10}{'token':<10}")
        total_pass = 0
        total_tasks = 0
        total_tokens = 0
        for domain_name, passed_n, total, accuracy, tokens in summary:
            total_pass += passed_n
            total_tasks += total
            total_tokens += tokens
            print(
                f"{domain_name:<10}{passed_n}/{total:<6}"
                f"{accuracy:<10.1%}{tokens:<10}",
            )
        print(
            f"合计      {total_pass}/{total_tasks} "
            f"{total_pass / total_tasks:.1%} | token {total_tokens}",
        )
        return 1 if any_fail else 0

    tasks_file = (
        Path(args.tasks_file) if args.tasks_file else DEFAULT_TASKS[args.domain]
    )
    tasks = load_tasks(tasks_file)
    if args.limit:
        tasks = tasks[: args.limit]

    print(f"评测: domain={args.domain} tasks={len(tasks)} mode=mock")
    results = asyncio.run(run_tasks(args.domain, tasks, budget=args.budget))

    passed = sum(1 for r in results if r["passed"])
    total_tokens = sum(
        (r.get("usage") or {}).get("input", 0)
        + (r.get("usage") or {}).get("output", 0)
        for r in results
    )
    print(
        f"\n通过: {passed}/{len(results)}"
        f" | 准确率: {passed / len(results):.1%}"
        f" | token 合计: {total_tokens}",
    )

    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        base_map = {entry["id"]: entry["passed"] for entry in baseline}
        new_map = {entry["id"]: entry["passed"] for entry in results}
        fixed = [
            task_id
            for task_id in base_map
            if task_id in new_map
            and base_map[task_id] is False
            and new_map[task_id] is True
        ]
        regressed = [
            task_id
            for task_id in base_map
            if task_id in new_map
            and base_map[task_id] is True
            and new_map[task_id] is False
        ]
        new_tasks = [
            task_id for task_id in new_map if task_id not in base_map
        ]
        print(
            f"\n基线对比({Path(args.baseline).name}): "
            f"修复 {len(fixed)} | 回归 {len(regressed)} | 新增 {len(new_tasks)}",
        )
        for task_id in fixed:
            print(f"  ✓ 修复 {task_id}")
        for task_id in regressed:
            print(f"  ✗ 回归 {task_id}")
        for task_id in new_tasks:
            print(f"  + 新增 {task_id}")
        if regressed:
            return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"{args.domain}_mock_{stamp}.json"
    out_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"结果已保存: {out_path}")

    return 0 if passed / len(results) >= args.threshold else 1


if __name__ == "__main__":
    raise SystemExit(main())
