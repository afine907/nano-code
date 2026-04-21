"""测试 Result 类型"""

import pytest

from jojo_code.core.exceptions import ConfigError
from jojo_code.core.result import Result


class TestResult:
    """Result 类型测试"""

    def test_ok(self):
        """测试成功结果"""
        result = Result.ok(42)
        assert result.is_ok() is True
        assert result.is_err() is False
        assert result.unwrap() == 42

    def test_err(self):
        """测试失败结果"""
        error = ConfigError("配置错误")
        result = Result.err(error)
        assert result.is_ok() is False
        assert result.is_err() is True
        assert result.unwrap_err() == error

    def test_unwrap_or_ok(self):
        """测试 unwrap_or 成功情况"""
        result = Result.ok("value")
        assert result.unwrap_or("default") == "value"

    def test_unwrap_or_err(self):
        """测试 unwrap_or 失败情况"""
        error = ConfigError("错误")
        result = Result.err(error)
        assert result.unwrap_or("default") == "default"

    def test_unwrap_raises(self):
        """测试 unwrap 失败时抛出异常"""
        error = ConfigError("错误")
        result = Result.err(error)

        with pytest.raises(ConfigError):
            result.unwrap()

    def test_map_ok(self):
        """测试 map 成功情况"""
        result = Result.ok(5)
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_ok()
        assert mapped.unwrap() == 10

    def test_map_err(self):
        """测试 map 失败情况"""
        error = ConfigError("错误")
        result = Result.err(error)
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_err()
        assert mapped.unwrap_err() == error

    def test_and_then_ok(self):
        """测试 and_then 成功情况"""
        result = Result.ok(5)
        chained = result.and_then(lambda x: Result.ok(x * 2))
        assert chained.is_ok()
        assert chained.unwrap() == 10

    def test_and_then_err(self):
        """测试 and_then 失败情况"""
        error = ConfigError("错误")
        result = Result.err(error)
        chained = result.and_then(lambda x: Result.ok(x * 2))
        assert chained.is_err()

    def test_or_else_ok(self):
        """测试 or_else 成功情况"""
        result = Result.ok(5)
        recovered = result.or_else(lambda e: Result.ok(0))
        assert recovered.is_ok()
        assert recovered.unwrap() == 5

    def test_or_else_err(self):
        """测试 or_else 失败情况"""
        error = ConfigError("错误")
        result = Result.err(error)
        recovered = result.or_else(lambda e: Result.ok(0))
        assert recovered.is_ok()
        assert recovered.unwrap() == 0

    def test_repr_ok(self):
        """测试成功结果的 repr"""
        result = Result.ok(42)
        assert "ok" in repr(result).lower()

    def test_repr_err(self):
        """测试失败结果的 repr"""
        error = ConfigError("错误")
        result = Result.err(error)
        assert "err" in repr(result).lower()
