# 工具权限限制设计方案

## 1. 设计目标

| 目标 | 说明 |
|------|------|
| 路径隔离 | 限制文件操作只能在指定目录内 |
| 命令过滤 | 阻止危险命令，允许安全命令 |
| 用户确认 | 危险操作需用户批准 |
| 可配置 | 通过配置文件灵活控制 |
| 审计追踪 | 记录所有工具调用 |

## 2. 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent 请求                            │
│                    "删除 src/ 目录"                          │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   PermissionManager                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PathGuard   │  │ CmdGuard    │  │ ConfirmGuard│         │
│  │ 路径检查    │  │ 命令过滤    │  │ 用户确认    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
     [ALLOW]         [CONFIRM]        [DENY]
      执行            等待确认          拒绝
```

## 3. 权限级别定义

```python
class PermissionLevel(Enum):
    """权限级别"""
    ALLOW = "allow"           # 自动允许，无需确认
    CONFIRM = "confirm"       # 需要用户确认
    DENY = "deny"             # 禁止执行
```

## 4. 配置结构设计

```yaml
# .nano-code/permissions.yaml

# 工作空间根目录（文件操作限制在此目录内）
workspace:
  root: "."                   # 当前目录，或绝对路径
  allow_outside: false        # 是否允许访问 workspace 外的文件

# 文件权限规则
file:
  # 默认策略
  default: allow              # allow | confirm | deny
  
  # 路径白名单（相对于 workspace.root）
  allowed_paths:
    - "src/**"
    - "tests/**"
    - "docs/**"
    - "*.md"
    - "*.txt"
    - "pyproject.toml"
  
  # 路径黑名单
  denied_paths:
    - ".env"
    - ".git/**"
    - "__pycache__/**"
    - "*.pem"
    - "*.key"
    - "secrets/**"
  
  # 写入需要确认的路径模式
  confirm_on_write:
    - "src/core/**"           # 核心代码修改需确认
    - "pyproject.toml"        # 项目配置修改需确认

# Shell 命令权限
shell:
  # 是否启用 shell 工具
  enabled: true
  
  # 默认策略
  default: confirm            # 默认需要确认
  
  # 允许的命令（自动执行）
  allowed_commands:
    - "ls"
    - "cat"
    - "head"
    - "tail"
    - "grep"
    - "find"
    - "git status"
    - "git log"
    - "git diff"
    - "pytest"
    - "ruff check"
    - "mypy"
  
  # 禁止的命令（无论参数如何）
  denied_commands:
    - "rm -rf /"
    - "rm -rf ~"
    - "sudo"
    - "chmod 777"
    - "curl * | *sh"          # 支持通配符
    - "wget * | *sh"
    - "mkfs"
    - "dd if="
  
  # 命令参数限制
  max_timeout: 300            # 最大超时时间（秒）
  allow_network: false        # 是否允许网络命令

# 全局设置
global:
  # 每个会话最大工具调用次数
  max_tool_calls: 100
  
  # 自动确认阈值（会话内连续允许 N 次后自动信任）
  auto_trust_after: 10
  
  # 审计日志
  audit_log: true
  audit_log_path: ".nano-code/audit.log"
```

## 5. 核心类设计

### 5.1 权限检查结果

```python
# src/nano_code/security/permission.py

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PermissionLevel(Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"


@dataclass
class PermissionResult:
    """权限检查结果"""
    level: PermissionLevel
    tool_name: str
    args: dict[str, Any]
    reason: str | None = None
    
    @property
    def allowed(self) -> bool:
        return self.level == PermissionLevel.ALLOW
    
    @property
    def needs_confirm(self) -> bool:
        return self.level == PermissionLevel.CONFIRM
    
    @property
    def denied(self) -> bool:
        return self.level == PermissionLevel.DENY
```

### 5.2 权限守卫接口

```python
# src/nano_code/security/guards.py

from abc import ABC, abstractmethod
from typing import Any


class BaseGuard(ABC):
    """权限守卫基类"""
    
    @abstractmethod
    def check(self, tool_name: str, args: dict[str, Any]) -> PermissionResult:
        """检查工具调用权限"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """守卫名称"""
        pass
```

### 5.3 路径守卫

```python
# src/nano_code/security/path_guard.py

import fnmatch
from pathlib import Path
from typing import Any

from nano_code.security.guards import BaseGuard
from nano_code.security.permission import PermissionLevel, PermissionResult


class PathGuard(BaseGuard):
    """路径权限守卫"""
    
    def __init__(
        self,
        workspace_root: Path,
        allowed_patterns: list[str] | None = None,
        denied_patterns: list[str] | None = None,
        confirm_patterns: list[str] | None = None,
        allow_outside: bool = False,
    ):
        self.workspace_root = workspace_root.resolve()
        self.allowed_patterns = allowed_patterns or ["*"]
        self.denied_patterns = denied_patterns or []
        self.confirm_patterns = confirm_patterns or []
        self.allow_outside = allow_outside
    
    @property
    def name(self) -> str:
        return "path_guard"
    
    def check(self, tool_name: str, args: dict[str, Any]) -> PermissionResult:
        # 只检查文件相关工具
        if tool_name not in ("read_file", "write_file", "edit_file", "list_directory"):
            return PermissionResult(PermissionLevel.ALLOW, tool_name, args)
        
        path = self._extract_path(args)
        if path is None:
            return PermissionResult(PermissionLevel.ALLOW, tool_name, args)
        
        file_path = Path(path).resolve()
        
        # 1. 检查是否在 workspace 内
        if not self.allow_outside:
            try:
                file_path.relative_to(self.workspace_root)
            except ValueError:
                return PermissionResult(
                    PermissionLevel.DENY,
                    tool_name,
                    args,
                    reason=f"路径 '{path}' 在工作空间外"
                )
        
        # 2. 检查黑名单
        relative_path = self._get_relative_path(file_path)
        for pattern in self.denied_patterns:
            if self._match_pattern(relative_path, pattern):
                return PermissionResult(
                    PermissionLevel.DENY,
                    tool_name,
                    args,
                    reason=f"路径 '{path}' 匹配禁止模式 '{pattern}'"
                )
        
        # 3. 检查白名单
        in_whitelist = any(
            self._match_pattern(relative_path, p)
            for p in self.allowed_patterns
        )
        if not in_whitelist:
            return PermissionResult(
                PermissionLevel.DENY,
                tool_name,
                args,
                reason=f"路径 '{path}' 不在允许列表中"
            )
        
        # 4. 检查是否需要确认
        if tool_name in ("write_file", "edit_file"):
            for pattern in self.confirm_patterns:
                if self._match_pattern(relative_path, pattern):
                    return PermissionResult(
                        PermissionLevel.CONFIRM,
                        tool_name,
                        args,
                        reason=f"修改文件 '{path}' 需要确认"
                    )
        
        return PermissionResult(PermissionLevel.ALLOW, tool_name, args)
    
    def _extract_path(self, args: dict[str, Any]) -> str | None:
        """从参数中提取路径"""
        return args.get("path")
    
    def _get_relative_path(self, file_path: Path) -> str:
        """获取相对路径字符串"""
        try:
            return str(file_path.relative_to(self.workspace_root))
        except ValueError:
            return str(file_path)
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """匹配路径模式"""
        return fnmatch.fnmatch(path, pattern)
```

### 5.4 命令守卫

```python
# src/nano_code/security/command_guard.py

import re
from typing import Any

from nano_code.security.guards import BaseGuard
from nano_code.security.permission import PermissionLevel, PermissionResult


class CommandGuard(BaseGuard):
    """命令权限守卫"""
    
    def __init__(
        self,
        enabled: bool = True,
        allowed_commands: list[str] | None = None,
        denied_commands: list[str] | None = None,
        default: PermissionLevel = PermissionLevel.CONFIRM,
        max_timeout: int = 300,
        allow_network: bool = False,
    ):
        self.enabled = enabled
        self.allowed_commands = allowed_commands or []
        self.denied_commands = denied_commands or []
        self.default = default
        self.max_timeout = max_timeout
        self.allow_network = allow_network
    
    @property
    def name(self) -> str:
        return "command_guard"
    
    def check(self, tool_name: str, args: dict[str, Any]) -> PermissionResult:
        if tool_name != "run_command":
            return PermissionResult(PermissionLevel.ALLOW, tool_name, args)
        
        if not self.enabled:
            return PermissionResult(
                PermissionLevel.DENY,
                tool_name,
                args,
                reason="Shell 命令已被禁用"
            )
        
        command = args.get("command", "")
        timeout = args.get("timeout", 30)
        
        # 1. 检查超时限制
        if timeout > self.max_timeout:
            return PermissionResult(
                PermissionLevel.DENY,
                tool_name,
                args,
                reason=f"超时时间 {timeout}s 超过最大限制 {self.max_timeout}s"
            )
        
        # 2. 检查黑名单命令
        for denied in self.denied_commands:
            if self._match_command(command, denied):
                return PermissionResult(
                    PermissionLevel.DENY,
                    tool_name,
                    args,
                    reason=f"命令匹配禁止模式: {denied}"
                )
        
        # 3. 检查网络命令
        if not self.allow_network and self._is_network_command(command):
            return PermissionResult(
                PermissionLevel.DENY,
                tool_name,
                args,
                reason="网络命令已被禁用"
            )
        
        # 4. 检查白名单命令
        for allowed in self.allowed_commands:
            if self._match_command(command, allowed):
                return PermissionResult(PermissionLevel.ALLOW, tool_name, args)
        
        # 5. 返回默认策略
        return PermissionResult(
            self.default,
            tool_name,
            args,
            reason=f"命令不在白名单中: {command}"
        )
    
    def _match_command(self, command: str, pattern: str) -> bool:
        """匹配命令模式"""
        # 支持通配符匹配
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(f"^{regex_pattern}", command.strip(), re.IGNORECASE))
    
    def _is_network_command(self, command: str) -> bool:
        """检查是否为网络命令"""
        network_tools = ["curl", "wget", "nc", "netcat", "ssh", "scp", "rsync"]
        return any(command.strip().startswith(tool) for tool in network_tools)
```

### 5.5 权限管理器

```python
# src/nano_code/security/manager.py

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from nano_code.security.guards import BaseGuard
from nano_code.security.path_guard import PathGuard
from nano_code.security.command_guard import CommandGuard
from nano_code.security.permission import PermissionLevel, PermissionResult


@dataclass
class PermissionConfig:
    """权限配置"""
    workspace_root: Path = Path(".")
    allow_outside: bool = False
    allowed_paths: list[str] = field(default_factory=lambda: ["*"])
    denied_paths: list[str] = field(default_factory=list)
    confirm_on_write: list[str] = field(default_factory=list)
    shell_enabled: bool = True
    allowed_commands: list[str] = field(default_factory=list)
    denied_commands: list[str] = field(default_factory=lambda: ["rm -rf /", "sudo"])
    shell_default: PermissionLevel = PermissionLevel.CONFIRM
    max_timeout: int = 300
    allow_network: bool = False
    max_tool_calls: int = 100
    audit_log: bool = True
    audit_log_path: Path = Path(".nano-code/audit.log")
    
    @classmethod
    def from_yaml(cls, path: Path) -> "PermissionConfig":
        """从 YAML 文件加载配置"""
        if not path.exists():
            return cls()
        
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        return cls(
            workspace_root=Path(data.get("workspace", {}).get("root", ".")),
            allow_outside=data.get("workspace", {}).get("allow_outside", False),
            allowed_paths=data.get("file", {}).get("allowed_paths", ["*"]),
            denied_paths=data.get("file", {}).get("denied_paths", []),
            confirm_on_write=data.get("file", {}).get("confirm_on_write", []),
            shell_enabled=data.get("shell", {}).get("enabled", True),
            allowed_commands=data.get("shell", {}).get("allowed_commands", []),
            denied_commands=data.get("shell", {}).get("denied_commands", ["rm -rf /", "sudo"]),
            shell_default=PermissionLevel(data.get("shell", {}).get("default", "confirm")),
            max_timeout=data.get("shell", {}).get("max_timeout", 300),
            allow_network=data.get("shell", {}).get("allow_network", False),
            max_tool_calls=data.get("global", {}).get("max_tool_calls", 100),
            audit_log=data.get("global", {}).get("audit_log", True),
            audit_log_path=Path(data.get("global", {}).get("audit_log_path", ".nano-code/audit.log")),
        )


class PermissionManager:
    """权限管理器"""
    
    def __init__(self, config: PermissionConfig):
        self.config = config
        self.guards: list[BaseGuard] = []
        self._call_count = 0
        self._audit_log: list[dict[str, Any]] = []
        
        # 初始化守卫
        self._init_guards()
    
    def _init_guards(self) -> None:
        """初始化权限守卫"""
        self.guards = [
            PathGuard(
                workspace_root=self.config.workspace_root,
                allowed_patterns=self.config.allowed_paths,
                denied_patterns=self.config.denied_paths,
                confirm_patterns=self.config.confirm_on_write,
                allow_outside=self.config.allow_outside,
            ),
            CommandGuard(
                enabled=self.config.shell_enabled,
                allowed_commands=self.config.allowed_commands,
                denied_commands=self.config.denied_commands,
                default=self.config.shell_default,
                max_timeout=self.config.max_timeout,
                allow_network=self.config.allow_network,
            ),
        ]
    
    def check(self, tool_name: str, args: dict[str, Any]) -> PermissionResult:
        """检查工具调用权限"""
        # 检查调用次数限制
        if self._call_count >= self.config.max_tool_calls:
            return PermissionResult(
                PermissionLevel.DENY,
                tool_name,
                args,
                reason=f"已达到最大调用次数 {self.config.max_tool_calls}"
            )
        
        # 运行所有守卫检查
        final_result = PermissionResult(PermissionLevel.ALLOW, tool_name, args)
        
        for guard in self.guards:
            result = guard.check(tool_name, args)
            
            # 记录审计日志
            if self.config.audit_log:
                self._log_call(tool_name, args, result)
            
            # 取最严格的权限级别
            if result.level.value > final_result.level.value:
                final_result = result
            
            # 如果被拒绝，立即返回
            if result.denied:
                return result
        
        self._call_count += 1
        return final_result
    
    def _log_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        result: PermissionResult,
    ) -> None:
        """记录审计日志"""
        import json
        from datetime import datetime
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "args": args,
            "result": result.level.value,
            "reason": result.reason,
        }
        self._audit_log.append(entry)
        
        # 写入文件
        if self.config.audit_log_path:
            self.config.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_audit_log(self) -> list[dict[str, Any]]:
        """获取审计日志"""
        return self._audit_log.copy()
```

## 6. 工具执行集成

### 6.1 修改 ToolRegistry

```python
# src/nano_code/tools/registry.py (修改后)

class ToolRegistry:
    """工具注册中心"""
    
    def __init__(
        self,
        permission_manager: PermissionManager | None = None,
        confirm_callback: Callable[[PermissionResult], bool] | None = None,
    ):
        self._tools: dict[str, BaseTool] = {}
        self.permission_manager = permission_manager
        self.confirm_callback = confirm_callback
        self._register_default_tools()
    
    def execute(self, name: str, args: dict[str, Any]) -> str:
        """执行工具（带权限检查）"""
        # 权限检查
        if self.permission_manager:
            result = self.permission_manager.check(name, args)
            
            if result.denied:
                raise PermissionError(f"权限拒绝: {result.reason}")
            
            if result.needs_confirm:
                if self.confirm_callback:
                    approved = self.confirm_callback(result)
                    if not approved:
                        raise PermissionError("用户拒绝执行")
                else:
                    raise PermissionError(f"操作需要确认: {result.reason}")
        
        # 执行工具
        tool = self.get(name)
        if tool is None:
            raise ValueError(f"Unknown tool: {name}")
        
        return str(tool.invoke(args))
```

### 6.2 CLI 确认交互

```python
# src/nano_code/cli/confirm.py

from rich.console import Console
from rich.panel import Panel

console = Console()


def request_user_confirmation(result: PermissionResult) -> bool:
    """请求用户确认"""
    console.print(Panel(
        f"[bold yellow]⚠️  操作需要确认[/bold yellow]\n\n"
        f"工具: [cyan]{result.tool_name}[/cyan]\n"
        f"参数: {result.args}\n"
        f"原因: [dim]{result.reason}[/dim]",
        title="Permission Request",
        border_style="yellow",
    ))
    
    while True:
        response = console.input("[bold]允许执行? [Y/n/a(始终允许)]: [/bold]").strip().lower()
        
        if response in ("y", "yes", ""):
            return True
        elif response in ("n", "no"):
            return False
        elif response == "a":
            # TODO: 记住此操作，后续自动允许
            return True
        else:
            console.print("[dim]请输入 Y (允许), N (拒绝) 或 A (始终允许)[/dim]")
```

## 7. 使用示例

```python
# 初始化
from pathlib import Path
from nano_code.security.manager import PermissionConfig, PermissionManager
from nano_code.tools.registry import ToolRegistry

# 加载配置
config = PermissionConfig.from_yaml(Path(".nano-code/permissions.yaml"))

# 创建权限管理器
permission_manager = PermissionManager(config)

# 创建工具注册表
registry = ToolRegistry(
    permission_manager=permission_manager,
    confirm_callback=request_user_confirmation,
)

# 执行工具
try:
    result = registry.execute("read_file", {"path": "src/main.py"})
    print(result)
except PermissionError as e:
    print(f"权限错误: {e}")
```

## 8. 配置示例

### 8.1 开发模式（宽松）

```yaml
# .nano-code/permissions.yaml (开发模式)
workspace:
  root: "."
  allow_outside: false

file:
  default: allow
  denied_paths:
    - ".env"
    - "*.pem"

shell:
  enabled: true
  default: confirm
  denied_commands:
    - "rm -rf /"
    - "rm -rf ~"
```

### 8.2 生产模式（严格）

```yaml
# .nano-code/permissions.yaml (生产模式)
workspace:
  root: "/app/workspace"
  allow_outside: false

file:
  default: confirm
  allowed_paths:
    - "src/**"
    - "tests/**"
  denied_paths:
    - ".env"
    - ".git/**"
    - "secrets/**"
  confirm_on_write:
    - "**"

shell:
  enabled: true
  default: confirm
  allowed_commands:
    - "ls"
    - "cat"
    - "pytest"
  denied_commands:
    - "rm *"
    - "sudo *"
    - "curl *"
    - "wget *"

global:
  max_tool_calls: 50
  audit_log: true
```

## 9. 实现优先级

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| P0 | PathGuard 基础实现 | 必须 |
| P0 | CommandGuard 基础实现 | 必须 |
| P1 | PermissionManager 集成 | 必须 |
| P1 | CLI 确认交互 | 必须 |
| P2 | YAML 配置加载 | 推荐 |
| P2 | 审计日志 | 推荐 |
| P3 | "始终允许" 记忆 | 可选 |
| P3 | 热重载配置 | 可选 |
