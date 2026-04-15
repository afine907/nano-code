"""
Nano Code - 验证和模式定义模块
提供数据验证、模式匹配等功能
"""

import json
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class ValidationError(Exception):
    """验证错误"""

    pass


@dataclass
class FieldValidationError:
    """字段验证错误"""

    field: str
    message: str
    code: str


class Validator(ABC):
    """验证器基类"""

    @abstractmethod
    def validate(self, value: Any) -> bool:
        pass

    @abstractmethod
    def get_error_message(self, field: str) -> str:
        pass


class RequiredValidator(Validator):
    """必填验证"""

    def validate(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        return True

    def get_error_message(self, field: str) -> str:
        return f"{field} 是必填字段"


class StringValidator(Validator):
    """字符串验证"""

    def __init__(
        self,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        allowed_values: list[str] | None = None,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.allowed_values = allowed_values

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False

        if self.min_length and len(value) < self.min_length:
            return False

        if self.max_length and len(value) > self.max_length:
            return False

        if self.pattern and not self.pattern.match(value):
            return False

        if self.allowed_values and value not in self.allowed_values:
            return False

        return True

    def get_error_message(self, field: str) -> str:
        if self.min_length:
            return f"{field} 长度不能少于 {self.min_length} 个字符"
        if self.max_length:
            return f"{field} 长度不能超过 {self.max_length} 个字符"
        if self.pattern:
            return f"{field} 格式不正确"
        if self.allowed_values:
            return f"{field} 必须是允许的值之一"
        return f"{field} 验证失败"


class NumberValidator(Validator):
    """数字验证"""

    def __init__(
        self,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        integer_only: bool = False,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only

    def validate(self, value: Any) -> bool:
        if self.integer_only and not isinstance(value, int):
            return False

        if not isinstance(value, (int, float)):
            return False

        if self.min_value is not None and value < self.min_value:
            return False

        if self.max_value is not None and value > self.max_value:
            return False

        return True

    def get_error_message(self, field: str) -> str:
        if self.min_value is not None:
            return f"{field} 不能小于 {self.min_value}"
        if self.max_value is not None:
            return f"{field} 不能大于 {self.max_value}"
        return f"{field} 必须是数字"


class EmailValidator(Validator):
    """邮箱验证"""

    PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.match(value))

    def get_error_message(self, field: str) -> str:
        return f"{field} 必须是有效的邮箱地址"


class URLValidator(Validator):
    """URL 验证"""

    PATTERN = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self.PATTERN.match(value))

    def get_error_message(self, field: str) -> str:
        return f"{field} 必须是有效的 URL"


class DateValidator(Validator):
    """日期验证"""

    def __init__(self, format: str = "%Y-%m-%d"):
        self.format = format

    def validate(self, value: Any) -> bool:
        if isinstance(value, datetime):
            return True

        if isinstance(value, str):
            try:
                datetime.strptime(value, self.format)
                return True
            except ValueError:
                return False

        return False

    def get_error_message(self, field: str) -> str:
        return f"{field} 必须是有效的日期格式 ({self.format})"


class JSONValidator(Validator):
    """JSON 验证"""

    def validate(self, value: Any) -> bool:
        if isinstance(value, (dict, list)):
            return True

        if isinstance(value, str):
            try:
                json.loads(value)
                return True
            except json.JSONDecodeError:
                return False

        return False

    def get_error_message(self, field: str) -> str:
        return f"{field} 必须是有效的 JSON"


class EnumValidator(Validator):
    """枚举验证"""

    def __init__(self, enum_class: type[Enum]):
        self.enum_class = enum_class
        self.allowed_values = [e.value for e in enum_class]

    def validate(self, value: Any) -> bool:
        return value in self.allowed_values

    def get_error_message(self, field: str) -> str:
        return f"{field} 必须是以下值之一: {', '.join(map(str, self.allowed_values))}"


class CustomValidator(Validator):
    """自定义验证"""

    def __init__(self, validator: Callable[[Any], bool], error_message: str):
        self.validator = validator
        self.error_message = error_message

    def validate(self, value: Any) -> bool:
        return self.validator(value)

    def get_error_message(self, field: str) -> str:
        return self.error_message


class SchemaValidator:
    """模式验证器"""

    def __init__(self, schema: dict[str, Validator]):
        self.schema = schema

    def validate(self, data: dict) -> list[FieldValidationError]:
        errors = []

        for field, validator in self.schema.items():
            value = data.get(field)

            if not validator.validate(value):
                errors.append(
                    FieldValidationError(
                        field=field, message=validator.get_error_message(field), code="invalid"
                    )
                )

        return errors

    def is_valid(self, data: dict) -> bool:
        return len(self.validate(data)) == 0


# 数据清洗
class DataCleaner:
    """数据清洗器"""

    @staticmethod
    def clean_string(value: str) -> str:
        """清洗字符串"""
        if not value:
            return ""

        # 去除首尾空白
        value = value.strip()

        # 去除多余空白
        value = re.sub(r"\s+", " ", value)

        return value

    @staticmethod
    def clean_email(email: str) -> str:
        """清洗邮箱"""
        email = email.lower().strip()
        return email

    @staticmethod
    def clean_phone(phone: str) -> str:
        """清洗手机号"""
        # 去除非数字字符
        phone = re.sub(r"\D", "", phone)

        # 添加国际区号（中国）
        if len(phone) == 11:
            phone = "+86" + phone

        return phone

    @staticmethod
    def clean_url(url: str) -> str:
        """清洗 URL"""
        url = url.strip()

        # 添加协议
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        return url

    @staticmethod
    def normalize_json(value: str) -> Any:
        """标准化 JSON"""
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value


# 数据转换
class DataConverter:
    """数据转换器"""

    @staticmethod
    def to_string(value: Any) -> str:
        """转为字符串"""
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def to_int(value: Any, default: int = 0) -> int:
        """转为整数"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def to_float(value: Any, default: float = 0.0) -> float:
        """转为浮点数"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def to_bool(value: Any) -> bool:
        """转为布尔值"""
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")

        return bool(value)

    @staticmethod
    def to_datetime(value: Any, format: str = "%Y-%m-%d %H:%M:%S") -> datetime | None:
        """转为日期时间"""
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                return datetime.strptime(value, format)
            except ValueError:
                return None

        return None

    @staticmethod
    def to_json(value: Any) -> str:
        """转为 JSON"""
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, indent=2)


# 数据规范化
class DataNormalizer:
    """数据规范化器"""

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """规范化空白字符"""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def normalize_line_endings(text: str) -> str:
        """规范化行结束符"""
        return text.replace("\r\n", "\n").replace("\r", "\n")

    @staticmethod
    def normalize_case(text: str, mode: str = "lower") -> str:
        """规范化大小写"""
        if mode == "lower":
            return text.lower()
        elif mode == "upper":
            return text.upper()
        elif mode == "title":
            return text.title()
        return text

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """规范化 Unicode"""
        import unicodedata

        return unicodedata.normalize("NFKC", text)

    @staticmethod
    def remove_special_chars(text: str, allowed: str = "") -> str:
        """移除特殊字符"""
        pattern = f"[^a-zA-Z0-9{re.escape(allowed)}]"
        return re.sub(pattern, "", text)


# 密码验证
class PasswordValidator:
    """密码验证器"""

    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
    ):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special

    def validate(self, password: str) -> tuple[bool, list[str]]:
        """验证密码，返回 (是否有效, 错误列表)"""
        errors = []

        if len(password) < self.min_length:
            errors.append(f"密码长度至少 {self.min_length} 个字符")

        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("密码必须包含大写字母")

        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("密码必须包含小写字母")

        if self.require_digit and not re.search(r"\d", password):
            errors.append("密码必须包含数字")

        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含特殊字符")

        return len(errors) == 0, errors

    def get_strength(self, password: str) -> str:
        """获取密码强度"""
        score = 0

        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if re.search(r"[a-z]", password):
            score += 1
        if re.search(r"[A-Z]", password):
            score += 1
        if re.search(r"\d", password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1

        if score <= 2:
            return "弱"
        elif score <= 4:
            return "中等"
        else:
            return "强"


# 敏感信息检测
class SensitiveDataDetector:
    """敏感信息检测器"""

    PATTERNS = {
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "phone": re.compile(r"\b1[3-9]\d{9}\b"),
        "id_card": re.compile(
            r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b"
        ),
        "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "url": re.compile(r"https?://[^\s]+"),
        "api_key": re.compile(
            r'\b(?:api[_-]?key|apikey)[=:]\s*["\']?[\w-]{20,}["\']?', re.IGNORECASE
        ),
        "password": re.compile(
            r'\b(?:password|passwd|pwd)[=:]\s*["\']?[^\s"\']+["\']?', re.IGNORECASE
        ),
    }

    @classmethod
    def detect(cls, text: str) -> dict[str, list[str]]:
        """检测敏感信息"""
        results = {}

        for name, pattern in cls.PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                results[name] = matches

        return results

    @classmethod
    def mask(cls, text: str) -> str:
        """脱敏处理"""
        # 邮箱
        text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "***@***.***", text)

        # 手机号
        text = re.sub(r"\b1[3-9]\d{9}\b", "1**********", text)

        # 身份证号
        text = re.sub(
            r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
            "**************1234",
            text,
        )

        # 信用卡号
        text = re.sub(r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "**** **** **** ****", text)

        return text
