"""评测检查项离线测试（不调用模型）。"""

from eval.run_eval import _check_pass


def _structured(**kwargs) -> dict:
    return kwargs


def test_contains_check() -> None:
    check = {"path": ["price"], "contains": "1420.50"}
    assert _check_pass(check, "text", _structured(price="1420.50 元"))
    assert not _check_pass(check, "text", _structured(price="1350.60 元"))


def test_any_of_check() -> None:
    check = {"path": ["summary"], "any_of": ["未知城市", "不存在"]}
    assert _check_pass(check, "text", _structured(summary="天气数据中不存在东京"))
    assert not _check_pass(check, "text", _structured(summary="天气晴朗"))


def test_paths_check_any_field_matches() -> None:
    check = {
        "paths": [["price"], ["summary"]],
        "any_of": ["未知代码", "无法获取"],
    }
    assert _check_pass(
        check,
        "text",
        _structured(price=None, summary="查询失败：未知代码 999999"),
    )
    assert _check_pass(
        check,
        "text",
        _structured(price="未知代码/名称 999999", summary=""),
    )
    assert not _check_pass(
        check,
        "text",
        _structured(price=None, summary="价格 1420.50 元"),
    )
