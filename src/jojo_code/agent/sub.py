"""子 Agent 支持 - AgentTool 实现"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from jojo_code.task import TaskType, generate_task_id


@dataclass
class AgentConfig:
    """子 Agent 配置"""

    name: str  # Agent 名称
    description: str = ""  # Agent 描述
    model: str = "claude-sonnet-4-20250514"  # 使用的模型
    max_iterations: int = 50  # 最大迭代次数
    timeout: float = 300.0  # 超时时间 (秒)
    tools: list[str] = field(default_factory=list)  # 可用工具
    system_prompt: str = ""  # 系统提示词


@dataclass
class AgentRequest:
    """Agent 请求"""

    task: str  # 任务描述
    context: dict[str, Any] = field(default_factory=dict)  # 上下文
    parent_task_id: str | None = None  # 父任务 ID


@dataclass
class AgentResponse:
    """Agent 响应"""

    success: bool
    result: Any = None
    error: str | None = None
    iterations: int = 0
    duration: float = 0.0
    tokens_used: int = 0


class SubAgent:
    """子 Agent

    可以被工具调用,创建独立的 Agent 执行任务。
    支持并行执行、状态共享。
    """

    _instances: dict[str, "SubAgent"] = {}

    def __init__(self, config: AgentConfig):
        self.config = config
        self._task_id: str | None = None
        self._status: str = "idle"
        self._history: list[dict[str, Any]] = []
        self._shared_state: dict[str, Any] = {}

    @property
    def id(self) -> str:
        return self._task_id or ""

    @property
    def status(self) -> str:
        return self._status

    def run(self, request: AgentRequest) -> AgentResponse:
        """同步运行 Agent

        Args:
            request: Agent 请求

        Returns:
            Agent 响应
        """
        start_time = datetime.now()
        self._status = "running"
        self._task_id = generate_task_id(TaskType.AGENT)

        try:
            # 初始化 LLM
            from jojo_code.core.llm import get_llm

            llm = get_llm()

            # 构建消息
            messages = []
            if self.config.system_prompt:
                messages.append({"role": "system", "content": self.config.system_prompt})
            messages.append({"role": "user", "content": request.task})

            # 迭代执行
            iterations = 0
            while iterations < self.config.max_iterations:
                iterations += 1

                # 调用 LLM
                response = llm.invoke(messages)

                # 检查是否需要工具调用
                if hasattr(response, "tool_calls") and response.tool_calls:
                    # 执行工具
                    for tool_call in response.tool_calls:
                        result = self._execute_tool(tool_call)
                        messages.append(
                            {
                                "role": "assistant",
                                "content": response.content,
                            }
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": str(result),
                            }
                        )
                else:
                    # 完成,返回结果
                    self._status = "completed"
                    duration = (datetime.now() - start_time).total_seconds()
                    return AgentResponse(
                        success=True,
                        result=response.content,
                        iterations=iterations,
                        duration=duration,
                    )

            # 超出最大迭代
            self._status = "timeout"
            return AgentResponse(
                success=False,
                error=f"超出最大迭代次数 {self.config.max_iterations}",
                iterations=iterations,
            )

        except Exception as e:
            self._status = "error"
            return AgentResponse(
                success=False,
                error=str(e),
                iterations=0,
            )

    async def run_async(self, request: AgentRequest) -> AgentResponse:
        """异步运行 Agent

        Args:
            request: Agent 请求

        Returns:
            Agent 响应
        """
        # 简化版本,实际可以用 asyncio.to_thread
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, request)

    def _execute_tool(self, tool_call: dict[str, Any]) -> Any:
        """执行工具调用

        Args:
            tool_call: 工具调用信息

        Returns:
            工具执行结果
        """
        # TODO: 实现工具执行
        tool_name = tool_call.get("name", "")

        # 这里应该调用 ToolRegistry
        return {"tool": tool_name, "result": "not implemented"}

    def get_history(self) -> list[dict[str, Any]]:
        """获取执行历史"""
        return self._history.copy()

    def set_shared_state(self, key: str, value: Any) -> None:
        """设置共享状态"""
        self._shared_state[key] = value

    def get_shared_state(self, key: str) -> Any:
        """获取共享状态"""
        return self._shared_state.get(key)

    @classmethod
    def get_instance(cls, name: str) -> "SubAgent | None":
        """获取已注册的 Agent 实例"""
        return cls._instances.get(name)

    @classmethod
    def register(cls, agent: "SubAgent") -> None:
        """注册 Agent 实例"""
        cls._instances[agent.config.name] = agent

    @classmethod
    def unregister(cls, name: str) -> bool:
        """注销 Agent 实例"""
        return cls._instances.pop(name, None) is not None


class AgentRegistry:
    """Agent 注册中心"""

    def __init__(self):
        self._agents: dict[str, SubAgent] = {}
        self._default_config = AgentConfig(name="default")

    def register(self, agent: SubAgent) -> None:
        """注册 Agent

        Args:
            agent: SubAgent 实例
        """
        self._agents[agent.config.name] = agent
        SubAgent.register(agent)

    def unregister(self, name: str) -> bool:
        """注销 Agent

        Args:
            name: Agent 名称

        Returns:
            是否成功
        """
        agent = self._agents.pop(name, None)
        if agent:
            SubAgent.unregister(name)
            return True
        return False

    def get(self, name: str) -> SubAgent | None:
        """获取 Agent

        Args:
            name: Agent 名称

        Returns:
            SubAgent 实例
        """
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        """列出所有 Agent"""
        return list(self._agents.keys())

    def create_agent(
        self,
        name: str,
        description: str = "",
        **kwargs,
    ) -> SubAgent:
        """创建并注册新 Agent

        Args:
            name: Agent 名称
            description: Agent 描述
            **kwargs: 其他配置

        Returns:
            SubAgent 实例
        """
        config = AgentConfig(name=name, description=description, **kwargs)
        agent = SubAgent(config)
        self.register(agent)
        return agent


# 全局注册中心
_agent_registry = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    """获取 Agent 注册中心"""
    return _agent_registry


def create_agent(name: str, **kwargs) -> SubAgent:
    """快速创建 Agent"""
    return _agent_registry.create_agent(name, **kwargs)


__all__ = [
    "AgentConfig",
    "AgentRequest",
    "AgentResponse",
    "SubAgent",
    "AgentRegistry",
    "get_agent_registry",
    "create_agent",
]
