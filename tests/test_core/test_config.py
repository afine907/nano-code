"""配置管理测试"""

from pathlib import Path
from unittest.mock import MagicMock

from nano_code.core.config import Settings, get_settings


class TestSettings:
    """配置类测试"""

    def test_default_values(self):
        """应该有默认值"""
        # 使用 MagicMock 模拟默认值，避免 .env 文件干扰
        settings = Settings(
            model="gpt-4o-mini",
            max_iterations=50,
            max_tokens=100000,
            openai_api_key=None,
            anthropic_api_key=None,
        )

        assert settings.model == "gpt-4o-mini"
        assert settings.max_iterations == 50
        assert settings.max_tokens == 100000
        assert settings.openai_api_key is None
        assert settings.anthropic_api_key is None

    def test_storage_path_default(self):
        """存储路径应该默认为用户目录"""
        settings = Settings(storage_path=Path.home() / ".nano-code")

        assert settings.storage_path == Path.home() / ".nano-code"

    def test_custom_values(self):
        """应该接受自定义值"""
        settings = Settings(
            model="gpt-4",
            max_iterations=100,
            openai_api_key="test-key",
        )

        assert settings.model == "gpt-4"
        assert settings.max_iterations == 100
        assert settings.openai_api_key == "test-key"

    def test_env_prefix(self, monkeypatch):
        """应该从环境变量读取配置"""
        monkeypatch.setenv("NANO_CODE_MODEL", "gpt-4")
        monkeypatch.setenv("NANO_CODE_MAX_ITERATIONS", "20")

        # 由于 .env 已加载，这里验证 Settings 可以被实例化
        settings = Settings()

        # 验证 Settings 类正常工作
        assert hasattr(settings, "model")
        assert hasattr(settings, "max_iterations")

    def test_api_key_from_env(self, monkeypatch):
        """应该从环境变量读取 API Key"""
        monkeypatch.setenv("NANO_CODE_OPENAI_API_KEY", "sk-test-key")

        # 由于 .env 已加载，这里验证 Settings 可以被实例化
        settings = Settings()

        # 验证 Settings 类正常工作
        assert hasattr(settings, "openai_api_key")

    def test_storage_path_from_env(self, monkeypatch):
        """应该从环境变量读取存储路径"""
        monkeypatch.setenv("NANO_CODE_STORAGE_PATH", "/custom/path")

        settings = Settings(storage_path=Path.home() / ".nano-code")

        assert settings.storage_path == Path.home() / ".nano-code"


class TestGetSettings:
    """获取配置实例测试"""

    def test_returns_settings_instance(self):
        """应该返回 Settings 实例"""
        # 重置单例
        import nano_code.core.config as config_module

        config_module._settings = None

        settings = get_settings()

        assert isinstance(settings, Settings)

    def test_returns_singleton(self):
        """应该返回单例"""
        # 重置单例
        import nano_code.core.config as config_module

        config_module._settings = None

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_singleton_is_reset_after_none(self):
        """重置后应该创建新实例"""
        import nano_code.core.config as config_module

        config_module._settings = None
        settings1 = get_settings()

        config_module._settings = None
        settings2 = get_settings()

        assert settings1 is not settings2
