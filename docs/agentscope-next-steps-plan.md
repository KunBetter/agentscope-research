# AgentScope 后续规划（2026-08-01，2026-09-13 修订）

> 本文是技术调研报告与方向脑暴之后的**决策与执行规划**。目标：把"12 个方向"收敛为一个主攻方向，给出时间盒、里程碑、验证清单与退出条件。
>
> **2026-09-13 修订**：确认 Python 单轨 + 阶段目标"验证多 Agent 真实增益"；M2 细化为阶段 0~4 与止损条件；版本更新至上游 2.0.8 核查；新增 [附录 A：AgentScope Java 2.0 能力对标](#附录-aagentscope-java-20-能力对标)。

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
- [x] 配置权限：数据工具只读，命令/写文件工具默认拒绝（2026-08-30 核对：POC 已实现并有离线测试覆盖）
- [x] 验证结构化输出（研报 JSON Schema，v2.0.5）（2026-08-30 核对：POC 已实现并有离线测试覆盖）
- [x] 接入 `BudgetControlMiddleware`，记录单任务 token 成本（实现为 `ReplyBudgetControlMiddleware`，`--budget` 开关；2026-09-13 核对）
- [x] 建立首批评测集（stock_qa 30 / weather 10 / todo 5，共 45 条 mock 任务；2026-09-13 核对）

> M1 更新（2026-08-02）：保守项基本落地——评测基线 stock_qa 20/20、
> weather 6/6（mock 模式 100%）；预算用 2.0.5 实际类名
> `ReplyBudgetControlMiddleware`（`--budget` 开关）；权限 DEFAULT 模式验证
> 只读工具放行、写工具默认需人工确认；schema 增加 `report_time` / `risk_note`。
> 方向调整：数据层与 StockRec 解耦，全部使用确定性 mock（移除
> Tushare/DuckDB/AKShare 接入与真实评测模式），真实数据源按需再接入。

**退出条件**：Agent 能通过自定义工具准确回答 10 个预置问题（基线 > 80%）；DeepSeek formatter 兼容性确认。

**备选决策点**：若此阶段发现 AgentScope 2.0.5 的 DeepSeek 接入或稳定性不满足要求，切换到备选方案（LangGraph 编排或手写编排），切换成本约 1~2 天。

### M2（第 3~6 周）：多 Agent 链路 —— 唯一目标「验证多 Agent 的真实增益」

> **阶段目标（2026-09-13 确认）**：量化回答一个问题——把单次分析升级为多角色链路，
> 通过率提升多少、成本增加多少。**只做能支撑这个结论的最小范围**。
>
> **平台决策（2026-09-13）**：**Python 单轨**，继续 `agentscope` 主线。理由：现有资产
> （engine/domains/45 条评测/41 个测试）全部在 Python 侧；Java 版的差异化能力是分布式与
> 多租户生产部署，本阶段用不上。Java 能力对标见 [附录 A](#附录-aagentscope-java-20-能力对标)。

#### 阶段 0（前置清账，1~2 天）

| # | 事项 | 产出 | 说明 |
| --- | --- | --- | --- |
| 0.1 | ~~重跑 `--all` 刷新基线~~ ✅ **2026-09-13 已完成** | `eval/results/all_summary_20260913-131208.json` + 文档数字已更新 | 结果 **45/45（100%）**，累计 179,486 tokens，实测成本 0.10 CNY；旧数字 43/45 作废 |
| 0.2 | ~~版本决策：2.0.5 → 2.0.8~~ ✅ **2026-09-13 已完成，结论：升级** | `requirements.txt` 已升至 2.0.8 + pydantic 2.13.5；弃用用法已迁移；文档已同步 | 验证链条：41→42 项离线测试全绿 → 全量评测 45/45（100%，180,092 tokens，与 2.0.5 的 179,486 基本持平）→ 压缩场景 8 轮 72 次对话、14 次压缩触发**零失败**（2.0.5 对照 3 次失败）。根因：2.0.8 新增 `compression_fallback_to_truncation` 与结构化摘要模板。唯一弃用告警 `context_buffer_ratio` 已从 `InjectionConfig` 迁至 `ContextConfig` |
| 0.3 | 修正本文陈旧勾选框 | 本文档 | M1 实际已完成，勾选框原未同步（本次已修） |

#### 阶段 1（第 1 周）：引擎编排能力（业务无关）

设计原则延续现有分层：**引擎管"怎么执行"，领域包管"执行什么"**。

- `engine/agent_engine.py` 新增角色契约：
  - `AgentRoleSpec`：`name` / `system_prompt` / `tools`（工具名子集）/ `output_schema`（可选）/ `read_only`
  - `RolePipeline`：角色顺序 + 角色间数据传递规则
- `DomainPackage` 新增**可选**出口 `roles()`：默认返回 `None`，走现有单 Agent 路径（**向后兼容，现有三个领域包零改动**）
- `AgentPipeline` 执行器：按序装配角色 → 上一角色的结构化输出作为下一角色的输入 `Msg` → 复用同一 `AgentEngine` 的模型与中间件配置
- 轨迹记录：每个角色的工具调用与产出统一落盘，供阶段 4 审计与回放
- **离线测试**（不调模型）：单角色回退、多角色装配顺序、工具子集隔离、失败短路、schema 透传

**退出条件**：`verify.sh` 全绿；用 `weather` 领域搭一个 2 角色玩具链路证明引擎可编排，且 `stock_qa` 单角色行为零回归。

#### 阶段 2（第 2 周）：stock_qa 四角色链路

| 角色 | 职责 | 工具 | 输出 |
| --- | --- | --- | --- |
| 规划 Agent | 拆解问题、决定需要哪些数据 | 无（纯推理） | 数据需求清单（结构化） |
| 数据收集 Agent | 按清单取数 | `get_stock_price` / `get_stock_financials`（只读） | 原始数据 + 来源标注 |
| 分析 Agent | 财报解读、趋势判断，结论必须带引用 | 无（消费上游产出） | 分析稿（结构化） |
| 风控复核 Agent | 校验数据口径一致性、质疑无依据结论、核对引用 | 无（只读上游产出） | 复核意见 + 修正建议 |

- 权限取最小集：**仅数据收集角色持有工具**，其余角色无工具（顺带验证权限系统在链路中的表现）
- 审计中间件：每角色的 `MODEL_CALL` / `TOOL_CALL` / 最终输出落盘为可回放轨迹
- 预算：`--budget` 覆盖整条链路，按角色记录 token 成本

**退出条件**：四角色链路端到端跑通，产出符合 `StockReport` schema，轨迹可回放。

#### 阶段 3（第 3 周）：风控复核的价值验证（**本阶段核心**）

这是整个 M2 唯一能证明"多 Agent 值得做"的实验。

- **注入式错误测试集**：构造 15~20 条"带坑"任务，覆盖三类典型错误：
  1. 数据口径不一致（把 PE 当 PB、报告期错配等）
  2. 幻觉结论（数据中没有支撑的断言）
  3. 引用错配（结论与所引数据对不上）
- **对照实验**：同一批任务分别跑「单 Agent」与「多角色链路」，记录三个数：
  - 通过率（沿用自建评测口径）
  - 风控环节检出率（错误被指出的比例）
  - token 成本 / 延迟（链路相对单 Agent 的倍数）
- **退出条件**：风控 Agent 对 ≥1 类错误检出率 ≥ 80%。达不到则先迭代 prompt 与复核规则；两轮无改善则**如实记录失败**并触发止损条件。

#### 阶段 4（第 4 周）：评测口径收敛与结论

- 多 Agent 专用任务集（20~30 条）并入 `eval/tasks/`，检查项支持"风控环节是否触发"
- 评测新增 `--compare` 模式：单 Agent vs 多 Agent 对比表（通过率 / 成本 / 延迟）
- 可选：用官方评测框架 [OpenJudge](https://github.com/agentscope-ai/OpenJudge)（PyPI `py-openjudge`）对同一批任务做交叉验证，检验自建口径是否偏乐观
- **退出条件（= M2 完成的定义）**：产出量化结论——多 Agent 相对单 Agent 的**通过率增益 vs 成本倍数**，结论无论正负都入库。

#### 止损条件

任一条件触发即停止加码，转为"单 Agent 结论"并直接进入 M3：

1. 阶段 3 风控检出率 < 60% 且两轮 prompt 迭代无改善；
2. 多 Agent 通过率提升 < 5 个百分点，而 token 成本 > 3 倍；
3. 2.0.5 / 2.0.8 在链路场景下出现无法绕过的稳定性问题。

#### 本阶段明确不做

- ❌ WebUI / Studio 可视化（事件轨迹先落盘，能回放即可）
- ❌ 真实数据源（Tushare / AKShare）——mock 足以支撑对照实验
- ❌ mem0 / 向量库等新记忆后端（文件型长期记忆已够）
- ❌ 新沙箱后端、K8s / E2B 等基础设施
- ❌ Java 平台迁移（结论见附录 A）
- ❌ 引入官方评测依赖（OpenJudge 仅作可选交叉验证）

### M3（第 7~8 周）：评测与集成决策（M2 通过后再启动）

- [ ] 用评测集对比：多 Agent 链路 vs 现有 `analyze_growth_potential.py` 单次分析
- [ ] 评估集成方式：独立服务（Agent Service）或与现有业务系统集成（待定）
- [ ] 沉淀可复用模板与中间件（审计日志、预算、只读策略）
- [ ] 输出集成方案文档

**退出条件**：评测数据支撑"值得集成"的结论，且集成方案获得确认。

---

## 5. 风险与应对

| 风险 | 应对 |
| --- | --- |
| 2.0 迭代快、破坏性变更 | 锁定 `2.0.8` + 独立 venv；升级前查 release notes；升级后跑全量评测回归（本次已验证无回归） |
| DeepSeek 兼容性（formatter/function calling） | M0~M1 优先验证；失败则先接 DashScope/OpenAI 对比 |
| 金融合规（幻觉、误导） | 只读数据 + 引用溯源 + 风控复核 + 人工确认；输出声明"不构成投资建议" |
| 沙箱安全 | 数据工具只读；命令工具默认拒绝；本地沙箱即可 |
| 评测主观性 | 预置 20~50 条客观题（有确定答案的财报/行情问题）为主，主观题为辅 |
| 与 LangGraph/AutoGen 的竞争 | M1 设备选决策点，实测为准，不被纸面对比绑定 |

---

## 6. 下一步行动（2026-09-13 更新）

M0 / M1 已完成，当前起点是 M2 阶段 0：

1. **先清账（阶段 0.1）**：重跑 `poc/eval/run_eval.py --all` 刷新 45 条基线，把可信通过率写回本文与 `poc/README.md`（此前任务集调整后未重跑，现无可信数字）；
2. **再定版本（阶段 0.2）**：独立 venv 装 `agentscope==2.0.8` 跑 `verify.sh`，复验压缩稳定性；通过则升级并同步 `requirements.txt`，不通过则维持 2.0.5 并记录原因；
3. **然后进阶段 1**：在 `engine/` 加 `AgentRoleSpec` / `AgentPipeline` 与 `DomainPackage.roles()` 可选出口，用 `weather` 做 2 角色玩具验证；
4. **按阶段 1 → 2 → 3 → 4 推进**，每阶段有明确退出条件与止损条件；
5. **M2 结束后**：按量化结论决定是否进入 M3（集成决策），以及是否启动方向 1（RAG 知识库）。

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
| 2026-08-02 | 阶段 4（官方评测验证） | 验证结论：`agentscope==2.0.5` 安装包无评测模块（子模块/导出均无 eval），官方 Evaluation API 对比接入不可行；保守替代：自建评测新增 `--all` 跨领域汇总。全量 45 条一次汇总 43/45（95.6%），两条失败为检查词表未覆盖 LLM 措辞变体，已修复并单独验证 |
| 2026-08-02 | 长期记忆 + 版本复核 | 文件型长期记忆接入：`--memory-dir` 启用 `AgenticMemoryMiddleware` + 受控 Read/Write 工具（Write 仅允许写记忆目录），跨会话取回端到端验证通过。版本复核：`pip index versions agentscope` 显示最新仍为 2.0.5，暂无升级目标；压缩后结构化输出不稳定为间歇性（复验触发两次压缩未见失败），官方评测模块缺失结论维持 |
| 2026-08-30 | 工程卫生加固 | 依赖清单 `requirements.txt`/`requirements-dev.txt`（锁版本）；`eval/results/` 产物 gitignore 不入库；缺失 API Key 改抛 `MissingApiKeyError`（CLI 退出码 2）；todo 写工具确认后真实写入（装配时重置状态）；评测任务集 sq-013~015 去重替换补覆盖（新增 PB/PE 数据点）；`--all` 汇总落盘；规划 M1 勾选框同步；`verify.sh` 支持新 venv 回退；新增 env_loader 与 todo 写入离线测试 |
| 2026-09-13 | M2 路线图 + 版本/生态核查 | 确认平台决策（Python 单轨）与阶段目标（验证多 Agent 真实增益），M2 细化为阶段 0~4 + 止损条件；修正 M1 陈旧勾选框；版本核查：PyPI 最新 **2.0.8**（2026-09-08），本项目锁 2.0.5；**更正"官方评测缺失"结论**——评测在独立仓库 OpenJudge，不在 `agentscope` 包内（已核对 2.0.5/2.0.8 wheel）；新增 Java 2.0 能力对标（附录 A） |
| 2026-09-13 | 阶段 0.1 完成：刷新评测基线 | 重跑 `--all`：**45/45（100%）**，累计 179,486 tokens，实测成本 0.10 CNY（余额 29.02 → 28.92）。API Key 执行前验证通过（`/models` + `/user/balance`）；确认默认模型名 `deepseek-v4-flash` 可用（服务端 resolve 为 `deepseek-flash`）、回退 `deepseek-v4-pro` 可用。文档数字已同步（本文 + `poc/README.md`） |
| 2026-09-13 | 阶段 0.2 完成：升级 agentscope 2.0.8 | 独立 venv 装 2.0.8 验证后判定升级：`requirements.txt` → `agentscope==2.0.8` + `pydantic==2.13.5`；两处 `context_buffer_ratio` 用法从 `InjectionConfig` 迁至 `ContextConfig`（新增回归测试，共 42 项）；`hello-agent` 基线环境与文档同步升级。验证：42 项离线测试全绿；全量评测 45/45（180,092 tokens）；**压缩场景 8 轮 72 次对话、14 次压缩触发零失败**（2.0.5 对照 3 次 `Failed to generate structured output`）——原"压缩后结构化输出不稳定"的已知限制**已消除** |

**当前状态**（2026-09-13）：M0 ✅；架构升级 ✅；M1 全部 ✅；**阶段 0.1 ✅（基线 45/45）**；**阶段 0.2 ✅（已升级 2.0.8，压缩稳定性问题消除）**；
文件型长期记忆 ✅ 跨会话验证通过；
**M2 下一个动作 = 阶段 1（引擎编排能力：`AgentRoleSpec` / `AgentPipeline` / `DomainPackage.roles()`）**。

---

## 附录 A：AgentScope Java 2.0 能力对标

> 核查时间：2026-09-13 ｜ 来源：`github.com/agentscope-ai/agentscope-java` 源码树、release notes、官方文档（`java.agentscope.io/v2/en/docs`）

### A.1 基本盘

| 维度 | 内容 |
| --- | --- |
| 定位 | Build distributed, production-grade, long-running agents |
| 最新版本 | **v2.0.3**（2026-09-07）；v2.0.0 GA 于 2026-07-10 |
| 要求 | JDK 17+；Apache-2.0 |
| 体量 | 5,580 stars / 1,347 forks / 877 open issues；最后 push 2026-09-12 |
| 文档 | <https://java.agentscope.io/>（v2 中英文档） |

### A.2 模块结构（Maven 多模块）

| 模块 | 职责 |
| --- | --- |
| `agentscope-core` | 基础框架：ReActAgent、message、event、model、tool、permission、middleware、memory、state、skill、rag、formatter、credential、hook、interruption、shutdown、tracing |
| `agentscope-harness` | 工程化外壳 `HarnessAgent`：workspace、plan、memory、sandbox、subagent、team、skill、tool、transcript、artifact、bus、coordination、gateway |
| `agentscope-extensions` | 21 个扩展模块（模型 / 沙箱 / 存储 / RAG / 协议 / 通道） |
| `agentscope-service` | Agent 控制平面 + Dashboard（Go `aistiod` 控制面 + Java gateway / dataplane / scheduler） |
| `agentscope-examples` / `-distribution` / `-dependencies-bom` | 示例 / 发行包 / 依赖版本统一管理 |

### A.3 三大设计支柱

**① Harness 工程（为长任务而生）**：`HarnessAgent` 是 `ReActAgent` 的薄包装，能力通过 Middleware + Toolkit 挂载，推理内核零改动。

| 能力 | 内容 |
| --- | --- |
| Workspace 驱动人格 | persona / knowledge / subagent spec / skills / MCP allowlist 文件化（`AGENTS.md`、`workspace/tools.json`）；系统提示每轮重建，改文件即时生效 |
| 分层记忆 | 上下文会话 → agent 自维护 `MEMORY.md` → 磁盘 append-only 事实日志（`memory/YYYY-MM-DD.md`），限流后台合并 |
| 自动上下文管理 | 结构化压缩保留 goals/state/findings/next steps；>80K 字符工具结果卸载到磁盘；上下文溢出重试兜底 |
| 子 Agent | Markdown 声明 spec，`agent_spawn` / `agent_send` 运行时编排，同步或后台委派，结果经 `system-reminder` 推回 |
| Plan Mode | 只读规划态，计划持久化在 `workspace/plans/` 并驱动执行，HITL 退出 |
| 技能自进化 | 成功模式存为 Markdown 技能；仓库支持 Git / Nacos / MySQL / classpath / workspace |
| 沙箱隔离 | 本地子进程 / Docker / Kubernetes / E2B / Daytona / AgentRun，带快照恢复；文件系统可插拔 |
| Agent 团队 | `TeamClient`（含 `LocalTeamClient`）+ `TeamCreateSpec` / `TeamMemberSpec` / `TeamTask` / `TeamMessage` / `TeamWakeups` |
| Channel | 会话管理、每会话并发、多 Agent 路由、流式事件；IM 通道（钉钉 / 飞书 / 企微等） |

**② 企业级分布式**：`IsolationScope` 四维隔离（session / user / agent / org）；`DistributedStore` 一行接入实现无状态水平扩展与跨副本会话恢复；`AgentStateStore` 支持内存 / JSON 文件 / MySQL / Redis / PostgreSQL；v2.0.3 新增 `VersionedState` + `ConflictPolicy` 乐观并发；Docker / docker-compose / Helm 部署。

**③ 精简基础框架**：31 个类型化事件、统一 `call()` / `streamEvents()` 执行核心；`ContentBlock` 统一多模态消息；AOP 式**五阶段**中间件（`onAgent` / `onReasoning` / `onActing` / `onModelCall` / `onSystemPrompt`）；`ModelRegistry` 字符串解析 + SPI 发现；三态权限；MCP 集成；原生结构化输出；`interruption` 优雅中断 + pending tool 恢复。

**④ 协议与生态**：AG-UI（SSE 事件流，含 CopilotKit 全栈示例）、A2A、OpenAI SDK 兼容；扩展覆盖 5 个模型 provider、4 个沙箱后端、8 类存储后端、RAG / mem / nacos / scheduler / studio / training / Spring Boot starters / Higress。

### A.4 与本项目相关的两个坑

1. **DeepSeek 走 OpenAI 兼容路径**（非独立 provider）：`deepseek:deepseek-v4-flash` + `DEEPSEEK_API_KEY`，core 内有 `DeepSeekCredential`。官方文档明确：**工具与结构化输出同时存在时，DeepSeek / Kimi 会优先满足 `response_format` 而跳过 tool calling**，需 `nativeStructuredOutputWithTools(false)`。这与本项目 Python 侧遇到的"压缩后结构化输出不稳定"是同类问题。
2. **Java 版同样无内置评测模块**：与 Python 侧一致，评测统一在独立仓库 [OpenJudge](https://github.com/agentscope-ai/OpenJudge)。

### A.5 Java 2.0 vs Python 2.0

| 维度 | Java 2.0 | Python 2.0 |
| --- | --- | --- |
| 定位 | 分布式、企业级、长运行 | 功能最全、迭代最快 |
| 最新版 | v2.0.3（09-07） | 2.0.8（09-08） |
| 独有强项 | HarnessAgent 双层架构、Plan Mode、subagent Markdown 声明、Team 协作、跨副本会话恢复、Go 控制平面、Spring Boot / Helm / K8s | `pipeline`(GoalPipeline)、`console`、`realtime`(语音)、`tts`、`embedding`、更多沙箱后端（bubblewrap / OpenSandbox / Apple Container）、skill hub、`app`(Web UI 多租户服务) |
| 共有 | ReActAgent 内核、事件系统、三态权限、中间件、MCP、原生结构化输出、分层记忆、沙箱抽象 | 同左 |

### A.6 结论

**本阶段维持 Python 单轨**。Java 版的差异化价值集中在"分布式 + 多租户 + 控制平面"，属于生产部署阶段的问题，而本项目当前阶段要回答的是"多 Agent 是否真有增益"——这是模型编排与提示工程问题，与平台语言无关，Python 侧资产（engine / domains / 45 条评测 / 41 个测试）可直接复用。

**重新评估的触发条件**（满足任一则重开 Java 议题）：

- M2/M3 结论为"值得集成"，且集成形态要求多租户、跨副本会话恢复或 K8s 部署；
- 需要 IM 通道（钉钉 / 飞书 / 企微）或 Spring Boot 生态集成；
- Python 侧在并发与长任务稳定性上出现无法绕过的问题。
