"""任务 ID 生成器"""

import secrets
import string

from jojo_code.task.types import TaskType

# 任务 ID 前缀映射
TASK_PREFIXES: dict[TaskType, str] = {
    TaskType.BASH: "b",
    TaskType.AGENT: "a",
    TaskType.TEAMMATE: "t",
    TaskType.WORKFLOW: "w",
    TaskType.MCP: "m",
    TaskType.DREAM: "d",
}

# 默认前缀
DEFAULT_PREFIX = "x"

# ID 随机部分长度
RANDOM_LENGTH = 8


def generate_task_id(task_type: TaskType) -> str:
    """生成任务 ID

    格式: {prefix}{random}
    - prefix: 1位字母，对应任务类型
    - random: 8位随机字符 (字母+数字)

    Args:
        task_type: 任务类型

    Returns:
        任务 ID (如 "babc1234")
    """
    prefix = TASK_PREFIXES.get(task_type, DEFAULT_PREFIX)
    random_part = "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(RANDOM_LENGTH)
    )
    return f"{prefix}{random_part}"


def parse_task_id(task_id: str) -> TaskType | None:
    """解析任务 ID 获取类型

    Args:
        task_id: 任务 ID

    Returns:
        任务类型，如果无法解析则返回 None
    """
    if not task_id:
        return None

    prefix = task_id[0].lower()
    for task_type, p in TASK_PREFIXES.items():
        if p == prefix:
            return task_type

    return None


def validate_task_id(task_id: str) -> bool:
    """验证任务 ID 格式

    Args:
        task_id: 任务 ID

    Returns:
        是否有效
    """
    if not task_id or len(task_id) != RANDOM_LENGTH + 1:
        return False

    # 第一位必须是有效前缀
    if task_id[0] not in TASK_PREFIXES.values():
        return False

    # 其余位必须是字母或数字
    return all(c in string.ascii_lowercase + string.digits for c in task_id[1:])


__all__ = [
    "generate_task_id",
    "parse_task_id",
    "validate_task_id",
    "TASK_PREFIXES",
]
