# 业务无关 Agent 引擎（engine + domains + tools）

> 定位：在 `poc/hello-agent/`（最小闭环基线）基础上的架构升级。
> hello_agent.py 保持不动，作为对照基线；本目录是"工具注册 + 业务领域层
> + 引擎层"的可运行实现。

## 1. 分层架构

```
┌───────────────────────────────────────────────────────────────┐
│ run_agent.py —— CLI 入口（业务无关：只做"选领域 → 跑引擎"）      │
├───────────────────────────────────────────────────────────────┤
│ engine/（引擎层 · 业务无关，写一次）                            │
│   domain.py        DomainPackage：领域包契约（4 个业务出口）     │
│   tool_registry.py ToolRegistry：工具注册表                     │
│                     ToolSpec → FunctionTool/ToolGroup/Toolkit  │
│   agent_engine.py  AgentEngine：模型 + 工具 + Agent 装配与执行   │
│   env_loader.py    API Key 加载（.env 优先）                    │
├───────────────────────────────────────────────────────────────┤
│ domains/（业务领域层 · 每业务一个包，插拔）                      │
│   stock_qa/  tools + prompts + schemas + domain               │
│   weather/   tools + prompts + schemas + domain               │
└───────────────────────────────────────────────────────────────┘
```

核心思想：**引擎管"怎么执行"，领域包管"执行什么"**。工具注册是业务注入的
主入口，但业务差异共有四个出口，全部由 `DomainPackage` 契约承载：

| 出口 | 承载内容 | 示例 |
| --- | --- | --- |
| `register_tools(registry)` | 业务工具 | `get_stock_price`、`get_city_weather` |
| `system_prompt` | 角色与行为约束 | "回答前必须先调工具，不得编造" |
| `output_schema` | 结构化输出契约 | `StockReport` / `WeatherReport` |
| `name / description` | 领域标识 | `stock_qa`、`weather` |

引擎不 import 任何业务模块；换业务 = 换领域包，引擎一行不改。

## 2. 一次问答的装配与执行流

```
load_domain("stock_qa") ──► AgentEngine(domain)
                               │
                 domain.register_tools(registry)   ← 业务注入①
                 registry.build_toolkit()          ← 引擎统一转换②
                 Agent(name, system_prompt, model, toolkit)
                                                   ← 引擎装配③
run_sync("贵州茅台多少钱？")
    └─► agent.reply(UserMsg, structured_schema=domain.output_schema)
          ├─► ReAct 循环：先调 get_stock_price / get_stock_financials
          └─► 最终调用 GenerateStructuredOutput 产出结构化研报
```

工具注册表支持：

- 函数注册与装饰器注册两种写法（`registry.register(fn, ...)` / `@registry.register(...)`）；
- 工具元数据声明：`name`、`description`、`read_only`（只读，权限系统前置）；
- 工具组分组建构（`basic` 组常驻，非 basic 组需描述，转换后成为
  AgentScope `ToolGroup`）。

## 3. 运行

复用 hello-agent 的 venv（已锁定 `agentscope==2.0.5`，Python 3.12）：

```bash
# 列出领域包
poc/hello-agent/.venv/bin/python run_agent.py --list-domains

# 跑投研问答（默认问题）
poc/hello-agent/.venv/bin/python run_agent.py --domain stock_qa

# 跑第二个领域，证明引擎业务无关
poc/hello-agent/.venv/bin/python run_agent.py --domain weather

# 自定义问题
poc/hello-agent/.venv/bin/python run_agent.py --domain weather --question "上海天气怎么样？"

# 启用单轮 token 预算（ReplyBudgetControlMiddleware）
poc/hello-agent/.venv/bin/python run_agent.py --domain stock_qa --budget 6000

# 多轮会话演示（短期记忆：同一引擎连续多轮 = 同一会话）
poc/hello-agent/.venv/bin/python poc/run_conversation.py --domain stock_qa

# 上下文压缩演示（极低阈值触发压缩并打印日志）
poc/hello-agent/.venv/bin/python poc/run_conversation.py --domain weather --compression-demo

# 单轮问答自定义上下文压缩阈值
poc/hello-agent/.venv/bin/python run_agent.py --domain stock_qa --context-trigger-ratio 0.5 --context-reserve-ratio 0.2

# 模型重试与回退
poc/hello-agent/.venv/bin/python run_agent.py --domain stock_qa --max-retries 2 --fallback-model deepseek-v4-pro

# HITL 写工具确认流演示（todo 领域：deny 拒绝 / confirm 自动确认）
poc/hello-agent/.venv/bin/python poc/run_hitl_demo.py
poc/hello-agent/.venv/bin/python poc/run_hitl_demo.py --confirm
```

一键离线验证（测试 + 装配冒烟，不调用模型）：

```bash
./verify.sh
```

API Key 加载优先级：`poc/.env` > `poc/hello-agent/.env` > 环境变量
（复制 `.env.example` 为 `.env` 即可）。

## 4. 评测基线（保守优先：先量化，再改进）

```bash
# 跑 stock_qa 基线（20 条，mock 模式：确定性，可精确打分）
poc/hello-agent/.venv/bin/python poc/eval/run_eval.py --domain stock_qa

# 跑 weather 基线（6 条）
poc/hello-agent/.venv/bin/python poc/eval/run_eval.py --domain weather

# 只跑前 N 条 / 自定义任务集
poc/hello-agent/.venv/bin/python poc/eval/run_eval.py --domain stock_qa --limit 3
```

当前基线（2026-08-02，mock 模式）：**stock_qa 30/30（100%）**、**weather 10/10（100%）**、**todo 5/5（100%）**。
结果明细落在 `poc/eval/results/`；退出码在通过率低于阈值（默认 0.8）时为 1。
检查项支持字段路径（`["financials", "*"]` 遍历 dict 值）、`any_of`
（容忍 LLM 对错误场景的不同措辞）与 `paths`（多个字段任一命中即通过，
如错误信息可能出现在 price 或 summary）。

回归对比：`--baseline <上次结果.json>` 输出 修复/回归/新增 差异，
存在回归时退出码为 1。

## 5. 数据源策略（当前全部 mock）

stock_qa / weather 的工具全部使用**确定性 mock 数据**，不依赖任何外部数据源
（Tushare / DuckDB / AKShare），与 StockRec 项目解耦。评测基线因此可复现、
可回归。后续需要真实数据时，只需替换 `domains/<业务>/tools.py` 内部实现，
引擎与领域包结构不变。

## 6. 测试（离线，不调用模型）

```bash
poc/hello-agent/.venv/bin/pip install pytest
cd poc && ../poc/hello-agent/.venv/bin/python -m pytest tests -q
```

覆盖：工具注册（函数式 / 装饰器 / 分组 / 只读标记）、领域包契约、引擎装配
（两个领域各自的工具与 schema，不共享状态）、预算中间件装配、权限判定
（DEFAULT 模式：只读工具 ALLOW / 写工具默认需人工确认）、评测检查项
（contains / any_of / paths）、上下文配置透传与校验、会话重置、模型
重试/回退配置、HITL 写工具确认策略（deny/confirm）、列表通配符查找。

## 7. 新增一个业务领域（三步）

1. 新建 `domains/<业务名>/` 包，实现 `tools.py`（普通函数）、`prompts.py`、
   `schemas.py`（Pydantic 模型）、`domain.py`（`DomainPackage` 子类）；
2. 在 `domain.py` 里覆写 `register_tools`，用 `registry.register(...)` 声明工具；
3. 在 `domains/__init__.py` 的 `DOMAIN_REGISTRY` 登记，并在
   `run_agent.py` 的 `DEFAULT_QUESTIONS` 补一个示例问题。

之后 `--domain <业务名>` 即可运行，引擎与工具注册表零改动。

## 8. 当前边界与下一步

- 数据层：两个领域均为确定性 mock（与外部数据源和 StockRec 解耦），
  换真实源只需改 `domains/<业务>/tools.py`；
- 模型可靠性：`--max-retries` / `--fallback-model` 可配置（`ModelConfig`
  透传），离线测试覆盖；
- 工具并行：已验证模型可在单轮并行调用两个独立工具（事件记录会标 `*`
  并统计并行数）；
- HITL 写工具确认：`--write-confirmation deny/confirm` 策略；todo 领域
  的 `add_todo` 写工具会触发 `RequireUserConfirmEvent`，deny 时工具不执行、
  confirm 时执行（两分支均已端到端验证）；
- 领域插拔：第三个领域包 todo（含写工具）已接入，引擎零改动；
- 短期记忆：已验证同一引擎多轮连续 run 保留上下文（多轮会话演示）；
  长期记忆（跨会话持久化）属规划 M2，未接入；
- 上下文管理：压缩阈值/保留比已可通过 `EngineConfig.context_config`
  或 CLI `--context-trigger-ratio / --context-reserve-ratio` 配置；
- 已知限制：上下文压缩触发后，结构化输出生成在 agentscope 2.0.5 +
  DeepSeek 组合下不稳定（`--compression-demo` 可复现：压缩日志出现后
  下一轮结构化输出失败）；默认压缩阈值（0.8）下正常对话不受影响，
  该问题待升级版本或换结构化输出路径时验证；
- 单 Agent 单轮：多 Agent 链路（规划 M2）将在领域包契约上扩展
  pipeline 拓扑出口，引擎层负责编排，业务层继续只提供内容。
