"""天气查询领域工具（业务相关，只读演示数据）。"""

from __future__ import annotations

_MOCK_WEATHER = {
    "北京": ("晴", "28°C", "北风3级"),
    "上海": ("小雨", "26°C", "东南风2级"),
    "广州": ("多云", "31°C", "南风2级"),
}


def get_city_weather(city: str) -> str:
    """返回给定城市的当前天气（演示用模拟数据，只读工具）。"""
    hit = _MOCK_WEATHER.get(city)
    if hit is None:
        return f"未知城市 {city}，可用城市: {', '.join(_MOCK_WEATHER)}"
    condition, temperature, wind = hit
    return f"{city} 当前天气: {condition}，{temperature}，{wind}"
