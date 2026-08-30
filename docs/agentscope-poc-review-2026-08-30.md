# AgentScope POC 评审与加固归档（2026-08-30）

> 本文归档 2026-08-30 会话的全部结论：项目深度评估 → 工程卫生加固 → 代码清理 → 使用 SOP。
> 代码改动与文档均已随本归档入库，本文是本次会话结论的唯一归档入口。

---

## 1. 会话概览

| 环节 | 产出 |
| --- | --- |
| 深度评估 | 项目定位、亮点、A/B/C/D 级问题清单（见 §2） |
| 工程卫生加固（P0） | 依赖清单、产物入库清理、基线口径统一（见 §3.1） |
| 代码严谨性（P1） | 异常体系、todo 真实写入、任务集补覆盖、`--all` 落盘（见 §3.2） |
| 代码清理 | 死代码 / 未使用 import / 重复配置 / 磁盘产物（见 §3.3） |
| 使用 SOP | `docs/agentscope-poc-sop.md`（见 §3.4） |

---

## 2. 项目评估结论

### 2.1 定位与状态（评估时点）

- 仓库性质：AgentScope（阿里通义实验室多智能体框架）调研 + POC 验证仓库；
- 规模：约 2200 行 Python（不含 venv）、4 份调研文档 + 使用 SOP；git 11 次提交（本会话后 13 次）；
- 版本：`agentscope==2.0.5`（锁定，PyPI 最新），Python 3.12 独立 venv；
- 执行进度：M0 ✅ → 三层引擎架构 ✅ → M1 全部 ✅；**M2 多 Agent 链路未启动**。

### 2.2 亮点（保留项）

1. **决策链路完整可审计**：12 方向脑暴 → 依据存量资产（StockRec）收敛为主攻方向 2，每个里程碑带退出条件与备选决策点；
2. **引擎分层正确**：`DomainPackage` 四出口契约（name/description/register_tools/system_prompt/output_schema），第三个领域包 todo 零改动接入，插拔性实证；
3. **评测先行**：确定性 mock（可精确打分、可回归）、`--baseline` diff、`--all` 汇总、阈值退出码语义；
4. **测试纪律**：41 项全离线（不调模型、不发请求），`verify.sh` 一键回归；
5. **诚实记录负面结论**：压缩+结构化输出间歇性不稳定、官方评测模块在 2.0.5 缺失（实测验证，非听信文档）。

### 2.3 评估问题清单（归档状态）

| 级别 | 问题 | 归档状态 |
| --- | --- | --- |
| A | 无依赖清单，新克隆不可复现 | ✅ 已修复：`requirements.txt` / `requirements-dev.txt` |
| A | 评测产物入库 + 混入 w-006 的污染文件 | ✅ 已修复：gitignore + 移除 17 个结果 JSON |
| A | 文档基线口径漂移（README 100% vs 规划 95.6%） | ✅ 已统一口径并标注时间 |
| B | mock 数据重复（hello-agent 与 stock_qa） | ⏳ 保留：hello-agent 为冻结对照基线，刻意不动 |
| B | todo 写工具"假写"（add_todo 不改状态） | ✅ 已修复：确认后真实写入 + 装配时重置 |
| B | `SystemExit` 作为错误通道（引擎层硬编码进程行为） | ✅ 已修复：`MissingApiKeyError`，CLI 退出码 2 |
| B | 测试依赖框架私有 API（`_reply_middlewares` 等） | ✅ 已加升级提示注释 |
| B | 评测任务集重复题（sq-013~015 与 sq-001~003 重复） | ✅ 已修复：替换为 3 个新财务指标点 |
| C | M2 多 Agent 链路零代码（核心差异化价值未验证） | ⏳ 遗留：见 §5 |
| C | 规划勾选框与实现脱节 | ✅ 已同步核对 |
| C | 真实数据源接入条件悬置 | ⏳ 遗留：未定义触发条件 |
| D | 压缩+结构化输出间歇性不稳定（2.0.5 + DeepSeek） | ⏳ 遗留：待新版本复验 |

### 2.4 总体结论

- **作为 AgentScope 技术验证 POC：优秀**。工程卫生经本会话加固后达到公司级基础要求（可复现、可回归、错误可诊断、文档同步）；
- **作为金融投研多智能体项目：地基完成**。权限/预算/HITL/记忆/评测等横切能力验证充分，但三角色链路与风控复核这一核心差异化价值尚未启动。

---

## 3. 本次改动清单（可追溯）

### 3.1 工程卫生（P0）

- 新增 `poc/requirements.txt`（`agentscope==2.0.5` / `pydantic==2.13.4` / `python-dotenv==1.2.2`——后两者是 poc 直接 import 但 agentscope 未声明的传递依赖）与 `requirements-dev.txt`（`pytest==9.1.1`）；
- `poc/.gitignore` 增加 `eval/results/`；从 git 移除 17 个历史结果 JSON；
- `poc/README.md` §4 基线口径统一：任务集 30/10/5 条，旧数字（2026-08-02）标注时间，任务集调整后需重跑 `--all` 刷新。

### 3.2 代码严谨性（P1）

- `engine/env_loader.py`：`SystemExit` → `MissingApiKeyError(RuntimeError)`；新增 `default_env_files()`（收敛 5 处重复的 `.env` 路径定义）；
- 5 个 CLI/评测脚本（`run_agent` / `run_conversation` / `run_hitl_demo` / `run_memory_demo` / `eval/run_eval.py`）统一捕获缺 Key → 退出码 2 + 清晰报错；
- `domains/todo`：`add_todo` 确认后真实写入列表；新增 `reset_todos()`，引擎装配时重置（评测逐任务隔离、演示互不影响）；
- `eval/tasks/stock_qa.jsonl`：sq-013~015 替换为 平安银行 2024 PB / 贵州茅台 2023 PB / 宁德时代 2023 PE（新增覆盖点，已校验与 mock 数据一致）；
- `eval/run_eval.py`：`--all` 汇总落盘 `all_summary_<时间戳>.json`（分领域+合计的通过数/准确率/token）；`--all` 分支补 `out_dir.mkdir`；
- `verify.sh`：venv 路径优先 `poc/.venv`、回退 `hello-agent/.venv`；
- `docs/agentscope-next-steps-plan.md`：M1 两个遗留勾选框核对为已完成，执行日志与当前状态同步。

### 3.3 代码清理

- `hello-agent/hello_agent.py`：删除 `FALLBACK_ENV_PATHS` 死代码（else 分支检查同一路径，行为不变）；
- `run_conversation.py`：移除未使用 import `list_domains`；
- 磁盘清理：9 个 `__pycache__`、`.pytest_cache`、17 个旧评测结果；
- AST 扫描确认：无未使用 import、无旧常量引用残留（`ENV_FILES` / `FALLBACK_ENV_PATHS` 等）。

### 3.4 使用 SOP

- 新增 `docs/agentscope-poc-sop.md`：一页速览 / 环境准备 / 常规操作 / 评测流程 / 开发流程（含提交前 Checklist）/ 版本升级 / 故障排查 FAQ / 命令速查。

### 3.5 测试

- 新增 `tests/test_env_loader.py`（3 项：缺失抛异常 / `.env` 优先级 / 环境变量兜底）+ `tests/test_domains.py`（2 项：todo 真实写入 / 装配重置）；
- 依赖私有 API 的既有测试（`test_budget_permission.py` / `test_memory.py`）补充升级提示注释。

---

## 4. 验证记录（归档时点）

| 验证项 | 结果 |
| --- | --- |
| 离线测试 | **41/41 通过**（原 36 + 新 5） |
| `verify.sh`（测试 + 领域列表 + 装配冒烟） | 全绿 ✅ |
| 全量 `py_compile` | 通过 ✅ |
| CLI 缺 Key → 退出码 2 + 清晰报错 | 冒烟通过 ✅ |
| 评测任务集 ids 唯一 + 检查项与 mock 数据一致 | 通过 ✅ |
| 未使用 import / 残留引用扫描 | 零告警 ✅ |

---

## 5. 遗留事项（下次会话从这里继续）

| 事项 | 类型 | 建议动作 |
| --- | --- | --- |
| 基线数字刷新 | 需 API Key + 网络 | 跑 `eval/run_eval.py --all`，把新数字写回 `poc/README.md` §4 |
| 多 Agent 链路（M2） | 核心方向 | 在 `DomainPackage` 契约上设计 pipeline 拓扑出口，引擎负责编排 |
| 真实数据源接入条件 | 决策 | 定义触发条件（如 M2 风控复核需要真实口径数据时） |
| 压缩+结构化输出不稳定 | 框架风险 | 新版本复验；M2 长轨迹前定向复现并记录 workaround |
| 官方评测模块缺失 | 框架风险 | 新版本复验（当前结论：2.0.5 安装包无评测模块） |
| hello-agent 数据重复 | 已知取舍 | 冻结对照基线，保持现状 |
| 提交策略 | git 操作 | 本次按"代码 / 文档"两组提交入库 |

---

## 6. 关联文档索引

| 文档 | 内容 |
| --- | --- |
| [技术调研报告](agentscope-tech-report.md) | 项目定位、版本演进、核心架构、生态、框架对比、优劣势与风险 |
| [应用方向脑暴](agentscope-applications-brainstorm.md) | 12 个应用方向及可行性分析、优先级矩阵 |
| [后续规划](agentscope-next-steps-plan.md) | 方向决策（金融投研）、POC 架构、里程碑与退出条件、风险清单 |
| [使用 SOP](agentscope-poc-sop.md) | 环境准备 / 常规操作 / 评测 / 开发 / 升级 / FAQ / 命令速查 |
| [引擎架构说明](../poc/README.md) | 引擎层 / 领域层 / 工具注册表的分层设计与实现 |
