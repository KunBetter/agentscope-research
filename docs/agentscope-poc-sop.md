# AgentScope POC 使用 SOP（Standard Operating Procedure）

> 适用范围：`poc/` 目录（业务无关 Agent 引擎 + 领域包 + 评测基线）
> 维护日期：2026-08-30 ｜ 配套文档：[poc/README.md](../poc/README.md)（实现细节）、[后续规划](agentscope-next-steps-plan.md)（方向与里程碑）
> 原则：**一切可复现、可回归**。离线验证不依赖网络/模型；评测基于确定性 mock 数据。

---

## 0. 一页速览（TL;DR）

```bash
# 首次使用（新机器 / 新克隆）
cd poc
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt        # 运行时 + pytest
# 配置 API Key：复制 .env.example 为 poc/.env 并填入真实 key

# 日常验证（改动后必跑，离线）
./verify.sh

# 单轮问答（需有效 API Key + 网络）
.venv/bin/python run_agent.py --domain stock_qa

# 建基线 / 回归（需有效 API Key + 网络，产物不入库）
.venv/bin/python poc/eval/run_eval.py --all
.venv/bin/python poc/eval/run_eval.py --domain stock_qa --baseline <上次结果.json>
```

**改动后必做**：① `./verify.sh` 全绿；② 涉及评测任务的改动重跑 `--all` 并刷新基线数字；③ 同步本文档 / `poc/README.md` / 规划日志。

---

## 1. 环境准备（首次使用 / 新机器）

### 1.1 依赖安装（Python 3.11+，已验证 3.12）

```bash
cd poc
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # 内含 requirements.txt（运行时）+ pytest
```

> 依赖版本锁定在 `requirements.txt`（当前 `agentscope==2.0.5` / `pydantic==2.13.4` / `python-dotenv==1.2.2`）。
> 若本机已有 `hello-agent/.venv`（旧环境），`verify.sh` 会自动回退使用，无需重建。

### 1.2 配置 API Key

优先级：`poc/.env` > `poc/hello-agent/.env` > 环境变量。

```bash
cp .env.example .env    # 编辑填入 DEEPSEEK_API_KEY
```

- `.env` 已被 gitignore，不会入库；
- 缺失 Key 时引擎抛 `MissingApiKeyError`，CLI 打印清晰错误并以**退出码 2** 结束（不抛堆栈）；
- 注意：shell 中 export 的旧 key 可能静默覆盖 `.env`——本仓库实现为本地 `.env` 优先，若仍出现 401 先查 shell 环境变量。

### 1.3 验证环境

```bash
./verify.sh    # 离线：41 个测试 + 领域列表 + 引擎装配冒烟
```

---

## 2. 常规操作

所有命令在 `poc/` 目录下执行，`run_*` 类命令需要有效 API Key 与网络（模型调用）。

| 目的 | 命令 | 说明 |
| --- | --- | --- |
| 一键离线回归 | `./verify.sh` | 改动后必跑；不调用模型 |
| 单轮问答 | `.venv/bin/python run_agent.py --domain stock_qa` | 默认问题；`--question` 自定义 |
| 列领域包 | `.venv/bin/python run_agent.py --list-domains` | 离线可用 |
| token 预算 | `.venv/bin/python run_agent.py --domain stock_qa --budget 6000` | 启用 `ReplyBudgetControlMiddleware` |
| 模型重试/回退 | `.venv/bin/python run_agent.py --max-retries 2 --fallback-model deepseek-v4-pro` | 网络抖动时兜底 |
| 多轮会话（短期记忆） | `.venv/bin/python poc/run_conversation.py --domain stock_qa` | 同一引擎多轮 = 同一会话 |
| 上下文压缩演示 | `.venv/bin/python poc/run_conversation.py --domain weather --compression-demo` | 已知限制见 §7 |
| HITL 写工具确认 | `.venv/bin/python poc/run_hitl_demo.py`（deny）／`--confirm` | 两分支端到端验证 |
| 长期记忆（跨会话） | `.venv/bin/python poc/run_memory_demo.py --reset` | `--reset` 清空记忆目录 |

---

## 3. 评测流程（基线 → 回归 → 结论）

评测基于**确定性 mock 数据**：结果可精确打分、可跨版本回归。任务集：stock_qa 30 条 / weather 10 条 / todo 5 条。

### 3.1 首次建立基线

```bash
.venv/bin/python poc/eval/run_eval.py --all
```

- 输出跨领域汇总表，并落盘 `poc/eval/results/<领域>_mock_<时间戳>.json` 与 `all_summary_<时间戳>.json`；
- 退出码：任一领域准确率 < 阈值（默认 0.8）返回 1（CI 可直接依赖）；
- **基线数字写回文档**：把汇总结果更新到 `poc/README.md` §4 与根 `README.md` 进展日志，并注明时间戳。

### 3.2 日常回归（改动后）

```bash
.venv/bin/python poc/eval/run_eval.py --domain stock_qa --baseline <上次结果.json>
.venv/bin/python poc/eval/run_eval.py --all        # 跨领域一致性
```

- `--baseline` 输出 修复/回归/新增 差异；**存在回归时退出码 1**；
- 对比对象：上次运行留存的结果文件（不跨网络保存）。

### 3.3 产物与 git 的关系

- `poc/eval/results/` 已 **gitignore，禁止入库**（属于可再生成的运行产物）；
- 需要长期参照的基线数字以文档形式（README §4）维护，而非结果文件本身；
- 提交前检查：`git status` 不应出现 `eval/results/`、`__pycache__/`、`.pytest_cache/`、`.env`。

### 3.4 任务集与检查项格式（`poc/eval/tasks/*.jsonl`）

每行一条任务：`{"id": "sq-001", "question": "...", "check": [{...}]}`。

- `check` 支持：`contains`（子串）、`any_of`（任一子串命中，容忍 LLM 措辞变体）、`paths`（多个字段任一命中）；
- 字段路径：`["financials", "*"]` 遍历 dict 全部值；`["@text"]` 检查自然语言回答；
- **新增任务规则**：`id` 全局唯一；检查项的值必须与 mock 数据一致（改 mock 必须同步改任务，反之亦然）；单条任务可含多个 check（全部通过才计为通过）。

---

## 4. 开发流程

### 4.1 新增业务领域包（三步，引擎零改动）

1. 新建 `poc/domains/<业务名>/`：`tools.py`（普通函数）+ `prompts.py`（system prompt）+ `schemas.py`（Pydantic 模型）+ `domain.py`（`DomainPackage` 子类）；
2. 在 `domain.py` 覆写 `register_tools(registry)`，用 `registry.register(...)` 声明工具（写工具必须 `read_only=False`，会触发 HITL 确认）；
3. 在 `poc/domains/__init__.py` 的 `DOMAIN_REGISTRY` 登记，并在 `run_agent.py` 的 `DEFAULT_QUESTIONS` 补示例问题。

完成后：`./verify.sh` 覆盖"装配冒烟"，再按 §4.3 提交。

### 4.2 修改引擎 / 领域层代码

- 引擎层（`poc/engine/`）保持**业务无关**：不 import 任何 `domains/` 模块；
- 领域状态类（如 todo 列表）须在 `register_tools` 时重置，保证评测逐任务隔离；
- 改完跑 `./verify.sh`；涉及评测行为（工具返回值、prompt、schema）的改动，重跑 `--all` 并刷新基线文档。

### 4.3 提交前检查清单（Checklist）

- [ ] `./verify.sh` 全绿（41 测试 + 装配冒烟）
- [ ] `git status` 无产物入库（`eval/results/`、`__pycache__/`、`.pytest_cache/`、`.env`）
- [ ] 评测任务集改动 → 基线数字已更新或标注"待重跑 `--all`"
- [ ] 文档同步：`poc/README.md`（行为变化）、本文档（命令/流程变化）、规划执行日志（`docs/agentscope-next-steps-plan.md`）
- [ ] 未引入新依赖 → 若引入，更新 `requirements.txt` 锁版本

---

## 5. 版本升级流程（AgentScope / 依赖）

1. **升级前**：查 PyPI / GitHub release notes，确认破坏性变更（1.0→2.0 曾有大规模重构，Runtime 仓库已归档）；
2. 确认升级目标后：修改 `requirements.txt` 锁版本 → 重建/更新 venv → 跑 `./verify.sh`；
3. **必验项**（历史教训）：
   - DeepSeek formatter / 工具调用 / 结构化输出兼容性（`run_agent.py --domain stock_qa`）；
   - 上下文压缩 + 结构化输出组合是否仍稳定（`--compression-demo`，2.0.5 下间歇性不稳定）；
   - 官方评测模块是否恢复（2.0.5 中缺失，结论记录于 `poc/README.md` §4）；
   - 重跑 `--all` 建新基线；
4. 更新文档中的版本复核结论（根 `README.md` 进展日志 + 本 SOP 无版本号硬编码处检查）。

---

## 6. 故障排查（FAQ）

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `401 Authentication Fails` | API Key 无效 / 被 shell 旧 key 覆盖 | 检查 `.env` 与 shell 环境变量；先手动 curl 验证 key |
| `错误: 缺少 DEEPSEEK_API_KEY…`（退出码 2） | 未配置 Key | 按 §1.2 配置 `.env`；`run_*` 命令缺 Key 属配置错误，应整体退出而非逐条失败 |
| 模型调用 `exhausted all attempts` | 网络 / 限流 / 凭据失败 | 看异常根因；加 `--max-retries 2 --fallback-model deepseek-v4-pro` |
| 找不到 agentscope 模块 | venv 不对 / 未安装 | 统一用 `.venv/bin/python`（或 `hello-agent/.venv/bin/python`） |
| 压缩后结构化输出失败（`--compression-demo`） | 已知限制：2.0.5 + DeepSeek 间歇性不稳定 | 重试一次；默认压缩阈值（0.8）下正常对话不触发 |
| 评测全部失败且非 Key 问题 | 任务/检查项与 mock 不一致 | 按 §3.4 校验任务集；`--limit 3` 先跑前 3 条定位 |
| 升级 AgentScope 后测试挂 | 测试依赖框架私有 API（`_reply_middlewares` 等，有注释标注） | 按 §5 复验；必要时调整测试断言 |

---

## 7. 命令速查表

```bash
# 环境
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env

# 离线验证
./verify.sh
.venv/bin/python -m pytest tests -q

# 运行（需 Key + 网络）
.venv/bin/python run_agent.py --list-domains
.venv/bin/python run_agent.py --domain stock_qa [--question "…"] [--budget 6000] [--max-retries 2] [--fallback-model deepseek-v4-pro] [--memory-dir poc/memory/stock_qa]
.venv/bin/python poc/run_conversation.py --domain stock_qa [--compression-demo]
.venv/bin/python poc/run_hitl_demo.py [--confirm]
.venv/bin/python poc/run_memory_demo.py [--reset]

# 评测（需 Key + 网络）
.venv/bin/python poc/eval/run_eval.py --domain stock_qa [--limit 3] [--threshold 0.8]
.venv/bin/python poc/eval/run_eval.py --all
.venv/bin/python poc/eval/run_eval.py --domain stock_qa --baseline <上次结果.json>
```
