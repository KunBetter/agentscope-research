"""API Key / 环境加载（业务无关）。"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from dotenv import load_dotenv


def load_api_key(
    env_var: str = "DEEPSEEK_API_KEY",
    env_files: Iterable[str | Path] = (),
    override: bool = True,
) -> str:
    """按优先级加载 API Key。

    与 hello-agent 保持一致：显式传入的 ``.env`` 文件优先（override 环境
    变量），随后兜底检查环境变量，避免 shell 中旧 key 静默覆盖本地配置。
    """
    for path in env_files:
        file_path = Path(path)
        if file_path.exists():
            load_dotenv(file_path, override=override)

    if os.getenv(env_var):
        return os.environ[env_var]

    raise SystemExit(
        f"缺少 {env_var}：请设置环境变量，或在 .env 中配置"
        "（参考 poc/.env.example）",
    )
