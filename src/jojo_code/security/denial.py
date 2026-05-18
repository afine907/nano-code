"""拒绝追踪 - 防止重复请求被拒绝的工具"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DenialRecord:
    """拒绝记录"""

    tool_name: str
    args: dict[str, Any]
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    count: int = 1


class DenialTracker:
    """拒绝追踪器

    跟踪被拒绝的工具调用，防止重复请求。
    支持阈值检测，当同一工具/参数被多次拒绝后，
    可以自动切换到提示用户模式。
    """

    def __init__(
        self,
        # 同一工具/参数组合被拒绝多少次后触发阈值
        threshold: int = 3,
        # 阈值窗口期 (秒)
        window_seconds: int = 300,
        # 记录过期时间 (秒)
        expiry_seconds: int = 3600,
    ):
        self.threshold = threshold
        self.window_seconds = window_seconds
        self.expiry_seconds = expiry_seconds

        # 存储拒绝记录: key = (tool_name, args_hash), value = DenialRecord
        self._denials: dict[str, DenialRecord] = {}

        # 用于快速查找的索引
        self._tool_index: dict[str, set[str]] = defaultdict(set)

    def _make_key(self, tool_name: str, args: dict[str, Any]) -> str:
        """生成唯一键

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            唯一键
        """
        import hashlib
        import json

        # 将 args 转换为可哈希的形式
        args_str = json.dumps(args, sort_keys=True)
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
        return f"{tool_name}:{args_hash}"

    def record(self, tool_name: str, args: dict[str, Any], reason: str) -> None:
        """记录一次拒绝

        Args:
            tool_name: 工具名称
            args: 工具参数
            reason: 拒绝原因
        """
        key = self._make_key(tool_name, args)
        now = datetime.now()

        if key in self._denials:
            # 已存在，增加计数
            record = self._denials[key]
            record.count += 1
            record.timestamp = now
            record.reason = reason
        else:
            # 新记录
            self._denials[key] = DenialRecord(
                tool_name=tool_name,
                args=args,
                reason=reason,
                timestamp=now,
                count=1,
            )
            self._tool_index[tool_name].add(key)

    def is_threshold_exceeded(self, tool_name: str, args: dict[str, Any]) -> bool:
        """检查是否超过阈值

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            是否超过阈值
        """
        key = self._make_key(tool_name, args)

        if key not in self._denials:
            return False

        record = self._denials[key]
        now = datetime.now()

        # 检查是否在窗口期内
        if (now - record.timestamp).total_seconds() > self.window_seconds:
            # 窗口期已过，重置计数
            record.count = 1
            return False

        return record.count >= self.threshold

    def get_denial_count(self, tool_name: str, args: dict[str, Any]) -> int:
        """获取拒绝次数

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            拒绝次数
        """
        key = self._make_key(tool_name, args)
        if key in self._denials:
            return self._denials[key].count
        return 0

    def get_tool_denials(self, tool_name: str) -> list[DenialRecord]:
        """获取某个工具的所有拒绝记录

        Args:
            tool_name: 工具名称

        Returns:
            拒绝记录列表
        """
        records = []
        if tool_name in self._tool_index:
            for key in self._tool_index[tool_name]:
                if key in self._denials:
                    records.append(self._denials[key])
        return records

    def clear(self, tool_name: str | None = None) -> None:
        """清除拒绝记录

        Args:
            tool_name: 工具名称，如果为 None 则清除所有
        """
        if tool_name is None:
            self._denials.clear()
            self._tool_index.clear()
        elif tool_name in self._tool_index:
            for key in self._tool_index[tool_name]:
                if key in self._denials:
                    del self._denials[key]
            self._tool_index.pop(tool_name, None)

    def cleanup_expired(self) -> int:
        """清理过期记录

        Returns:
            清理的记录数
        """
        now = datetime.now()
        expired_keys = []

        for key, record in self._denials.items():
            if (now - record.timestamp).total_seconds() > self.expiry_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            record = self._denials.pop(key)
            self._tool_index[record.tool_name].discard(key)

        # 清理空的索引
        empty_tools = [t for t, keys in self._tool_index.items() if not keys]
        for tool in empty_tools:
            self._tool_index.pop(tool, None)

        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_denials": len(self._denials),
            "tools_tracked": len(self._tool_index),
            "threshold": self.threshold,
            "window_seconds": self.window_seconds,
        }


class AdaptivePermissionMixin:
    """自适应权限混合类

    根据拒绝追踪自动调整权限行为。
    当某个操作被连续拒绝时，自动切换到需要确认的模式。
    """

    def __init__(self):
        self._denial_tracker = DenialTracker()
        self._auto_confirm_threshold = 3

    @property
    def denial_tracker(self) -> DenialTracker:
        return self._denial_tracker

    def check_with_denial_tracking(
        self,
        tool_name: str,
        args: dict[str, Any],
        check_fn: callable,
    ) -> tuple[bool, str]:
        """带拒绝追踪的权限检查

        Args:
            tool_name: 工具名称
            args: 工具参数
            check_fn: 实际的权限检查函数

        Returns:
            (是否允许, 原因)
        """
        # 先进行实际的权限检查
        result = check_fn(tool_name, args)

        if result.denied:
            # 记录拒绝
            self._denial_tracker.record(tool_name, args, result.reason or "权限被拒绝")

            # 检查是否超过阈值
            if self._denial_tracker.is_threshold_exceeded(tool_name, args):
                threshold = self._denial_tracker.threshold
            msg = f"操作被连续拒绝 {threshold} 次，请检查参数或权限配置"
            return False, msg

            return False, result.reason or "权限被拒绝"

        return True, ""


__all__ = [
    "DenialRecord",
    "DenialTracker",
    "AdaptivePermissionMixin",
]
