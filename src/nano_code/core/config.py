"""配置管理"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM 配置（直接读取环境变量名，无前缀）
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    anthropic_api_key: str | None = None
    model: str = "gpt-4o-mini"

    # Agent 配置
    max_iterations: int = 50
    max_tokens: int = 100000

    # 存储配置
    storage_path: Path = Path.home() / ".nano-code"


# 全局配置实例
_settings: Settings | None = None

# 为了向后兼容，添加别名
Config = Settings


def load_config() -> Settings:
    """加载配置（兼容旧 API）"""
    return get_settings()


def validate_config(config: Settings) -> bool:
    """验证配置（兼容旧 API）"""
    return True  # Pydantic 会自动验证


def get_settings() -> Settings:
    """获取配置实例（单例）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
