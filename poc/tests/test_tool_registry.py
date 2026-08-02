"""工具注册表离线测试。"""

from engine.tool_registry import ToolRegistry


def _echo(text: str) -> str:
    """原样返回输入。"""
    return text


def _greeting() -> str:
    """问候语。"""
    return "hi"


def test_register_function_and_expose_name() -> None:
    registry = ToolRegistry()
    registry.register(_echo, name="echo_tool", read_only=True)
    assert registry.tool_names == ("echo_tool",)
    assert registry.specs[0].read_only is True


def test_register_as_decorator() -> None:
    registry = ToolRegistry()

    @registry.register(read_only=True)
    def greeting() -> str:
        """问候。"""
        return "hi"

    assert registry.tool_names == ("greeting",)


def test_build_toolkit_preserves_metadata_and_groups() -> None:
    registry = ToolRegistry()
    registry.register(
        _echo,
        name="echo",
        read_only=True,
        group="data",
        group_description="数据查询（只读）",
    )
    registry.register(_greeting, name="greeting")

    toolkit = registry.build_toolkit()
    group_names = {group.name for group in toolkit.tool_groups}
    assert group_names == {"basic", "data"}

    basic = next(g for g in toolkit.tool_groups if g.name == "basic")
    data = next(g for g in toolkit.tool_groups if g.name == "data")
    assert basic.tools[0].name == "greeting"
    assert data.tools[0].name == "echo"
    assert data.tools[0].is_read_only is True


def test_non_basic_group_requires_description() -> None:
    registry = ToolRegistry()
    try:
        registry.register(_echo, group="data")
    except ValueError:
        pass
    else:
        raise AssertionError("非 basic 工具组缺少描述时应抛 ValueError")
