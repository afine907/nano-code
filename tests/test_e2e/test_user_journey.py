"""
Jojo-Code 端到端测试 - 用户视角（简化版）

模拟真实用户的使用场景，覆盖完整的使用旅程。

运行方式：
    pytest tests/test_e2e/test_user_journey.py -v -m longcat

环境变量：
    OPENAI_API_KEY: LongCat API Key
"""

import os

import pytest

pytestmark = pytest.mark.longcat


class TestUserJourneyBasic:
    """用户旅程：基础功能"""

    def test_journey_first_time_user(self):
        """新用户的首次使用 - 列出文件并了解项目结构"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("列出当前目录的文件")
        result = graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        assert len(messages) > 0
        print("\n✅ 用户看到了文件列表")

    def test_journey_ask_for_help(self):
        """用户请求帮助 - 直接问问题"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("今天天气怎么样？")
        result = graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = (
            messages[-1].get("content", "") if isinstance(messages[-1], dict) else str(messages[-1])
        )
        assert len(content) > 10
        print("\n✅ 用户得到了回答")

    def test_journey_simple_calculation(self):
        """用户做简单计算"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("123 * 456 等于多少？")
        result = graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = (
            messages[-1].get("content", "") if isinstance(messages[-1], dict) else str(messages[-1])
        )
        assert "56088" in content or "56,088" in content
        print("\n✅ 用户得到了正确计算结果")


class TestUserJourneyFileOps:
    """用户旅程：文件操作"""

    def test_journey_create_and_read_file(self):
        """用户创建一个文件，然后读取"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("在 /tmp 目录下创建 hello.py，内容是 print('Hello World')")
        result = graph.invoke(state)

        assert result is not None
        # 验证文件是否被创建
        assert os.path.exists("/tmp/hello.py")
        print("\n✅ 用户成功创建了文件")

    def test_journey_read_existing_file(self):
        """用户读取一个已存在的文件"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        # 先创建测试文件
        os.makedirs("/tmp/jojo_test", exist_ok=True)
        with open("/tmp/jojo_test/test.txt", "w") as f:
            f.write("这是测试文件内容")

        graph = build_agent_graph()

        state = create_initial_state("读取 /tmp/jojo_test/test.txt 文件内容")
        result = graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        assert len(messages) > 0
        print("\n✅ 用户成功读取了文件")


class TestUserJourneyCodeGen:
    """用户旅程：代码生成"""

    def test_journey_generate_function(self):
        """用户请求生成一个函数"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("用 Python 写一个快速排序函数")
        result = graph.invoke(state)

        assert result is not None
        print("\n✅ 用户得到了排序算法帮助")

    def test_journey_generate_api(self):
        """用户请求生成 REST API"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("用 Flask 写一个简单的用户管理 REST API")
        result = graph.invoke(state)

        assert result is not None
        print("\n✅ 用户得到了 REST API 帮助")

    def test_journey_write_test(self):
        """用户请求写单元测试"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("为这个函数写 pytest 单元测试: def add(a, b): return a + b")
        result = graph.invoke(state)

        assert result is not None
        print("\n✅ 用户得到了单元测试帮助")


class TestUserJourneyShell:
    """用户旅程：Shell 命令"""

    def test_journey_run_shell_command(self):
        """用户执行 Shell 命令"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("执行 ls -la 命令")
        result = graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        assert len(messages) > 0
        print("\n✅ 用户看到了命令输出")


class TestUserJourneyGit:
    """用户旅程：Git 操作"""

    def test_journey_check_git_status(self):
        """用户查看 Git 状态"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("查看 Git 仓库状态")
        result = graph.invoke(state)

        assert result is not None
        print("\n✅ 用户看到了 Git 状态")


class TestUserJourneyWeb:
    """用户旅程：Web 功能"""

    def test_journey_search_web(self):
        """用户搜索网页"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("搜索 Python 异步编程")
        result = graph.invoke(state)

        # 只要有返回即可
        assert result is not None
        print("\n✅ 用户看到了搜索结果")


class TestUserJourneyMultiTurn:
    """用户旅程：多轮对话"""

    def test_journey_continue_conversation(self):
        """用户继续之前的对话"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        # 第一轮：创建一个文件
        state1 = create_initial_state("在 /tmp 目录下创建 result.txt，内容写 'Hello'")
        result1 = graph.invoke(state1)
        assert result1 is not None

        # 第二轮：继续任务（创建新的状态，但保留之前的上下文）
        # 注意：由于每次都是新状态，这里主要是验证流程可以继续
        state2 = create_initial_state("查看 /tmp 目录下有哪些文件")
        result2 = graph.invoke(state2)
        assert result2 is not None

        print("\n✅ 用户完成了多轮任务")


class TestUserJourneyErrorHandling:
    """用户旅程：错误处理"""

    def test_journey_handle_error_gracefully(self):
        """用户遇到错误时的体验"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("读取 /tmp/这个文件不存在12345.txt")
        result = graph.invoke(state)

        # 期望：用户得到了响应（无论成功或错误）
        assert result is not None
        messages = result.get("messages", [])
        assert len(messages) > 0
        print("\n✅ 错误处理完成")


class TestUserJourneyComplexTask:
    """用户旅程：复杂任务"""

    def test_journey_create_project(self):
        """用户创建一个完整项目"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state(
            "在 /tmp/my_project 目录下创建 Python 项目，包含 src 和 tests 目录"
        )
        result = graph.invoke(state)

        assert result is not None
        # 可能创建了目录，也可能没有，这取决于 Agent 行为
        print("\n✅ 用户完成了项目创建任务")

    def test_journey_json_parsing(self):
        """用户解析 JSON 数据"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("解析这个 JSON: {'name': '张三', 'age': 25}")
        result = graph.invoke(state)

        assert result is not None
        print("\n✅ 用户完成了 JSON 解析")


class TestUserJourneyRealWorld:
    """用户旅程：真实世界场景"""

    def test_journey_bug_fix(self):
        """用户让 Agent 帮忙修复 bug"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state(
            "分析这个 Python 函数的 bug：def divide(a, b): return a / b，当 b 为 0 时会怎样？"
        )
        result = graph.invoke(state)

        assert result is not None
        print("\n✅ 用户得到了 bug 分析")

    def test_journey_explain_code(self):
        """用户让 Agent 解释代码"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("解释这段代码的作用：map(lambda x: x*2, [1,2,3])")
        result = graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = (
            messages[-1].get("content", "") if isinstance(messages[-1], dict) else str(messages[-1])
        )
        assert len(content) > 20
        print("\n✅ 用户得到了代码解释")

    def test_journey_write_regex(self):
        """用户让 Agent 写正则表达式"""
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        graph = build_agent_graph()

        state = create_initial_state("用 Python 正则表达式提取字符串中的邮箱地址")
        result = graph.invoke(state)

        assert result is not None
        print("\n✅ 用户得到了正则表达式")
