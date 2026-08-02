"""股票问答领域工具（业务相关，只读演示数据）。

当前数据层全部使用确定性 mock，不依赖任何外部数据源（Tushare / DuckDB /
AKShare），与 StockRec 项目解耦。后续需要真实数据时，只需替换这些函数
内部实现，引擎与领域包结构不变。
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

_SYMBOL_NAMES = {
    "600519": "贵州茅台",
    "000001": "平安银行",
    "300750": "宁德时代",
}
_NAME_TO_SYMBOL = {name: code for code, name in _SYMBOL_NAMES.items()}


def _resolve_symbol(symbol: str) -> str:
    """支持代码（600519）或名称（贵州茅台）入参。"""
    key = symbol.strip()
    return _NAME_TO_SYMBOL.get(key, key)


def get_stock_price(symbol: str) -> str:
    """返回给定股票代码或名称的当前价格（演示数据，只读工具）。"""
    symbol = _resolve_symbol(symbol)
    hit = _MOCK_PRICES.get(symbol)
    if hit is None:
        available = ", ".join(
            f"{code} {name}" for code, name in _SYMBOL_NAMES.items()
        )
        return f"未知代码/名称 {symbol}，可用: {available}"
    name, price = hit
    return f"{symbol} {name} 当前价格: {price} 元（演示数据）"


def get_stock_financials(symbol: str, year: int = 2024) -> str:
    """返回给定股票某年的财务摘要（PE/PB/ROE，演示数据，只读工具）。"""
    symbol = _resolve_symbol(symbol)
    hit = _MOCK_FINANCIALS.get(symbol, {}).get(str(year))
    if hit is None:
        available = ", ".join(_MOCK_FINANCIALS.get(symbol, {})) or "无"
        return (
            f"暂无可查 {symbol} 的 {year} 年财务数据，"
            f"可用年份: {available}（演示数据）"
        )
    return f"{symbol} {year} 年财务摘要: {hit}（演示数据）"
