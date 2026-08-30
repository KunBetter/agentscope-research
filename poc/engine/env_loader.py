"""API Key / 环境加载（业务无关）。"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from dotenv import load_dotenv


class MissingApiKeyError(RuntimeError):
    """API Key 未配置（环境变量与所有 .env 文件均缺失）。

    抛异常而非 SystemExit：让调用方（CLI / 评测 / 库用户）自行决定
    如何展示与退出，避免在引擎层硬编码进程行为。
    """


POC_ROOT = Path(__file__).resolve().parents[1]


def default_env_files() -> tuple[Path, ...]:
    """poc 默认 .env 查找顺序（按优先级）：poc/.env → poc/hello-agent/.env。

    所有 CLI / 评测脚本共用此定义，避免多处重复维护环境文件顺序。
    """
    return (POC_ROOT / ".env", POC_ROOT / "hello-agent" / ".env")


def load_api_key(
    env_var: str = "DEEPSEEK_API_KEY",
    env_files: Iterable[str | Path] = (),
    override: bool = True,
) -> str:
    """按优先级加载 API Key。

    与 hello-agent 保持一致：显式传入的 ``.env`` 文件优先（override 环境
    变量），随后兜底检查环境变量，避免 shell 中旧 key 静默覆盖本地配置。
    缺失时抛 :class:`MissingApiKeyError`。
    """
    for path in env_files:
        file_path = Path(path)
        if file_path.exists():
            load_dotenv(file_path, override=override)

    key = os.getenv(env_var)
    if key:
        return key

    raise MissingApiKeyError(
        f"缺少 {env_var}：请设置环境变量，或在 .env 中配置"
        "（参考 poc/.env.example）",
    )
