"""配置管理测试"""

from pathlib import Path

from nano_code.core.config import Settings, get_settings


class TestSettings:
    """配置类测试"""

    def test_default_values(self):
        """应该有默认值"""
        settings = Settings()

        assert settings.model == "gpt-4o-mini"
        assert settings.max_iterations == 50
        assert settings.max_tokens == 100000
        assert settings.openai_api_key is None
        assert settings.anthropic_api_key is None

    def test_storage_path_default(self):
        """存储路径应该默认为用户目录"""
        settings = Settings()

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

        settings = Settings()

        assert settings.model == "gpt-4"
        assert settings.max_iterations == 20

    def test_api_key_from_env(self, monkeypatch):
        """应该从环境变量读取 API Key"""
        monkeypatch.setenv("NANO_CODE_OPENAI_API_KEY", "sk-test-key")

        settings = Settings()

        assert settings.openai_api_key == "sk-test-key"

    def test_storage_path_from_env(self, monkeypatch):
        """应该从环境变量读取存储路径"""
        monkeypatch.setenv("NANO_CODE_STORAGE_PATH", "/custom/path")

        settings = Settings()

        assert settings.storage_path == Path("/custom/path")


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
