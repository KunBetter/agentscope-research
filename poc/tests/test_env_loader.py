"""API Key 加载离线测试（不发起网络请求）。"""

import pytest

from engine.env_loader import MissingApiKeyError, load_api_key


def test_missing_key_raises_missing_api_key_error(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError):
        load_api_key(env_files=())


def test_env_file_priority_over_environment(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("DEEPSEEK_API_KEY=from-file\n", encoding="utf-8")
    assert load_api_key(env_files=[env_file]) == "from-file"


def test_environment_variable_as_fallback(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "from-env")
    assert load_api_key(env_files=()) == "from-env"
