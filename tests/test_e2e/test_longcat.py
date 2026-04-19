"""LongCat API 真实调用测试

配置方式（设置环境变量）：
- OPENAI_API_KEY: LongCat API Key
- OPENAI_BASE_URL: https://api.longcat.chat/openai/v1
- MODEL: LongCat-Flash-Chat

运行: pytest -m longcat tests/test_e2e/test_longcat.py -v
"""

import os

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

pytestmark = pytest.mark.longcat


@pytest.fixture
def longcat_configured():
    """检查 LongCat 配置是否完整"""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY 未设置")
    if not os.getenv("OPENAI_BASE_URL"):
        pytest.skip("OPENAI_BASE_URL 未设置")


class TestLongCatBasicChat:
    """测试基本对话功能"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from nano_code.core.llm import get_llm

        self.llm = get_llm()

    def test_simple_completion(self):
        """测试简单对话"""
        response = self.llm.invoke("用中文说'你好世界'")

        assert response is not None
        assert len(response.content) > 0
        print(f"\n响应: {response.content}")

    def test_multi_turn_conversation(self):
        """测试多轮对话"""
        messages = [
            SystemMessage(content="你是一个有帮助的助手，请简短回答"),
            HumanMessage(content="2+2等于多少？只回答数字"),
        ]

        response = self.llm.invoke(messages)

        assert response is not None
        print(f"\n响应: {response.content}")


class TestLongCatToolCalling:
    """测试工具调用功能"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from nano_code.core.llm import get_llm

        self.llm = get_llm()

    def test_tool_binding(self):
        """测试工具绑定"""
        from nano_code.tools.registry import get_tool_registry

        registry = get_tool_registry()
        tools = registry.get_langchain_tools()

        llm_with_tools = self.llm.bind_tools(tools)

        assert llm_with_tools is not None

    def test_simple_tool_call(self):
        """测试简单工具调用"""
        from langchain_core.tools import tool

        @tool
        def get_weather(location: str) -> str:
            """获取指定位置的天气"""
            return f"{location}的天气：晴，25°C"

        llm_with_tools = self.llm.bind_tools([get_weather])
        response = llm_with_tools.invoke("北京今天天气怎么样？")

        assert response is not None
        print(f"\n响应: {response}")
        if hasattr(response, "tool_calls") and response.tool_calls:
            print(f"工具调用: {response.tool_calls}")


class TestLongCatAgentIntegration:
    """测试 Agent 集成"""

    @pytest.mark.slow
    def test_agent_with_longcat(self, longcat_configured, monkeypatch):
        """测试 Agent 使用 LongCat"""
        from nano_code.agent.graph import build_agent_graph
        from nano_code.agent.state import create_initial_state

        graph = build_agent_graph()
        state = create_initial_state("你好，请自我介绍")
        result = graph.invoke(state)

        assert result is not None
        print(f"\n最终状态: {result}")

    @pytest.mark.slow
    def test_agent_with_file_tool(self, longcat_configured, tmp_path):
        """测试 Agent 使用文件工具"""
        from nano_code.agent.graph import build_agent_graph
        from nano_code.agent.state import create_initial_state

        test_file = tmp_path / "test.txt"
        test_file.write_text("这是一个测试文件的内容。\n第二行内容。")

        graph = build_agent_graph()
        state = create_initial_state(f"请读取文件 {test_file} 的内容")
        result = graph.invoke(state)

        assert result is not None
        print(f"\n最终状态: {result}")

    @pytest.mark.slow
    def test_agent_with_shell_tool(self, longcat_configured, tmp_path):
        """测试 Agent 调用 shell 工具"""
        from nano_code.agent.graph import build_agent_graph
        from nano_code.agent.state import create_initial_state

        graph = build_agent_graph()
        state = create_initial_state("列出当前目录的文件")
        result = graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        assert len(messages) > 0
        print(f"\n响应: {messages[-1]}")

    @pytest.mark.slow
    def test_agent_combined_flow(self, longcat_configured, tmp_path):
        """测试 Agent 组合流程：创建文件 → 读取 → 执行"""
        from nano_code.agent.graph import build_agent_graph
        from nano_code.agent.state import create_initial_state

        test_file = tmp_path / "hello.py"
        test_file.write_text("print('Hello World')")

        graph = build_agent_graph()
        state = create_initial_state(f"请读取文件 {test_file}，然后执行它")
        result = graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        assert len(messages) > 0
        print(f"\n最终状态: {result}")

    @pytest.mark.slow
    def test_agent_error_handling(self, longcat_configured):
        """测试 Agent 异常处理"""
        from nano_code.agent.graph import build_agent_graph
        from nano_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("")
        result = graph.invoke(state)

        assert result is not None
        print(f"\n空输入处理: {result}")
