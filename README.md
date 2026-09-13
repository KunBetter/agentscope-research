# AgentScope 调研资料

本目录包含对阿里巴巴开源的 AgentScope 多智能体框架的调研成果：

| 文件 | 内容 |
| --- | --- |
| [AgentScope 技术调研报告](docs/agentscope-tech-report.md) | 项目定位、版本演进、核心架构、生态、框架对比、优劣势与风险 |
| [AgentScope 可行性应用方向脑暴](docs/agentscope-applications-brainstorm.md) | 12 个应用方向及可行性分析、优先级矩阵、落地路线建议 |
| [AgentScope 后续规划](docs/agentscope-next-steps-plan.md) | 方向决策（主攻金融投研多智能体）、POC 架构、里程碑与退出条件、风险清单、**M2 多 Agent 详细路线图（阶段 0~4 + 止损条件）**、**附录 A：Java 2.0 能力对标** |
| [Hello Agent 示例技术方案](docs/agentscope-hello-agent-example.md) | 最小闭环的技术架构、代码走读、使用说明、验证结论与踩坑记录 |
| [POC 使用 SOP](docs/agentscope-poc-sop.md) | 环境准备 / 常规操作 / 评测流程 / 开发与升级流程 / 故障排查 / 命令速查 |
| [评审与加固归档（2026-08-30）](docs/agentscope-poc-review-2026-08-30.md) | 本次会话的评估结论、改动清单、验证记录与遗留事项 |
| [业务无关 Agent 引擎架构](poc/README.md) | 引擎层 / 业务领域层 / 工具注册表的分层设计、实现与使用说明 |

## POC

| 目录 | 内容 | 状态 |
| --- | --- | --- |
| [poc/hello-agent](poc/hello-agent/) | 最小场景：单 Agent + DeepSeek v4-flash + 只读工具闭环 | ✅ 跑通（2026-08-01） |
| [poc/](poc/) | 业务无关引擎三层架构：engine 引擎层 + domains 领域包 + 工具注册表 | ✅ 跑通（2026-08-02） |

## 进展日志

| 日期 | 内容 |
| --- | --- |
| 2026-08-01 | 完成 AgentScope 技术调研与 12 方向脑暴 |
| 2026-08-01 | 确定规划：主攻金融投研多智能体，先跑最小场景 |
| 2026-08-01 | 最小场景跑通（agentscope 2.0.5 + DeepSeek v4-flash + 只读工具）；清理 zshrc 旧 key |
| 2026-08-02 | 架构升级：基于最小形态实现业务无关 Agent 引擎（engine/）+ 业务领域层（domains/，stock_qa、weather）+ 工具注册表；11 个离线测试与两个领域端到端验证通过 |
| 2026-08-02 | M1 保守项：评测基线（stock_qa 20/20、weather 6/6）、Tushare 真实数据工具（带 mock 回退）、预算中间件、权限验证、schema 升级 |
| 2026-08-02 | 解耦调整：数据层与 StockRec 解耦，全部改用确定性 mock（移除 Tushare/DuckDB/AKShare 接入与真实评测模式），保持 Agent 能力简单、可复现 |
| 2026-08-02 | 记忆与上下文：多轮会话演示验证短期记忆；`ContextConfig` 压缩阈值/保留比可配置（EngineConfig + CLI），含离线测试 |
| 2026-08-02 | 阶段 1 完成：模型重试/回退配置、工具并行调用验证、评测集扩充（stock_qa 30 + weather 10，100%）、verify.sh 一键验证、评测 --baseline diff、工具调用事件摘要 |
| 2026-08-02 | 阶段 3 完成：HITL 写工具人工确认流（deny/confirm 两分支验证）、第三个领域包 todo（含写工具）插拔接入、todo 评测 5/5；修复评测列表通配符 bug |
| 2026-08-02 | 阶段 4 收尾：验证 agentscope 2.0.5 无官方评测模块（记录结论）；自建评测新增 --all 跨领域汇总；全量 45 条基线 95.6%（两条为 LLM 措辞变体，已修复词表并单独验证） |
| 2026-08-02 | 文件型长期记忆接入（AgenticMemoryMiddleware + 受控 Read/Write，跨会话验证通过）；版本复核：2.0.5 为 PyPI 最新，压缩/评测模块待新版本复验 |
| 2026-08-30 | 工程卫生加固：依赖清单 requirements.txt / requirements-dev.txt（锁版本）、eval 产物 gitignore 不入库、缺失 API Key 改抛 MissingApiKeyError（CLI 退出码 2）、todo 写工具确认后真实写入（装配时重置）、评测任务集去重补覆盖、--all 汇总落盘、规划 M1 勾选同步、verify.sh 新 venv 回退 |
| 2026-08-30 | 代码清理 + 使用 SOP：去重 5 处 .env 配置（default_env_files）、移除未使用 import 与 hello-agent 死代码、清理 __pycache__/pytest_cache/旧评测产物；新增 [POC 使用 SOP](docs/agentscope-poc-sop.md) |
| 2026-08-30 | 结论归档：[评审与加固归档](docs/agentscope-poc-review-2026-08-30.md)（评估结论、改动清单、验证记录、遗留事项），全部改动按"代码 / 文档"两组提交入库 |
| 2026-09-13 | 版本与生态核查：上游最新 **2.0.8**（2026-09-08，本项目锁 2.0.5）；更正"官方评测缺失"结论 —— 评测在独立仓库 [OpenJudge](https://github.com/agentscope-ai/OpenJudge) 而非 `agentscope` 包内（已核对 2.0.5/2.0.8 wheel）；Python/Java 双版本能力对标（Java 最新 v2.0.3） |
| 2026-09-13 | 路线图修订：确认 Python 单轨 + 阶段目标"验证多 Agent 真实增益"，[后续规划](docs/agentscope-next-steps-plan.md) M2 细化为阶段 0~4（清账 → 引擎编排 → 四角色链路 → 风控价值验证 → 评测结论）+ 止损条件；修正 M1 陈旧勾选框；离线验证 41 测试全绿 |

**调研时间**：2026-08-01，版本与生态信息 **2026-09-13 复核**（上游 Python 2.0.8 / Java v2.0.3；评测能力在独立仓库 OpenJudge）

**一句话结论**：AgentScope 已从"多智能体开发框架"演进为覆盖开发、运行、安全、部署、评测全生命周期的生产级 Agent 工程平台（当前 Python 主线 2.0），其事件系统、权限系统、Workspace 沙箱、多租户 Agent 服务等能力在同类开源框架中差异化明显，非常适合作为企业级 Agent 应用的技术底座；但版本迭代较快，选型时需要做稳定性评估。
