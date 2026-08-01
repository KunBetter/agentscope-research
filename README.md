# AgentScope 调研资料

本目录包含对阿里巴巴开源的 AgentScope 多智能体框架的调研成果：

| 文件 | 内容 |
| --- | --- |
| [AgentScope 技术调研报告](docs/agentscope-tech-report.md) | 项目定位、版本演进、核心架构、生态、框架对比、优劣势与风险 |
| [AgentScope 可行性应用方向脑暴](docs/agentscope-applications-brainstorm.md) | 12 个应用方向及可行性分析、优先级矩阵、落地路线建议 |

**调研时间**：2026-08-01（信息以截至当日的公开资料为准）

**一句话结论**：AgentScope 已从"多智能体开发框架"演进为覆盖开发、运行、安全、部署、评测全生命周期的生产级 Agent 工程平台（当前 Python 主线 2.0），其事件系统、权限系统、Workspace 沙箱、多租户 Agent 服务等能力在同类开源框架中差异化明显，非常适合作为企业级 Agent 应用的技术底座；但版本迭代较快，选型时需要做稳定性评估。
