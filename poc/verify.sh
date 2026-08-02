#!/usr/bin/env bash
# 一键离线验证：离线测试 + 引擎装配冒烟（不调用模型、不依赖网络）
set -euo pipefail
cd "$(dirname "$0")"

PY="hello-agent/.venv/bin/python"

echo "== 1/3 离线测试 =="
"$PY" -m pytest tests -q

echo "== 2/3 领域列表 =="
"$PY" run_agent.py --list-domains

echo "== 3/3 引擎装配冒烟（假 key，不发请求） =="
DEEPSEEK_API_KEY=test-key "$PY" - <<'PY'
import sys
sys.path.insert(0, ".")
from domains import list_domains, load_domain
from engine.agent_engine import AgentEngine, EngineConfig

for name in list_domains():
    engine = AgentEngine(load_domain(name), EngineConfig(env_files=()))
    print(f"  OK {name}: tools={engine.registry.tool_names}")
print("装配冒烟通过")
PY

echo "全部通过 ✅"
