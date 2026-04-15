"""
Nano Code - Core 模块单元测试
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from nano_code.core.config import Config, load_config, validate_config
from nano_code.core.llm import AnthropicClient, LLMClient, OpenAIClient


class TestConfig:
    """测试配置管理"""

    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        assert config.model == "claude-3-5-sonnet-20241022"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096

    def test_custom_config(self):
        """测试自定义配置"""
        config = Config(model="claude-3-opus", temperature=0.5, max_tokens=8192)
        assert config.model == "claude-3-opus"
        assert config.temperature == 0.5
        assert config.max_tokens == 8192

    def test_config_validation(self):
        """测试配置验证"""
        config = Config(model="test-model")
        assert validate_config(config) is True

    def test_invalid_config(self):
        """测试无效配置"""
        config = Config(temperature=2.0)  # 超出范围
        assert validate_config(config) is False

    def test_config_to_dict(self):
        """测试配置序列化"""
        config = Config(model="test")
        data = config.to_dict()
        assert data["model"] == "test"

    def test_config_from_dict(self):
        """测试配置反序列化"""
        data = {"model": "test", "temperature": 0.5}
        config = Config.from_dict(data)
        assert config.model == "test"
        assert config.temperature == 0.5

    def test_env_override(self):
        """测试环境变量覆盖"""
        with patch.dict("os.environ", {"MODEL": "env-model"}):
            config = Config()
            assert config.model == "env-model"


class TestLLMClient:
    """测试 LLM 客户端基类"""

    def test_client_init(self):
        """测试客户端初始化"""
        client = LLMClient(api_key="test-key", base_url="http://test.com")
        assert client.api_key == "test-key"
        assert client.base_url == "http://test.com"

    @pytest.mark.asyncio
    async def test_generate(self):
        """测试生成方法"""
        client = LLMClient(api_key="test")
        with pytest.raises(NotImplementedError):
            await client.generate("test prompt")

    def test_validate_response(self):
        """测试响应验证"""
        client = LLMClient(api_key="test")
        # 有效响应
        assert client.validate_response({"content": "test"}) is True
        # 无效响应
        assert client.validate_response({}) is False


class TestAnthropicClient:
    """测试 Anthropic 客户端"""

    @pytest.mark.asyncio
    async def test_generate(self):
        """测试生成"""
        client = AnthropicClient(api_key="test-key")

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"content": [{"text": "response text"}]})
            mock_session.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await client.generate("test prompt")
            assert result == "response text"

    @pytest.mark.asyncio
    async def test_generate_error(self):
        """测试生成错误"""
        client = AnthropicClient(api_key="invalid")

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value="Unauthorized")
            mock_session.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(Exception):
                await client.generate("test prompt")

    @pytest.mark.asyncio
    async def test_stream_generate(self):
        """测试流式生成"""
        client = AnthropicClient(api_key="test-key")

        results = []
        async for chunk in client.stream_generate("test"):
            results.append(chunk)

        assert len(results) > 0

    def test_build_headers(self):
        """测试构建请求头"""
        client = AnthropicClient(api_key="test-key", version="2023-06-01")
        headers = client._build_headers()
        assert "x-api-key" in headers
        assert "anthropic-version" in headers


class TestOpenAIClient:
    """测试 OpenAI 客户端"""

    @pytest.mark.asyncio
    async def test_generate(self):
        """测试生成"""
        client = OpenAIClient(api_key="test-key")

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"choices": [{"message": {"content": "response"}}]}
            )
            mock_session.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await client.generate("test prompt")
            assert result == "response"

    @pytest.mark.asyncio
    async def test_stream_generate(self):
        """测试流式生成"""
        client = OpenAIClient(api_key="test-key")

        results = []
        async for chunk in client.stream_generate("test"):
            results.append(chunk)

        assert isinstance(results, list)


class TestLLMRetry:
    """测试 LLM 重试机制"""

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """测试失败重试"""
        client = LLMClient(api_key="test")
        client.max_retries = 3

        call_count = 0

        async def failing_generate(prompt):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        client._generate = failing_generate

        result = await client.generate_with_retry("test")
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """测试超出最大重试次数"""
        client = LLMClient(api_key="test")
        client.max_retries = 2

        async def always_fail(prompt):
            raise Exception("Permanent failure")

        client._generate = always_fail

        with pytest.raises(Exception):
            await client.generate_with_retry("test")


class TestLLMCaching:
    """测试 LLM 缓存"""

    def test_cache_hit(self):
        """测试缓存命中"""
        client = LLMClient(api_key="test")
        prompt = "test prompt"

        client.cache[client._get_cache_key(prompt)] = "cached response"

        result = client.get_from_cache(prompt)
        assert result == "cached response"

    def test_cache_miss(self):
        """测试缓存未命中"""
        client = LLMClient(api_key="test")

        result = client.get_from_cache("new prompt")
        assert result is None

    def test_cache_set(self):
        """测试设置缓存"""
        client = LLMClient(api_key="test")
        client.add_to_cache("prompt", "response")

        assert client.get_from_cache("prompt") == "response"

    def test_cache_clear(self):
        """测试清空缓存"""
        client = LLMClient(api_key="test")
        client.add_to_cache("prompt", "response")
        client.clear_cache()

        assert client.get_from_cache("prompt") is None


class TestLLMRateLimit:
    """测试 LLM 速率限制"""

    @pytest.mark.asyncio
    async def test_rate_limit(self):
        """测试速率限制"""
        client = LLMClient(api_key="test")
        client.rate_limit = 2  # 每秒2次
        client.rate_window = 1  # 1秒窗口

        import time

        # 前两次应该通过
        start = time.time()
        await client._check_rate_limit()
        await client._check_rate_limit()

        # 第三次应该被限制
        with pytest.raises(Exception):
            await client._check_rate_limit()


class TestConfigManager:
    """测试配置管理器"""

    def test_load_yaml_config(self):
        """测试加载 YAML 配置"""
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read = Mock(
                return_value="model: test\ntemperature: 0.5"
            )
            config = load_config("test.yaml")
            assert config.model == "test"

    def test_load_json_config(self):
        """测试加载 JSON 配置"""
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read = Mock(
                return_value='{"model": "test"}'
            )
            config = load_config("test.json")
            assert config.model == "test"

    def test_load_env_config(self):
        """测试加载环境变量配置"""
        with patch.dict("os.environ", {"MODEL": "env-model", "TEMPERATURE": "0.3"}):
            config = load_config("test.json")
            assert config.model == "env-model"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
