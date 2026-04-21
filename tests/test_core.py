"""
jojo Code - Core 模块单元测试
"""


class TestConfig:
    """测试配置管理"""

    def test_default_config(self):
        """测试默认配置"""
        from jojo_code.core.config import get_settings

        settings = get_settings()
        assert settings.model is not None
        assert settings.max_iterations > 0


class TestSettings:
    """测试设置类"""

    def test_settings_defaults(self):
        """测试默认设置"""

        from jojo_code.core.config import Settings

        settings = Settings()
        # 默认模型可能是 gpt-4o-mini 或从环境变量读取
        assert settings.model is not None
        assert settings.max_iterations == 50


class TestGetSettings:
    """测试获取设置"""

    def test_get_settings_singleton(self):
        """测试单例模式"""
        from jojo_code.core.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


# 兼容性测试
class TestCompatibility:
    """兼容性测试"""

    def test_config_imports(self):
        """测试配置导入"""
        from jojo_code.core.config import Config, Settings

        assert Config is not None
        assert Settings is not None

    def test_llm_imports(self):
        """测试 LLM 导入"""
        from jojo_code.core.llm import (
            get_llm,
        )

        assert get_llm is not None
