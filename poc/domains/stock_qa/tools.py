"""股票问答领域工具（业务相关，只读）。

数据源策略（保守优先，三级降级）：
1. 强制 mock：环境变量 ``STOCK_TOOLS_MOCK=1`` 时只用演示数据（评测基线，
   保证确定性）；
2. Tushare 真实数据：已安装 ``tushare`` 且配置 ``TUSHARE_TOKEN`` 时优先
   （对应规划 M1：Tushare 财务/收盘价查询）；
3. 自动回退：无依赖 / 无 token / 网络异常时回退演示数据，并在结果中标注。

替换或扩展为 DuckDB K 线 / AKShare 行情时，只需改这些函数内部实现，
引擎与领域包结构不变。
"""

from __future__ import annotations

import os

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


def _force_mock() -> bool:
    """评测基线用：显式锁定演示数据，保证结果确定性。"""
    return os.getenv("STOCK_TOOLS_MOCK", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _resolve_symbol(symbol: str) -> str:
    """支持代码（600519）或名称（贵州茅台）入参。"""
    key = symbol.strip()
    return _NAME_TO_SYMBOL.get(key, key)


def _ts_code(symbol: str) -> str:
    """A 股代码 → Tushare ts_code（6 开头为沪市，其余按深市处理）。"""
    return f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"


def _tushare_pro() -> object | None:
    """返回 tushare pro 实例；未安装 / 无 token / 强制 mock 时返回 None。"""
    if _force_mock():
        return None
    try:
        import tushare as ts
    except ImportError:
        return None
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        return None
    ts.set_token(token)
    return ts.pro_api()


def _fmt_number(value: object) -> str:
    """把 Tushare 数值格式化为两位小数；NaN/None 返回 N/A。"""
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "N/A"
    if number != number:  # NaN
        return "N/A"
    return f"{number:.2f}"


def _mock_marker() -> str:
    return "演示数据" if _force_mock() else "演示数据（Tushare 不可用，已回退）"


def get_stock_price(symbol: str) -> str:
    """返回给定股票代码或名称的最新价格；优先 Tushare 收盘价，失败回退演示数据（只读工具）。"""
    symbol = _resolve_symbol(symbol)
    pro = _tushare_pro()
    if pro is not None:
        try:
            df = pro.daily(
                ts_code=_ts_code(symbol),
                fields="ts_code,trade_date,close",
                limit=1,
            )
            if df is not None and not df.empty:
                row = df.iloc[0]
                name = _SYMBOL_NAMES.get(symbol, symbol)
                return (
                    f"{symbol} {name} 最新收盘价: {row['close']:.2f} 元"
                    f"（Tushare {row['trade_date']}）"
                )
        except Exception:  # noqa: BLE001 - 工具层兜底，任何失败都回退
            pass

    hit = _MOCK_PRICES.get(symbol)
    if hit is None:
        available = ", ".join(
            f"{code} {name}" for code, name in _SYMBOL_NAMES.items()
        )
        return f"未知代码/名称 {symbol}，可用: {available}"
    name, price = hit
    return f"{symbol} {name} 当前价格: {price} 元（{_mock_marker()}）"


def get_stock_financials(symbol: str, year: int = 2024) -> str:
    """返回给定股票某年的财务摘要（PE_TTM/PB/ROE）；优先 Tushare，失败回退演示数据（只读工具）。"""
    symbol = _resolve_symbol(symbol)
    pro = _tushare_pro()
    if pro is not None:
        try:
            code = _ts_code(symbol)
            daily_basic = pro.daily_basic(
                ts_code=code,
                fields="ts_code,trade_date,pe_ttm,pb",
                limit=1,
            )
            indicator = pro.fina_indicator(
                ts_code=code,
                period=f"{year}1231",
                fields="ts_code,end_date,roe_yearly",
            )
            pe = pb = roe = None
            if daily_basic is not None and not daily_basic.empty:
                row = daily_basic.iloc[0]
                pe, pb = row["pe_ttm"], row["pb"]
            if indicator is not None and not indicator.empty:
                roe = indicator.iloc[0]["roe_yearly"]
            if pe is not None or pb is not None or roe is not None:
                return (
                    f"{symbol} {year} 年财务摘要: "
                    f"PE_TTM={_fmt_number(pe)}, PB={_fmt_number(pb)}, "
                    f"ROE={_fmt_number(roe)}%（Tushare）"
                )
        except Exception:  # noqa: BLE001 - 工具层兜底，任何失败都回退
            pass

    hit = _MOCK_FINANCIALS.get(symbol, {}).get(str(year))
    if hit is None:
        available = ", ".join(_MOCK_FINANCIALS.get(symbol, {})) or "无"
        return (
            f"暂无可查 {symbol} 的 {year} 年财务数据，"
            f"可用年份: {available}（{_mock_marker()}）"
        )
    return f"{symbol} {year} 年财务摘要: {hit}（{_mock_marker()}）"
