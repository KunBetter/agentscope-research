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
```

API Key 加载优先级：`poc/.env` > `poc/hello-agent/.env` > `~/git/StockRec/.env`
> 环境变量（复制 `.env.example` 为 `.env` 即可）。

## 4. 测试（离线，不调用模型）

```bash
poc/hello-agent/.venv/bin/pip install pytest
cd poc && ../poc/hello-agent/.venv/bin/python -m pytest tests -q
```

覆盖：工具注册（函数式 / 装饰器 / 分组 / 只读标记）、领域包契约、引擎装配
（两个领域各自的工具与 schema，不共享状态）。

## 5. 新增一个业务领域（三步）

1. 新建 `domains/<业务名>/` 包，实现 `tools.py`（普通函数）、`prompts.py`、
   `schemas.py`（Pydantic 模型）、`domain.py`（`DomainPackage` 子类）；
2. 在 `domain.py` 里覆写 `register_tools`，用 `registry.register(...)` 声明工具；
3. 在 `domains/__init__.py` 的 `DOMAIN_REGISTRY` 登记，并在
   `run_agent.py` 的 `DEFAULT_QUESTIONS` 补一个示例问题。

之后 `--domain <业务名>` 即可运行，引擎与工具注册表零改动。

## 6. 当前边界与下一步

- 演示数据：两个领域的工具目前都是 mock，替换真实数据源（Tushare /
  DuckDB / AKShare）只改 `domains/<业务>/tools.py`；
- 单 Agent 单轮：多 Agent 链路（规划 M2）将在领域包契约上扩展
  pipeline 拓扑出口，引擎层负责编排，业务层继续只提供内容。
