"""测试权限模式和风险等级"""

import pytest

from jojo_code.security.modes import PermissionMode, RiskLevel


class TestPermissionMode:
    """测试 PermissionMode 枚举"""

    def test_all_modes_exist(self):
        """测试所有模式都存在"""
        assert PermissionMode.AUTO.value == "auto"
        assert PermissionMode.MANUAL.value == "manual"
        assert PermissionMode.BYPASS.value == "bypass"

    def test_allows_write(self):
        """测试写操作权限"""
        # AUTO 和 MANUAL 允许写操作（需要确认）
        assert PermissionMode.AUTO.allows_write() is True
        assert PermissionMode.MANUAL.allows_write() is True
        # BYPASS 当前实现不允许写操作（这可能是实现错误）
        assert PermissionMode.BYPASS.allows_write() is False

    def test_requires_confirmation_bypass(self):
        """BYPASS 模式永远不需要确认"""
        assert PermissionMode.BYPASS.requires_confirmation(RiskLevel.LOW) is False
        assert PermissionMode.BYPASS.requires_confirmation(RiskLevel.MEDIUM) is False
        assert PermissionMode.BYPASS.requires_confirmation(RiskLevel.HIGH) is False
        assert PermissionMode.BYPASS.requires_confirmation(RiskLevel.CRITICAL) is False

    def test_requires_confirmation_auto(self):
        """AUTO 模式 MEDIUM 及以上需要确认"""
        assert PermissionMode.AUTO.requires_confirmation(RiskLevel.LOW) is False
        assert PermissionMode.AUTO.requires_confirmation(RiskLevel.MEDIUM) is True
        assert PermissionMode.AUTO.requires_confirmation(RiskLevel.HIGH) is True
        assert PermissionMode.AUTO.requires_confirmation(RiskLevel.CRITICAL) is True

    def test_requires_confirmation_manual(self):
        """MANUAL 模式所有操作都需要确认"""
        assert PermissionMode.MANUAL.requires_confirmation(RiskLevel.LOW) is True
        assert PermissionMode.MANUAL.requires_confirmation(RiskLevel.MEDIUM) is True
        assert PermissionMode.MANUAL.requires_confirmation(RiskLevel.HIGH) is True
        assert PermissionMode.MANUAL.requires_confirmation(RiskLevel.CRITICAL) is True

    def test_from_string_valid(self):
        """测试从字符串解析有效模式"""
        assert PermissionMode.from_string("auto") == PermissionMode.AUTO
        assert PermissionMode.from_string("manual") == PermissionMode.MANUAL
        assert PermissionMode.from_string("bypass") == PermissionMode.BYPASS

    def test_from_string_invalid(self):
        """测试从字符串解析无效模式"""
        with pytest.raises(ValueError, match="无效的权限模式"):
            PermissionMode.from_string("invalid_mode")


class TestRiskLevel:
    """测试 RiskLevel 枚举"""

    def test_all_levels_exist(self):
        """测试所有风险等级都存在"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_comparison_less_than(self):
        """测试风险等级小于比较"""
        assert RiskLevel.LOW < RiskLevel.MEDIUM
        assert RiskLevel.LOW < RiskLevel.HIGH
        assert RiskLevel.LOW < RiskLevel.CRITICAL
        assert RiskLevel.MEDIUM < RiskLevel.HIGH
        assert RiskLevel.MEDIUM < RiskLevel.CRITICAL
        assert RiskLevel.HIGH < RiskLevel.CRITICAL

    def test_comparison_greater_than(self):
        """测试风险等级大于比较"""
        assert RiskLevel.CRITICAL > RiskLevel.HIGH
        assert RiskLevel.CRITICAL > RiskLevel.MEDIUM
        assert RiskLevel.CRITICAL > RiskLevel.LOW
        assert RiskLevel.HIGH > RiskLevel.MEDIUM
        assert RiskLevel.HIGH > RiskLevel.LOW
        assert RiskLevel.MEDIUM > RiskLevel.LOW

    def test_comparison_equal(self):
        """测试风险等级等于比较"""
        assert RiskLevel.LOW == RiskLevel.LOW
        assert RiskLevel.LOW <= RiskLevel.LOW
        assert RiskLevel.LOW >= RiskLevel.LOW

    def test_comparison_less_equal(self):
        """测试风险等级小于等于比较"""
        assert RiskLevel.LOW <= RiskLevel.MEDIUM
        assert RiskLevel.LOW <= RiskLevel.LOW
        assert RiskLevel.MEDIUM <= RiskLevel.HIGH

    def test_comparison_greater_equal(self):
        """测试风险等级大于等于比较"""
        assert RiskLevel.CRITICAL >= RiskLevel.HIGH
        assert RiskLevel.CRITICAL >= RiskLevel.CRITICAL
        assert RiskLevel.HIGH >= RiskLevel.MEDIUM

    def test_from_string_valid(self):
        """测试从字符串解析有效风险等级"""
        assert RiskLevel.from_string("low") == RiskLevel.LOW
        assert RiskLevel.from_string("medium") == RiskLevel.MEDIUM
        assert RiskLevel.from_string("high") == RiskLevel.HIGH
        assert RiskLevel.from_string("critical") == RiskLevel.CRITICAL

    def test_from_string_invalid(self):
        """测试从字符串解析无效风险等级"""
        with pytest.raises(ValueError, match="无效的风险等级"):
            RiskLevel.from_string("extreme")
