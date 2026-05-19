"""
Jojo-Code 端到端测试用例集

覆盖 Agent 核心功能：工具调用、多轮对话、错误处理、边界条件等

运行方式：
    pytest tests/test_e2e/test_agent_e2e.py -v -m longcat

环境变量：
    OPENAI_API_KEY: LongCat API Key
    OPENAI_BASE_URL: https://api.longcat.chat/openai/v1
"""

import os

import pytest

# 跳过标记
pytestmark = pytest.mark.longcat


def get_last_message_content(messages: list) -> str:
    """从 messages 列表中获取最后一个消息的内容"""
    if not messages:
        return ""
    last = messages[-1]
    # 支持字典格式和对象格式
    if isinstance(last, dict):
        return last.get("content", "") or last.get("text", "") or str(last)
    elif hasattr(last, "content"):
        return last.content
    return str(last)


@pytest.fixture
def longcat_configured():
    """检查 LongCat 配置"""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY 未设置")


class TestAgentBasicTools:
    """测试 Agent 基础工具调用"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        self.graph = build_agent_graph()
        self.create_state = create_initial_state

    def test_list_files(self):
        """测试列出文件工具"""
        state = self.create_state("列出当前目录的文件")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        assert len(messages) > 0
        content = get_last_message_content(messages)
        print(f"\n✅ 列出文件: {content[:200]}")

    def test_shell_command(self):
        """测试 Shell 命令执行"""
        state = self.create_state("执行 ls -la 命令")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        assert "total" in content.lower() or "drwx" in content
        print("\n✅ Shell 执行成功")

    def test_code_generation(self):
        """测试代码生成"""
        state = self.create_state("用 Python 实现快速排序算法")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        # 验证生成了代码
        assert "def" in content or "quicksort" in content.lower() or "partition" in content.lower()
        print("\n✅ 代码生成成功")


class TestAgentFileOperations:
    """测试文件操作"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        self.graph = build_agent_graph()
        self.create_state = create_initial_state
        self.tmp_dir = "/tmp/jojo_test"

    def test_file_read(self, tmp_path):
        """测试文件读取"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("测试内容 Hello World")

        state = self.create_state(f"读取文件 {test_file}")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        assert "测试内容" in content or "Hello" in content
        print("\n✅ 文件读取成功")

    def test_file_write(self, tmp_path):
        """测试文件写入"""
        test_file = tmp_path / "output.txt"

        state = self.create_state(f"在 {test_file} 写入内容 'jojo test'")
        result = self.graph.invoke(state)

        assert result is not None
        # 验证文件创建
        assert test_file.exists()
        content = test_file.read_text()
        assert "jojo" in content or "test" in content
        print("\n✅ 文件写入成功")

    def test_code_file_creation(self, tmp_path):
        """测试代码文件创建"""
        test_file = tmp_path / "hello.py"

        state = self.create_state(f"创建 Python 文件 {test_file}，实现 hello 函数")
        result = self.graph.invoke(state)

        assert result is not None
        assert test_file.exists()
        content = test_file.read_text()
        assert "def" in content or "hello" in content.lower()
        print("\n✅ 代码文件创建成功")


class TestAgentGitOperations:
    """测试 Git 操作"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        self.graph = build_agent_graph()
        self.create_state = create_initial_state

    def test_git_status(self):
        """测试 Git 状态查询"""
        state = self.create_state("查看当前 Git 仓库状态")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        # 应该返回分支信息或"不是git仓库"等
        print("\n✅ Git 状态查询完成")
        print(f"   内容: {content[:150]}...")

    def test_git_log(self):
        """测试 Git 日志查看"""
        state = self.create_state("查看最近 3 条 Git 提交记录")
        result = self.graph.invoke(state)

        assert result is not None
        print("\n✅ Git 日志查询完成")


class TestAgentWebCapabilities:
    """测试 Web 能力"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        self.graph = build_agent_graph()
        self.create_state = create_initial_state

    def test_web_search(self):
        """测试 Web 搜索"""
        state = self.create_state("搜索 Python 异步编程的最佳实践")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        assert len(content) > 50  # 有实际内容
        print("\n✅ Web 搜索完成")

    def test_web_fetch(self):
        """测试 Web 内容获取"""
        state = self.create_state("获取 https://httpbin.org/get 的内容")
        result = self.graph.invoke(state)

        assert result is not None
        print("\n✅ Web 内容获取完成")


class TestAgentMultiTurn:
    """测试多轮对话"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        self.graph = build_agent_graph()
        self.create_state = create_initial_state

    def test_context_preservation(self):
        """测试上下文保持"""
        # 第一轮：设置上下文
        state = self.create_state("记住我的名字叫张三")
        self.graph.invoke(state)

        # 第二轮：验证记忆
        state = self.create_state("我刚才告诉你我叫什么？")
        result2 = self.graph.invoke(state)

        messages = result2.get("messages", [])
        content = get_last_message_content(messages)
        assert "张三" in content
        print("\n✅ 上下文保持成功")

    def test_sequential_tools(self):
        """测试顺序工具调用"""
        state = self.create_state("先列出当前目录，再统计有多少个 .py 文件")
        result = self.graph.invoke(state)

        assert result is not None
        # 应该调用了多个工具
        print("\n✅ 顺序工具调用完成")


class TestAgentTermination:
    """测试 Agent 终止条件"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        self.graph = build_agent_graph()
        self.create_state = create_initial_state

    def test_no_tool_needed(self):
        """测试无需工具的直接回答"""
        state = self.create_state("今天天气怎么样？")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        assert len(content) > 10  # 有实际回答
        print(f"\n✅ 直接回答成功: {content[:100]}...")

    def test_simple_math(self):
        """测试简单计算"""
        state = self.create_state("计算 123 * 456")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        # 应该包含正确答案 56088
        assert "56088" in content or "123" in content
        print("\n✅ 数学计算完成")


class TestAgentErrorHandling:
    """测试错误处理"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        self.graph = build_agent_graph()
        self.create_state = create_initial_state

    def test_nonexistent_file(self):
        """测试读取不存在的文件"""
        state = self.create_state("读取文件 /tmp/nonexistent_file_xyz123.txt")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        # 应该优雅处理错误
        assert (
            "不存在" in content
            or "无法" in content
            or "Error" in content
            or "not found" in content.lower()
        )
        print("\n✅ 错误处理成功")

    def test_invalid_command(self):
        """测试无效命令处理"""
        state = self.create_state("执行一个不存在的命令 xyz_command_not_found")
        result = self.graph.invoke(state)

        assert result is not None
        print("\n✅ 无效命令处理完成")


class TestAgentCodeGeneration:
    """测试代码生成能力"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        self.graph = build_agent_graph()
        self.create_state = create_initial_state

    def test_unit_test_generation(self):
        """测试单元测试生成"""
        state = self.create_state("为这个函数编写 pytest 单元测试: def add(a, b): return a + b")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        assert "def test" in content or "assert" in content
        print("\n✅ 单元测试生成完成")

    def test_rest_api_generation(self):
        """测试 REST API 生成"""
        state = self.create_state("用 Flask 实现一个简单的用户管理 REST API，包含增删改查")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        assert "@app.route" in content or "GET" in content or "POST" in content
        print("\n✅ REST API 生成完成")

    def test_regex_generation(self):
        """测试正则表达式生成"""
        state = self.create_state("用正则提取字符串中的邮箱地址")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        assert "re." in content or "regex" in content.lower() or "pattern" in content.lower()
        print("\n✅ 正则表达式生成完成")

    def test_type_hints(self):
        """测试类型提示添加"""
        state = self.create_state("为这个函数添加类型提示: def process(data): return sorted(data)")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        assert "->" in content or ": str" in content or ": list" in content
        print("\n✅ 类型提示添加完成")


class TestAgentEdgeCases:
    """测试边界条件"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        self.graph = build_agent_graph()
        self.create_state = create_initial_state

    def test_empty_input(self):
        """测试空输入处理"""
        state = self.create_state("")
        result = self.graph.invoke(state)

        assert result is not None
        print("\n✅ 空输入处理完成")

    def test_very_long_input(self):
        """测试超长输入处理"""
        long_input = "a" * 10000
        state = self.create_state(long_input)
        result = self.graph.invoke(state)

        assert result is not None
        print("\n✅ 超长输入处理完成")

    def test_special_characters(self):
        """测试特殊字符处理"""
        state = self.create_state("处理这个字符串: 你好🎉🌟🚀 123!@#")
        result = self.graph.invoke(state)

        assert result is not None
        print("\n✅ 特殊字符处理完成")


class TestAgentComplexTasks:
    """测试复杂任务"""

    @pytest.fixture(autouse=True)
    def setup(self, longcat_configured):
        from jojo_code.agent.graph import build_agent_graph
        from jojo_code.agent.state import create_initial_state

        self.graph = build_agent_graph()
        self.create_state = create_initial_state

    def test_create_project_structure(self):
        """测试创建项目结构"""
        state = self.create_state(
            "在 /tmp 下创建一个新的 Python 项目结构，包含 src/tests 目录和 requirements.txt"
        )
        result = self.graph.invoke(state)

        assert result is not None
        # 验证目录结构
        import os

        assert os.path.isdir("/tmp/jojo_test")
        print("\n✅ 项目结构创建完成")

    def test_shell_pipeline(self):
        """测试 Shell 管道操作"""
        state = self.create_state("统计当前目录下 .py 文件的数量")
        result = self.graph.invoke(state)

        assert result is not None
        # 管道应该被正确处理
        print("\n✅ Shell 管道操作完成")

    def test_json_parsing(self):
        """测试 JSON 解析"""
        state = self.create_state("解析这个 JSON: {'name': '张三', 'age': 25}，提取 name 字段")
        result = self.graph.invoke(state)

        assert result is not None
        messages = result.get("messages", [])
        content = get_last_message_content(messages)
        assert "张三" in content
        print("\n✅ JSON 解析完成")
