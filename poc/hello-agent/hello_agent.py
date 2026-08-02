"""AgentScope 2.0.5 最小场景：单个 ReActAgent + DeepSeek + 一个只读工具。

验证目标（最小闭环）：
  1. agentscope 2.0.5 安装可用；
  2. DeepSeek 模型接入（含 CoT thinking 与流式）；
  3. 自定义 Tool 注册 + 工具调用闭环（Agent 先调工具、再基于结果作答）。

运行：
  .venv/bin/python hello_agent.py

API Key 来源（按顺序）：
  1. 环境变量 DEEPSEEK_API_KEY；
  2. 本目录 .env；
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from agentscope.agent import Agent
from agentscope.credential import DeepSeekCredential
from agentscope.message import UserMsg
from agentscope.model import DeepSeekChatModel
from agentscope.tool import FunctionTool, Toolkit

DEEPSEEK_MODEL = "deepseek-v4-flash"
FALLBACK_ENV_PATHS = [
    Path(__file__).parent / ".env",
]


def get_stock_price(symbol: str) -> str:
    """返回给定股票代码的当前价格（演示用模拟数据，只读工具）。"""
    prices = {
        "600519": "1420.50",  # 贵州茅台
        "000001": "11.23",  # 平安银行
        "300750": "198.76",  # 宁德时代
    }
    price = prices.get(symbol)
    if price is None:
        return f"未知代码 {symbol}，可用代码: {', '.join(prices)}"
    return f"{symbol} 当前价格: {price} 元"


def _load_api_key() -> str:
    # 本地 .env 优先（避免 shell 中 export 的旧 key 覆盖）
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
    else:
        for path in FALLBACK_ENV_PATHS:
            if path.exists():
                load_dotenv(path, override=True)
                break
    if os.getenv("DEEPSEEK_API_KEY"):
        return os.environ["DEEPSEEK_API_KEY"]
    raise SystemExit(
        "缺少 DEEPSEEK_API_KEY：请设置环境变量，或参考 .env.example 创建 .env",
    )


async def main() -> None:
    api_key = _load_api_key()

    model = DeepSeekChatModel(
        credential=DeepSeekCredential(api_key=api_key),
        model=DEEPSEEK_MODEL,
        parameters=DeepSeekChatModel.Parameters(
            thinking_enable=True,
            max_tokens=2000,
        ),
        stream=True,
    )

    toolkit = Toolkit(
        tools=[
            FunctionTool(
                get_stock_price,
                is_read_only=True,  # 只读工具，权限系统会据此做安全判断
            ),
        ],
    )

    agent = Agent(
        name="hello_agent",
        system_prompt=(
            "你是一个股票问答助手。回答前必须先用 get_stock_price 工具获取"
            "价格，再基于工具返回的真实数据作答，不要编造价格。"
        ),
        model=model,
        toolkit=toolkit,
    )

    print(f"模型: {DEEPSEEK_MODEL} | Agent: {agent.name}\n")
    reply = await agent.reply(
        UserMsg(name="user", content="贵州茅台（600519）现在多少钱？"),
    )

    print("=== Agent 回答 ===")
    print(reply.get_text_content())
    if reply.usage:
        print(
            f"\n[token] input={reply.usage.input_tokens} "
            f"output={reply.usage.output_tokens}",
        )


if __name__ == "__main__":
    asyncio.run(main())
