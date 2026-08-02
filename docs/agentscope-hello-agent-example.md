# Hello Agent 示例：技术方案与使用说明

> 对应代码：`poc/hello-agent/` ｜ 状态：✅ 已跑通（2026-08-01）
> 定位：AgentScope 2.0 的**最小可行闭环**，是后续金融投研多智能体的验证底座。
>
> 2026-08-02 更新：基于本示例的架构升级已落地到 [poc/](../poc/README.md)
> （engine 引擎层 + domains 领域层 + 工具注册表），本示例保留为最小基线。

---

## 1. 目标与范围

本示例只验证一件事：**AgentScope 能不能"装得上、接得通、转得动"**。具体拆为 4 个检查点：

| # | 检查点 | 判定标准 |
| --- | --- | --- |
| 1 | 安装 | `agentscope==2.0.5` 在独立 venv 中可用 |
| 2 | 模型接入 | DeepSeek v4-flash 连通，支持 CoT thinking 与流式 |
| 3 | 工具闭环 | Agent 先调用只读工具，再基于工具结果作答 |
| 4 | 成本可见 | 每次回复返回 token 用量 |

**明确不做**（避免过早复杂化）：多 Agent、沙箱、Agent Service、RAG、评测、真实数据源——这些留到后续阶段。

---

## 2. 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                     hello_agent.py                      │
│                                                         │
│  DeepSeekChatModel ──► Agent(name, system_prompt, ...)  │
│       │                    │  ▲                         │
│       │  model 调用         │  │ 回复 Msg                │
│       ▼                    ▼  │                         │
│  DeepSeek API ◄── ReAct 循环 ─┘                          │
│        (thinking + 流式)      │                          │
│                              ▼                          │
│                     Toolkit(basic)                      │
│                              │                          │
│                              ▼                          │
│              FunctionTool(get_stock_price)              │
│                     is_read_only=True                   │
└─────────────────────────────────────────────────────────┘
```

### 2.1 各组件职责

| 组件 | 类 / 位置 | 职责 |
| --- | --- | --- |
| 模型 | `DeepSeekChatModel`（`agentscope.model`） | 统一封装 DeepSeek API：凭据、流式、thinking、重试 |
| 凭据 | `DeepSeekCredential`（`agentscope.credential`） | 管理 api_key / base_url，`SecretStr` 防泄漏 |
| Agent | `Agent`（`agentscope.agent`） | 2.0 统一 Agent 类：内置 ReAct 推理-行动循环、上下文压缩、权限引擎 |
| 工具 | `FunctionTool`（`agentscope.tool`） | 把任意 Python 函数包装为标准工具，自动提取签名/文档生成 JSON Schema |
| 工具集 | `Toolkit` | 工具的注册入口，tools 属于 "basic" 工具组 |
| 消息 | `UserMsg`（`agentscope.message`） | 统一消息对象（文本块自动封装），贯穿上下文与事件流 |

### 2.2 关键设计决策

1. **锁版本**：`agentscope==2.0.5`，独立 venv（Python 3.12），避免系统 Python 3.14 的兼容风险。
2. **模型固定**：`deepseek-v4-flash` + 官方 base_url，减少变量。
3. **工具只读**：`FunctionTool(..., is_read_only=True)` 显式声明工具无副作用，这是后续权限系统（允许/拒绝/人工确认）的最小前置实践。
4. **API Key 优先级**：本地 `.env` > 环境变量回退链。之所以本地优先，是因为 shell 里 export 的旧 key 会静默覆盖 `.env`（见 §6 踩坑记录）。

---

## 3. 代码走读

### 3.1 模型初始化

```python
model = DeepSeekChatModel(
    credential=DeepSeekCredential(api_key=api_key),
    model=DEEPSEEK_MODEL,  # "deepseek-v4-flash"
    parameters=DeepSeekChatModel.Parameters(
        thinking_enable=True,   # 开启 CoT 思维链
        max_tokens=2000,
    ),
    stream=True,
)
```

`thinking_enable` 对应 DeepSeek 的 `reasoning_content` 字段；`stream=True` 走流式输出，长回复不阻塞。

### 3.2 工具注册

```python
def get_stock_price(symbol: str) -> str:
    """返回给定股票代码的当前价格（演示用模拟数据，只读工具）。"""
    ...

toolkit = Toolkit(tools=[FunctionTool(get_stock_price, is_read_only=True)])
```

`FunctionTool` 自动从函数签名与 docstring 提取工具名、参数 Schema 与描述，无需手写 JSON Schema。

### 3.3 Agent 创建与调用

```python
agent = Agent(
    name="hello_agent",
    system_prompt="你是一个股票问答助手。回答前必须先用 get_stock_price 工具获取价格……",
    model=model,
    toolkit=toolkit,
)

reply = await agent.reply(UserMsg(name="user", content="贵州茅台（600519）现在多少钱？"))
```

`Agent` 是异步 API（`await agent.reply(...)`），返回 `Msg`；文本通过 `reply.get_text_content()` 提取，用量通过 `reply.usage`（input/output tokens）统计。

---

## 4. 使用方案

### 4.1 环境要求

- Python 3.12（AgentScope 2.0 要求 3.11+）
- DeepSeek API Key（已配置在 `poc/hello-agent/.env`，该文件已 gitignore）

### 4.2 安装与运行

```bash
cd poc/hello-agent
/usr/local/bin/python3.12 -m venv .venv
.venv/bin/pip install agentscope==2.0.5
.venv/bin/python hello_agent.py
```

### 4.3 API Key 配置（按优先级）

1. `poc/hello-agent/.env`（推荐，本示例中优先）；
2. 环境变量 `DEEPSEEK_API_KEY`；

### 4.4 预期输出

```
模型: deepseek-v4-flash | Agent: hello_agent

=== Agent 回答 ===
根据工具返回的真实数据，贵州茅台（600519）当前价格为 **1420.50 元**。

[token] input=1064 output=122
```

价格 `1420.50` 只存在于工具数据中（不在 prompt 里），且输入 token 显著高于普通提问，可确认工具调用发生过。

### 4.5 故障排查

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 401 Authentication Fails | API Key 无效/被旧 key 覆盖 | 检查 `.env` 与 shell 环境变量；确认 key 结尾与预期一致 |
| 模型调用"exhausted all attempts" | API 异常或凭据失败 | 看异常根因（认证/限流/网络）；先手动 curl 验证 key |
| 找不到 agentscope 模块 | venv 未激活或未安装 | 用 `.venv/bin/python` 而非系统 python |

---

## 5. 验证结论

| 检查点 | 结果 |
| --- | --- |
| 安装 `agentscope==2.0.5` | ✅ 成功（Python 3.12 venv） |
| DeepSeek v4-flash 接入 | ✅ 成功（thinking + 流式） |
| 工具调用闭环 | ✅ 成功（Agent 基于工具结果作答） |
| token 统计 | ✅ 正常（input=1064 / output=122） |

结论：**AgentScope 2.0.5 与 DeepSeek 组合的最小链路成立**，可以进入下一阶段（接入真实数据源）。

---

## 6. 踩坑记录

1. **旧 key 静默覆盖**：`~/.zshrc` 中 export 的旧 `DEEPSEEK_API_KEY` 优先级高于 `.env`，导致本地新 key 不生效、连续 401。已通过"本地 `.env` 优先 + `override=True`"解决，旧 key 已从 zshrc 删除（备份 `~/.zshrc.bak`）。
2. **系统 Python 3.14**：默认 `python3` 为 3.14，为与 AgentScope 兼容性对齐，统一用 Python 3.12 建 venv。
3. **pip 网络受限**：沙箱内无法解析 PyPI，安装需在沙箱外执行（已批准）。

---

## 7. 扩展路径（下一步）

> 2026-08-02：架构已升级为"引擎层 + 业务领域层 + 工具注册表"三层
> （见 [poc/README.md](../poc/README.md)），本示例保留为最小基线。
> 后续接入真实数据在 `poc/domains/stock_qa/tools.py` 内替换实现即可。

1. **数据层当前为确定性 mock**（与外部数据源解耦）：后续接真实数据时替换 `poc/domains/stock_qa/tools.py` 内部实现即可；
2. **补充财务工具**：在 stock_qa 领域包继续注册 PE/PB/ROE 等查询工具，对应规划 M1；
3. **权限强化**：数据工具保持只读，命令工具默认拒绝；
4. **多 Agent**：在 M2 阶段增加"分析 Agent + 风控复核 Agent"，复用 engine/domains 的分层模式。

关联规划见 [AgentScope 后续规划](agentscope-next-steps-plan.md)。
