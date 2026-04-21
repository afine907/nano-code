"""测试异常类"""

from jojo_code.core.exceptions import (
    ConfigError,
    JojoCodeError,
    LLMError,
    SecurityError,
    ToolError,
    ValidationError,
)


class TestJojoCodeError:
    """JojoCodeError 测试"""

    def test_basic_error(self):
        """测试基本错误"""
        error = JojoCodeError("发生错误")
        assert error.message == "发生错误"
        assert error.hint is None
        assert str(error) == "发生错误"

    def test_error_with_hint(self):
        """测试带提示的错误"""
        error = JojoCodeError("发生错误", hint="请检查配置")
        assert error.message == "发生错误"
        assert error.hint == "请检查配置"
        assert "💡 提示: 请检查配置" in str(error)


class TestConfigError:
    """ConfigError 测试"""

    def test_config_error(self):
        """测试配置错误"""
        error = ConfigError("API Key 缺失", hint="请设置 OPENAI_API_KEY 环境变量")
        assert isinstance(error, JojoCodeError)
        assert error.message == "API Key 缺失"
        assert error.hint == "请设置 OPENAI_API_KEY 环境变量"


class TestLLMError:
    """LLMError 测试"""

    def test_llm_error(self):
        """测试 LLM 错误"""
        error = LLMError("API 调用失败", hint="请检查网络连接")
        assert isinstance(error, JojoCodeError)
        assert error.message == "API 调用失败"


class TestToolError:
    """ToolError 测试"""

    def test_tool_error(self):
        """测试工具错误"""
        error = ToolError("文件不存在", hint="请检查文件路径")
        assert isinstance(error, JojoCodeError)


class TestSecurityError:
    """SecurityError 测试"""

    def test_security_error(self):
        """测试安全错误"""
        error = SecurityError("权限不足", hint="请检查文件权限")
        assert isinstance(error, JojoCodeError)


class TestValidationError:
    """ValidationError 测试"""

    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError("输入无效", hint="请检查输入格式")
        assert isinstance(error, JojoCodeError)
