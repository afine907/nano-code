"""AgentTool - 将子 Agent 封装为 LangChain 工具"""

from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from jojo_code.agent.sub import AgentConfig, SubAgent


class AgentToolInput(BaseModel):
    """AgentTool 输入schema"""

    task: str = Field(description="要执行的任务描述")
    context: dict[str, Any] = Field(default_factory=dict, description="传递给 Agent 的额外上下文")


class AgentTool(BaseTool):
    """Agent 工具 - 将 SubAgent 封装为 LangChain 工具

    使用方式:
        agent = create_sub_agent(name="my_agent", tools=["read_file", "write_file"])
        tool = AgentTool(agent=agent)
        result = tool.invoke({"task": "帮我读取 README.md"})
    """

    name: str = "agent"
    description: str = "执行子 Agent 完成复杂任务"
    args_schema: type[BaseModel] = AgentToolInput

    def __init__(
        self,
        agent: SubAgent | None = None,
        name: str | None = None,
        description: str | None = None,
        **kwargs,
    ):
        # 如果提供了 agent，使用其配置
        if agent:
            kwargs["name"] = name or f"agent_{agent.config.name}"
            kwargs["description"] = description or agent.config.description
            # 存储 agent 引用（不在 schema 中）
            object.__setattr__(self, "_agent", agent)
        else:
            object.__setattr__(self, "_agent", None)

        super().__init__(**kwargs)

    @property
    def _sub_agent(self) -> SubAgent | None:
        return object.__getattribute__(self, "_agent")

    def _run(self, task: str, context: dict[str, Any] | None = None) -> Any:
        """同步执行"""
        from jojo_code.agent.sub import AgentRequest

        if not self._sub_agent:
            return {"error": "Agent 未初始化"}

        request = AgentRequest(
            task=task,
            context=context or {},
        )

        response = self._sub_agent.run(request)

        if response.success:
            return {
                "result": response.result,
                "iterations": response.iterations,
                "duration": response.duration,
            }
        else:
            return {"error": response.error}

    async def _arun(self, task: str, context: dict[str, Any] | None = None) -> Any:
        """异步执行"""
        from jojo_code.agent.sub import AgentRequest

        if not self._sub_agent:
            return {"error": "Agent 未初始化"}

        request = AgentRequest(
            task=task,
            context=context or {},
        )

        response = await self._sub_agent.run_async(request)

        if response.success:
            return {
                "result": response.result,
                "iterations": response.iterations,
                "duration": response.duration,
            }
        else:
            return {"error": response.error}


def create_agent_tool(
    name: str,
    description: str = "",
    tools: list[str] | None = None,
    model: str = "claude-sonnet-4-20250514",
    **kwargs,
) -> AgentTool:
    """快速创建 AgentTool

    Args:
        name: Agent 名称
        description: Agent 描述
        tools: 可用工具列表
        model: 使用的模型
        **kwargs: 其他配置

    Returns:
        AgentTool 实例
    """
    # 创建 SubAgent
    config = AgentConfig(
        name=name,
        description=description,
        tools=tools or [],
        model=model,
        **kwargs,
    )
    agent = SubAgent(config)

    # 封装为工具
    return AgentTool(
        agent=agent,
        name=f"agent_{name}",
        description=description or f"执行 {name} 任务",
    )


# 内置 Agent 工厂
class BuiltInAgents:
    """内置 Agent 工厂"""

    @staticmethod
    def code_review_agent() -> AgentTool:
        """代码审查 Agent"""
        return create_agent_tool(
            name="code_reviewer",
            description="审查代码并提供改进建议",
            tools=["read_file", "glob_search", "grep_search"],
            system_prompt="你是一个代码审查专家。审查用户提供的代码，指出问题并提供改进建议。",
        )

    @staticmethod
    def research_agent() -> AgentTool:
        """研究 Agent"""
        return create_agent_tool(
            name="researcher",
            description="搜索和研究信息",
            tools=["web_search", "read_file"],
            system_prompt="你是一个研究助手。帮助用户搜索和研究信息，整理成简洁的报告。",
        )

    @staticmethod
    def debug_agent() -> AgentTool:
        """调试 Agent"""
        return create_agent_tool(
            name="debugger",
            description="帮助调试代码问题",
            tools=["read_file", "run_command", "grep_search"],
            system_prompt="你是一个调试专家。帮助用户定位和修复代码问题。",
        )


__all__ = [
    "AgentTool",
    "AgentToolInput",
    "create_agent_tool",
    "BuiltInAgents",
]
