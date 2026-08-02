# Hello Agent（最小场景）

验证 AgentScope 2.0.5 的最小闭环：**单个 ReActAgent + DeepSeek + 一个只读工具**。

```bash
# 首次
/usr/local/bin/python3.12 -m venv .venv
.venv/bin/pip install agentscope==2.0.5

# 运行（API Key 自动从环境变量 / 本目录 .env 读取）
.venv/bin/python hello_agent.py
```

预期输出：Agent 先调用 `get_stock_price` 工具，再基于返回的价格作答。

> 说明：价格是脚本内的模拟数据，只用来验证"模型 → 工具调用 → 基于结果作答"闭环；
> 换成真实数据只需替换工具函数内部实现。
