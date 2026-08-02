"""股票问答领域工具（业务相关，只读演示数据）。

替换为真实数据源（Tushare / DuckDB / AKShare）时只需改这些函数内部实现，
引擎与领域包结构不变 —— 对应规划 M1。
"""

from __future__ import annotations

_MOCK_PRICES = {
    "600519": ("贵州茅台", "1420.50"),
    "000001": ("平安银行", "11.23"),
    "300750": ("宁德时代", "198.76"),
}

_MOCK_FINANCIALS = {
    "600519": {
        "2024": "PE=23.4, PB=7.8, ROE=33.1%",
        "2023": "PE=28.1, PB=9.2, ROE=32.7%",
    },
    "000001": {
        "2024": "PE=5.2, PB=0.6, ROE=11.8%",
        "2023": "PE=4.9, PB=0.6, ROE=11.2%",
    },
    "300750": {
        "2024": "PE=21.6, PB=4.3, ROE=21.2%",
        "2023": "PE=24.8, PB=5.1, ROE=20.6%",
    },
}


def get_stock_price(symbol: str) -> str:
    """返回给定股票代码的当前价格（演示用模拟数据，只读工具）。"""
    hit = _MOCK_PRICES.get(symbol)
    if hit is None:
        return f"未知代码 {symbol}，可用代码: {', '.join(_MOCK_PRICES)}"
    name, price = hit
    return f"{symbol} {name} 当前价格: {price} 元"


def get_stock_financials(symbol: str, year: int = 2024) -> str:
    """返回给定股票某年的财务摘要（PE/PB/ROE，演示模拟数据，只读工具）。"""
    hit = _MOCK_FINANCIALS.get(symbol, {}).get(str(year))
    if hit is None:
        return (
            f"暂无可查 {symbol} 的 {year} 年财务数据，"
            f"可用: {', '.join(_MOCK_FINANCIALS.get(symbol, {}))}"
        )
    return f"{symbol} {year} 年财务摘要: {hit}"
