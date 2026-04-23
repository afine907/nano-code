"""AgentOps 配置"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OpsConfig:
    """AgentOps 配置"""

    # 是否启用
    enabled: bool = True

    # 是否持久化 Trace
    persist_traces: bool = True

    # Trace 存储目录
    trace_dir: str = ".jojo-code/traces"

    # 内存中最大保留的 Trace 数量
    max_traces_in_memory: int = 1000

    # 是否实时显示
    real_time_display: bool = False

    @classmethod
    def from_env(cls) -> "OpsConfig":
        """从环境变量加载配置"""
        return cls(
            enabled=os.getenv("JOJO_CODE_OPS_ENABLED", "true").lower() == "true",
            persist_traces=os.getenv("JOJO_CODE_OPS_PERSIST", "true").lower() == "true",
            trace_dir=os.getenv("JOJO_CODE_OPS_TRACE_DIR", ".jojo-code/traces"),
            max_traces_in_memory=int(os.getenv("JOJO_CODE_OPS_MAX_TRACES", "1000")),
            real_time_display=os.getenv("JOJO_CODE_OPS_REALTIME", "false").lower() == "true",
        )

    def get_trace_path(self) -> Path:
        """获取 Trace 目录路径"""
        return Path(self.trace_dir)
