"""业务无关的 Agent 引擎层。

对外暴露：
- ``DomainPackage``：业务领域包契约（领域层必须实现）；
- ``ToolRegistry``：工具注册表（领域包 → 引擎 Toolkit 的中间契约）；
- ``AgentEngine / EngineConfig / AgentResult``：引擎装配与一轮问答执行。

引擎不 import 任何具体业务模块，业务差异全部由领域包注入。
"""

from .agent_engine import AgentEngine, AgentResult, EngineConfig
from .domain import DomainPackage
from .tool_registry import ToolRegistry

__all__ = [
    "AgentEngine",
    "AgentResult",
    "DomainPackage",
    "EngineConfig",
    "ToolRegistry",
]
