"""配置管理"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # LLM 配置
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    model: str = "gpt-4o-mini"

    # Agent 配置
    max_iterations: int = 50
    max_tokens: int = 100000

    # 存储配置
    storage_path: Path = Path.home() / ".nano-code"

    class Config:
        env_prefix = "NANO_CODE_"
        env_file = ".env"


# 全局配置实例
_settings: Settings | None = None


def get_settings() -> Settings:
    """获取配置实例（单例）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
