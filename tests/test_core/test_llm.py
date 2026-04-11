"""LLM 客户端测试"""

import os
from unittest.mock import MagicMock, patch

from nano_code.core.config import Settings
from nano_code.core.llm import DEFAULT_MODEL, get_llm


def create_mock_settings(**kwargs) -> Settings:
    """创建测试用的 Settings mock"""
    defaults = {
        "model": "gpt-4o-mini",
        "openai_api_key": None,
        "openai_base_url": None,
        "anthropic_api_key": None,
        "max_iterations": 50,
        "max_tokens": 100000,
    }
    defaults.update(kwargs)
    return Settings(**defaults)


class TestGetLLM:
    """获取 LLM 实例测试"""

    def test_default_model(self):
        """应该有默认模型"""
        assert DEFAULT_MODEL == "gpt-4o-mini"

    def test_returns_openai_by_default(self):
        """默认应该返回 OpenAI 客户端"""
        mock_settings = create_mock_settings(openai_api_key="test-key")

        with (
            patch("nano_code.core.llm.get_settings", return_value=mock_settings),
            patch("nano_code.core.llm.os.getenv", return_value=None),
            patch("nano_code.core.llm.ChatOpenAI") as mock_openai,
        ):
            mock_openai.return_value = MagicMock()
            get_llm()

            mock_openai.assert_called_once()
            assert mock_openai.call_args[1]["model"] == DEFAULT_MODEL

    def test_returns_anthropic_when_key_present(self):
        """有 Anthropic API Key 时应该返回 Anthropic 客户端"""
        mock_settings = create_mock_settings(anthropic_api_key="sk-ant-test")

        with (
            patch("nano_code.core.llm.get_settings", return_value=mock_settings),
            patch("nano_code.core.llm.os.getenv", return_value=None),
            patch("nano_code.core.llm.ChatAnthropic") as mock_anthropic,
        ):
            mock_anthropic.return_value = MagicMock()
            get_llm()

            mock_anthropic.assert_called_once()

    def test_anthropic_uses_claude_model(self):
        """Anthropic 应该使用 Claude 模型"""
        mock_settings = create_mock_settings(anthropic_api_key="sk-ant-test")

        with (
            patch("nano_code.core.llm.get_settings", return_value=mock_settings),
            patch("nano_code.core.llm.os.getenv", return_value=None),
            patch("nano_code.core.llm.ChatAnthropic") as mock_anthropic,
        ):
            mock_anthropic.return_value = MagicMock()
            get_llm(model="claude-sonnet-4-20250514")

            assert mock_anthropic.call_args[1]["model"].startswith("claude")

    def test_anthropic_defaults_to_sonnet(self):
        """Anthropic 默认使用 Claude Sonnet"""
        mock_settings = create_mock_settings(anthropic_api_key="sk-ant-test")

        with (
            patch("nano_code.core.llm.get_settings", return_value=mock_settings),
            patch("nano_code.core.llm.os.getenv", return_value=None),
            patch("nano_code.core.llm.ChatAnthropic") as mock_anthropic,
        ):
            mock_anthropic.return_value = MagicMock()
            get_llm(model="gpt-4")  # 非 Claude 模型名

            assert mock_anthropic.call_args[1]["model"] == "claude-sonnet-4-20250514"

    def test_custom_model(self):
        """应该接受自定义模型"""
        mock_settings = create_mock_settings(openai_api_key="test-key")

        with (
            patch("nano_code.core.llm.get_settings", return_value=mock_settings),
            patch("nano_code.core.llm.os.getenv", return_value=None),
            patch("nano_code.core.llm.ChatOpenAI") as mock_openai,
        ):
            mock_openai.return_value = MagicMock()
            get_llm(model="gpt-4")

            assert mock_openai.call_args[1]["model"] == "gpt-4"

    def test_custom_temperature(self):
        """应该接受自定义温度"""
        mock_settings = create_mock_settings(openai_api_key="test-key")

        with (
            patch("nano_code.core.llm.get_settings", return_value=mock_settings),
            patch("nano_code.core.llm.os.getenv", return_value=None),
            patch("nano_code.core.llm.ChatOpenAI") as mock_openai,
        ):
            mock_openai.return_value = MagicMock()
            get_llm(temperature=0.5)

            assert mock_openai.call_args[1]["temperature"] == 0.5

    def test_model_from_env(self):
        """应该从配置读取模型"""
        mock_settings = create_mock_settings(model="gpt-4-turbo", openai_api_key="test-key")

        with (
            patch("nano_code.core.llm.get_settings", return_value=mock_settings),
            patch("nano_code.core.llm.os.getenv", return_value=None),
            patch("nano_code.core.llm.ChatOpenAI") as mock_openai,
        ):
            mock_openai.return_value = MagicMock()
            get_llm()

            assert mock_openai.call_args[1]["model"] == "gpt-4-turbo"

    def test_model_parameter_overrides_env(self):
        """模型参数应该覆盖配置"""
        mock_settings = create_mock_settings(model="gpt-4-turbo", openai_api_key="test-key")

        with (
            patch("nano_code.core.llm.get_settings", return_value=mock_settings),
            patch("nano_code.core.llm.os.getenv", return_value=None),
            patch("nano_code.core.llm.ChatOpenAI") as mock_openai,
        ):
            mock_openai.return_value = MagicMock()
            get_llm(model="gpt-4")

            assert mock_openai.call_args[1]["model"] == "gpt-4"
