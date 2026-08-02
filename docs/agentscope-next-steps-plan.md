# AgentScope 后续规划（2026-08-01）

> 本文是技术调研报告与方向脑暴之后的**决策与执行规划**。目标：把"12 个方向"收敛为一个主攻方向，给出时间盒、里程碑、验证清单与退出条件。

---

## 1. 现状评估

### 1.1 调研仓库状态

| 维度 | 状态 |
| --- | --- |
| 阶段 | 调研完成（技术报告 + 方向脑暴），**尚未做任何代码验证** |
| 交付物 | `agentscope-tech-report.md`（框架深度报告）、`agentscope-applications-brainstorm.md`（12 方向） |
| 信息时效 | 已核对：Python 主线 v2.0.5 为当前最新（结构化输出、环境注入、OpenSandbox/Daytona/K8s/Bubblewrap、RAG 多存储均在该版本）；Java 2.0.0 GA（2026-07） |
| 缺口 | 没有锁版本、没有 POC 代码、没有选定方向、没有评测基线 |

### 1.2 关键结论（与存量资产对齐）

调研报告本身是"通用视角"的框架分析；规划必须结合团队实际资产。盘点本地项目后，最重要的发现是：

**已经有一套成熟的 A 股量化系统 StockRec**：

- 数据管道：Tushare（财务/资金流）+ AKShare（实时行情）+ Baostock（K 线）+ DuckDB/SQLite 存储；
- 已有 AI 分析：DeepSeek（v4-pro/v4-flash + CoT）做成长性分析（`analyze_growth_potential.py`）、周度全流程自动化（`weekly_automation.py`）；
- 已有量化评测意识：LightGBM walk-forward IC 评测、回测脚本；
- 已有展示层：Dash 大盘。

**这意味着方向 2（金融/投研多智能体分析）不是从零开始，而是对现有单 Agent 分析的"系统工程化升级"**——数据、模型、场景全部现成，AgentScope 恰好补上现有方案的短板。

### 1.3 现有 AI 分析的真实短板（AgentScope 的补位点）

| 现状短板 | AgentScope 2.0 对应能力 |
| --- | --- |
| 单次调用、无执行轨迹可追溯 | 事件系统 + Studio 轨迹回放（合规追溯） |
| 无复核环节，幻觉无约束 | 多 Agent 编排（分析师 + 风控复核） |
| 每次分析上下文割裂 | 长期记忆中间件（mem0 / 文件型，跨会话跟踪标的） |
| 数据工具裸奔、无权限控制 | 权限系统（只读数据、命令工具默认禁用） |
| 无成本控制 | `BudgetControlMiddleware` |
| 输出格式不统一 | 结构化输出（v2.0.5 新增） |

---

## 2. 方向决策

### 2.1 决策：主攻方向 2（金融/投研多智能体分析）

理由：

1. **资产匹配度最高**：StockRec 提供数据源、模型、场景与评测基础，几乎零前置数据依赖；
2. **差异化价值最高**：把现有 DeepSeek 单次分析升级为"可追溯、可复核、可评测"的多智能体链路，是 AgentScope 相对 LangGraph/AutoGen 的最强项（事件/权限/记忆/评测开箱即用）；
3. **脑暴文档中该方向即为 ★★★★★ 且标注"若团队有金融数据源，这是差异化价值最高的方向"**——条件已满足。

### 2.2 辅助方向（作为能力组件，不单独立项）

- **方向 1（RAG）**：用于研报/公告知识库问答，作为分析 Agent 的一个工具；
- **方向 3（Deep Research）**：官方示例可改造为投研资料收集 Agent；
- **方向 4（Agent 中台）**：等 1~2 个业务应用跑通后再启动，不首发。

### 2.3 明确不做（本阶段）

- 方向 7（百万级仿真）、方向 12（RL 训练平台）：成本高、回报间接，作储备；
- 方向 11（实时语音）：作为增强能力，不首发；
- 多沙箱后端（K8s/E2B 等）：POC 阶段用本地 + 只读数据工具即可，避免过早引入基础设施复杂度。

---

## 3. POC 目标架构

投研多智能体链路（首版最小闭环）：

```
用户提问
  → 规划 Agent（拆分任务、确定所需数据）
  → 数据收集 Agent（工具：行情/财务查询，当前 mock 数据源）[只读权限]
  → 分析 Agent（财报解读、因子归因、趋势判断，输出带引用的分析）
  → 风控复核 Agent（校验数据口径、质疑幻觉、检查结论与数据一致性）
  → 结构化输出（研报 JSON Schema，含数据来源与引用）
  → （可选）人工确认 / WebUI 实时查看执行过程
```

用到的 AgentScope 能力：`ReActAgent` + 自定义 Tool 注册、`Pipeline`/Agent Team 编排、权限系统（只读模式）、结构化输出、长期记忆、预算控制、事件系统 + WebUI/Studio。

**架构落地状态（2026-08-02）**：单 Agent 骨架已按三层实现——`poc/engine/`（业务无关引擎：`DomainPackage` 契约、`ToolRegistry` 工具注册表、`AgentEngine` 装配）、`poc/domains/`（业务领域包：`stock_qa` / `weather`，各自 tools + prompts + schemas）、`poc/run_agent.py`（CLI 入口）。两个领域包均已端到端跑通（工具调用 + 结构化输出），详见 [poc/README.md](../poc/README.md)。**数据层与 StockRec 解耦**：当前全部使用确定性 mock（移除 Tushare/DuckDB/AKShare 接入），引擎与领域包结构不变，后续按需再接入真实数据源。

---

## 4. 里程碑与时间盒

### M0（本周内）：决策 + POC 环境（0.5~1 天）

- [x] 完成方向决策（本文档）
- [x] 在独立 venv 安装 `agentscope==2.0.5`（**锁定版本**，不追最新）
- [x] 跑通最小场景（`poc/hello-agent`：单 Agent + DeepSeek + 只读工具闭环）
- [x] 验证 DeepSeek 模型接入（v4-flash + CoT thinking + 流式 + token 统计）

**退出条件**：Quickstart 跑通，DeepSeek 调用成功。✅ 已达成（2026-08-01）

> 最小场景验证结论：
> - AgentScope 2.0.5 与 DeepSeek v4-flash 兼容性 OK（工具调用 + 流式 + token 用量均正常）；
> - 自定义 `FunctionTool` 注册为只读工具后，Agent 能"先调工具、再基于结果作答"，闭环成立；
> - 注意点：`~/.zshrc` 中 export 的旧 key 会顶掉 `.env` 新 key，脚本已改为本地 `.env` 优先；
> - 下一小步是把演示工具换成真实数据源（Tushare/AKShare），其余结构不动。

### M1（第 1~2 周）：单 Agent 数据问答验证

- [x] 自定义 Tool（mock 演示数据）：`get_stock_price` / `get_stock_financials`（数据层与外部数据源解耦，真实数据源按需再接入）
- [ ] 配置权限：数据工具只读，命令/写文件工具默认拒绝
- [ ] 验证结构化输出（研报 JSON Schema，v2.0.5）
- [ ] 接入 `BudgetControlMiddleware`，记录单任务 token 成本
- [ ] 建立首批评测集（20~50 条典型投研任务，如"某标的 PE/PB/ROE 趋势""财报数据与口径核对"）

> M1 更新（2026-08-02）：保守项基本落地——评测基线 stock_qa 20/20、
> weather 6/6（mock 模式 100%）；预算用 2.0.5 实际类名
> `ReplyBudgetControlMiddleware`（`--budget` 开关）；权限 DEFAULT 模式验证
> 只读工具放行、写工具默认需人工确认；schema 增加 `report_time` / `risk_note`。
> 方向调整：数据层与 StockRec 解耦，全部使用确定性 mock（移除
> Tushare/DuckDB/AKShare 接入与真实评测模式），真实数据源按需再接入。

**退出条件**：Agent 能通过自定义工具准确回答 10 个预置问题（基线 > 80%）；DeepSeek formatter 兼容性确认。

**备选决策点**：若此阶段发现 AgentScope 2.0.5 的 DeepSeek 接入或稳定性不满足要求，切换到备选方案（LangGraph 编排或手写编排），切换成本约 1~2 天。

### M2（第 3~4 周）：多 Agent 链路

- [ ] 数据收集 / 分析 / 风控复核 三角色 Agent 跑通
- [ ] 风控 Agent 能发现 ≥1 类典型错误（数据口径不一致、幻觉结论）
- [ ] 长期记忆接入（先文件型，再评估 mem0）：跨会话跟踪标的上下文
- [ ] 事件流 + WebUI/Studio 可视化执行过程

**退出条件**：20 个评测任务跑通，风控复核发现至少 1 类错误并修正，可追溯性（轨迹 + 引用）达标。

### M3（第 5~6 周）：评测与集成决策

- [ ] 用评测集对比：多 Agent 链路 vs 现有 `analyze_growth_potential.py` 单次分析
- [ ] 评估集成方式：独立服务（Agent Service）或与现有业务系统集成（待定）
- [ ] 沉淀模板与中间件（审计日志、预算、只读策略）
- [ ] 输出集成方案文档

**退出条件**：评测数据支撑"值得集成"的结论，且集成方案获得确认。

---

## 5. 风险与应对

| 风险 | 应对 |
| --- | --- |
| 2.0 迭代快、破坏性变更 | 锁定 `2.0.5` + 独立 venv；升级前查 release notes；记录升级路径 |
| DeepSeek 兼容性（formatter/function calling） | M0~M1 优先验证；失败则先接 DashScope/OpenAI 对比 |
| 金融合规（幻觉、误导） | 只读数据 + 引用溯源 + 风控复核 + 人工确认；输出声明"不构成投资建议" |
| 沙箱安全 | 数据工具只读；命令工具默认拒绝；本地沙箱即可 |
| 评测主观性 | 预置 20~50 条客观题（有确定答案的财报/行情问题）为主，主观题为辅 |
| 与 LangGraph/AutoGen 的竞争 | M1 设备选决策点，实测为准，不被纸面对比绑定 |

---

## 6. 建议的行动顺序（下一步）

1. **今天**：确认本规划（特别是方向选择），创建 POC 目录/仓库；
2. **本周**：安装 `agentscope==2.0.5` 独立环境，跑通 Quickstart + DeepSeek 接入；
3. **下周起**：按 M1 → M2 → M3 推进，每个里程碑有明确退出条件；
4. **M3 后**：根据评测结果决定集成方式，以及是否启动方向 1（RAG 知识库）。

---

## 7. 执行日志

| 日期 | 进展 | 说明 |
| --- | --- | --- |
| 2026-08-01 | 完成调研 | 技术报告 + 12 方向脑暴入库 |
| 2026-08-01 | 确定规划 | 主攻方向 2（金融投研多智能体），先跑最小场景再逐步加复杂度 |
| 2026-08-01 | M0 达成 | `poc/hello-agent` 最小闭环跑通：agentscope 2.0.5 + DeepSeek v4-flash + 只读工具；token 统计正常 |
| 2026-08-01 | 清理旧 key | 删除 `~/.zshrc` 中的旧 `DEEPSEEK_API_KEY`（备份 `.zshrc.bak`）；示例脚本改为本地 `.env` 优先 |
| 2026-08-02 | 架构升级 | 基于 hello-agent 最小形态实现业务无关引擎三层架构（engine 引擎层 / domains 领域层 / ToolRegistry 工具注册表）；stock_qa 与 weather 两个领域包端到端跑通，11 个离线测试通过 |
| 2026-08-02 | M1 保守项 | 评测基线（stock_qa 20/20、weather 6/6，mock 100%）、Tushare 真实数据工具（收盘价 + PE/PB/ROE，带回退）、预算中间件（ReplyBudgetControlMiddleware）、权限拒绝路径验证、schema 升级（report_time/risk_note） |
| 2026-08-02 | 解耦调整 | 数据层与 StockRec 解耦：移除 Tushare/DuckDB/AKShare 接入与真实评测模式，全部改用确定性 mock；卸载相关依赖；更新文档 |
| 2026-08-02 | 记忆/上下文 | 短期记忆验证：`poc/run_conversation.py` 多轮会话演示（同一引擎保留上下文，第 3 轮可引用第 1 轮信息）；上下文压缩配置：`EngineConfig.context_config` 透传 `ContextConfig`（trigger/reserve），CLI 参数化，含离线测试。**发现已知限制**：压缩触发后结构化输出在 2.0.5 + DeepSeek 下不稳定（无压缩时同轮数可跑通），已记录待验证 |
| 2026-08-02 | 保守功能批次 | 模型重试/回退（`--max-retries`/`--fallback-model`，`ModelConfig` 透传）；工具并行调用验证（事件记录 + `*` 标记）；评测集扩充至 stock_qa 30 / weather 10（100%）；`verify.sh` 一键离线验证；`--baseline` 评测 diff；工具调用事件摘要 |
| 2026-08-02 | 阶段 3 | HITL 写工具确认流：`EngineConfig.write_confirmation`（deny/confirm），todo 领域 `add_todo` 触发 `RequireUserConfirmEvent`，两分支端到端验证；第三个领域包 todo（只读 + 写工具）接入，引擎零改动；todo 评测 5/5；修复评测 `*` 通配符在列表上的查找 bug |

**当前状态**：M0 ✅；架构升级 ✅；阶段 1~3 落地（模型重试/回退、短期记忆、工具并行、评测集 30+10+5 基线 100%、verify.sh、HITL 写工具确认、第三个领域包插拔）→ 下一步：阶段 4 官方 Evaluation API 对比接入（多 Agent 按需，不主动推进）。
