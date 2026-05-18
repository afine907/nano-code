# jojo-code 参考 Claude Code 改进方案

> 基于 Claude Code 源码分析 (2026-03-31 泄露版)
> 日期: 2026-05-17

---

## 一、当前架构 vs Claude Code

### 1.1 现有架构 (jojo-code)

```
jojo-code/
├── src/jojo_code/
│   ├── agent/           # LangGraph 状态机
│   │   ├── graph.py     # 状态图定义
│   │   ├── nodes.py     # 节点实现
│   │   └── state.py     # 状态定义
│   ├── tools/           # 工具系统 (~20个)
│   │   └── registry.py  # 工具注册中心
│   ├── core/            # 核心功能
│   │   ├── llm.py       # LLM 调用
│   │   ├── api_server.py
│   │   └── config.py
│   ├── cli/             # CLI 入口
│   ├── security/        # 权限系统
│   └── session/         # 会话管理
```

### 1.2 Claude Code 架构

```
Claude Code (TypeScript)
├── src/
│   ├── main.tsx         # 入口 (804KB)
│   ├── commands/        # 88 个命令
│   ├── tools/           # 44 个工具类
│   ├── tasks/           # 任务系统 (7种类型)
│   ├── state/           # Zustand-like 状态管理
│   ├── context/         # React Context
│   ├── services/        # 后端服务
│   │   ├── api/         # API 调用
│   │   ├── mcp/         # MCP 协议
│   │   └── oauth/       # 认证
│   └── hooks/           # React Hooks
```

---

## 二、对比分析

| 模块 | jojo-code | Claude Code | 差距 |
|------|-----------|-------------|------|
| **状态机** | LangGraph (简单) | LangGraph + Task状态机 | 中 |
| **工具数量** | ~20 | 44 | 大 |
| **权限系统** | 基础 (3级) | 精细 (auto/manual/bypass + 规则引擎) | 大 |
| **任务系统** | 无 | 7种任务类型 | 很大 |
| **子 Agent** | 无 | AgentTool | 很大 |
| **Skills** | 无 | SkillTool | 很大 |
| **MCP 支持** | 无 | 完整支持 | 很大 |
| **TUI** | 无 | Ink (React) | 大 |
| **会话记忆** | 基础 | SessionMemory 服务 | 中 |

---

## 三、改进方案 (分阶段)

### Phase 1: 核心增强 (高优先级)

#### 3.1 精细化权限系统

**当前**: 简单的 allow/deny

**目标**: Claude Code 风格的三级权限模式

```python
# 参考 Claude Code 的权限设计
from enum import Enum
from dataclasses import dataclass
from typing import Callable

class PermissionMode(Enum):
    AUTO = "auto"      # 自动批准 (信任)
    MANUAL = "manual"  # 手动确认
    BYPASS = "bypass"  # 跳过权限检查

@dataclass
class PermissionRule:
    """权限规则"""
    tool_pattern: str      # 工具名匹配 (支持通配符)
    args_pattern: dict     # 参数匹配
    action: "allow" | "deny" | "ask"

@dataclass
class PermissionResult:
    allowed: bool
    needs_confirm: bool = False
    reason: str = ""
    rule_matched: str | None = None

class PermissionManager:
    def __init__(self, mode: PermissionMode):
        self.mode = mode
        self.rules: list[PermissionRule] = []
        self.denial_tracking: dict[str, int] = {}  # 拒绝计数

    def check(self, tool_name: str, args: dict) -> PermissionResult:
        """权限检查"""
        # 1. 快速路径
        if self.mode == PermissionMode.BYPASS:
            return PermissionResult(allowed=True)

        # 2. 匹配规则
        for rule in self.rules:
            if self._matches_rule(tool_name, args, rule):
                if rule.action == "allow":
                    return PermissionResult(allowed=True)
                elif rule.action == "deny":
                    return PermissionResult(allowed=False, reason=f"规则拒绝: {rule.tool_pattern}")

        # 3. 自动模式
        if self.mode == PermissionMode.AUTO:
            return PermissionResult(allowed=True)

        # 4. 手动模式需要确认
        return PermissionResult(
            allowed=False,
            needs_confirm=True,
            reason=f"需要确认执行: {tool_name}"
        )
```

#### 3.2 任务系统 (Task Framework)

**目标**: 支持多任务并发执行

```python
# 参考 Claude Code 的 Task 系统
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable
import asyncio

class TaskType(Enum):
    LOCAL_BASH = "local_bash"
    LOCAL_AGENT = "local_agent"
    REMOTE_AGENT = "remote_agent"
    SUBAGENT = "subagent"
    WORKFLOW = "workflow"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"

@dataclass
class TaskState:
    id: str
    type: TaskType
    status: TaskStatus
    description: str
    tool_use_id: str | None = None
    start_time: float = 0
    end_time: float | None = None
    output_file: str = ""
    output_offset: int = 0

class TaskFramework:
    """任务框架 - 支持多任务并发"""

    def __init__(self):
        self.tasks: dict[str, TaskState] = {}
        self._results: dict[str, Any] = {}

    async def spawn(self, task_type: TaskType, task_fn: Callable, description: str) -> str:
        """创建并启动任务"""
        task_id = self._generate_task_id(task_type)
        self.tasks[task_id] = TaskState(
            id=task_id,
            type=task_type,
            status=TaskStatus.PENDING,
            description=description
        )

        # 后台执行
        asyncio.create_task(self._run_task(task_id, task_fn))
        return task_id

    async def _run_task(self, task_id: str, task_fn: Callable):
        self.tasks[task_id].status = TaskStatus.RUNNING
        self.tasks[task_id].start_time = time.time()

        try:
            result = await task_fn()
            self._results[task_id] = result
            self.tasks[task_id].status = TaskStatus.COMPLETED
        except Exception as e:
            self.tasks[task_id].status = TaskStatus.FAILED
            self._results[task_id] = {"error": str(e)}
        finally:
            self.tasks[task_id].end_time = time.time()

    def kill(self, task_id: str):
        """终止任务"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.KILLED
```

---

### Phase 2: 能力扩展

#### 3.3 子 Agent 支持 (AgentTool)

```python
# 参考 Claude Code 的 AgentTool
class SubAgent:
    """子 Agent - 可独立运行的 Agent"""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: list[str],  # 允许的工具列表
        model: str | None = None
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.allowed_tools = tools
        self.model = model

    async def run(self, user_message: str, parent_context: dict) -> str:
        """运行子 Agent"""
        # 使用独立的 LangGraph 图
        graph = build_agent_graph(
            system_prompt=self.system_prompt,
            allowed_tools=self.allowed_tools,
            model=self.model
        )

        result = await graph.ainvoke({
            "messages": [{"role": "user", "content": user_message}]
        })
        return result["messages"][-1].content

class AgentTool(BaseTool):
    """Agent 工具 - 用于创建和管理子 Agent"""

    name = "Agent"
    description = "Create and run sub-agents for parallel task execution"

    def __init__(self, agent_registry: "AgentRegistry"):
        super().__init__()
        self.agent_registry = agent_registry

    def _run(self, agent_name: str, task: str) -> str:
        agent = self.agent_registry.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")
        return asyncio.run(agent.run(task, {}))
```

#### 3.4 MCP 协议支持

```python
# 参考 Claude Code 的 MCP 支持
from typing import Protocol
import asyncio

class MCPClient:
    """MCP 协议客户端"""

    def __init__(self, server_config: dict):
        self.command = server_config["command"]
        self.args = server_config.get("args", [])
        self.env = server_config.get("env", {})
        self._process: asyncio.subprocess.Process | None = None

    async def connect(self):
        """连接到 MCP 服务器"""
        self._process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            env=self.env
        )

    async def call_tool(self, name: str, args: dict) -> dict:
        """调用 MCP 工具"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": args
            }
        }
        # 发送请求
        self._process.stdin.write(json.dumps(request).encode() + b"\n")
        # 读取响应
        response_line = await self._process.stdout.readline()
        return json.loads(response_line)

class MCPTool(BaseTool):
    """MCP 工具封装"""

    def __init__(self, client: MCPClient, tool_def: dict):
        self.client = client
        self.name = tool_def["name"]
        self.description = tool_def.get("description", "")

    def _run(self, **kwargs) -> str:
        result = asyncio.run(self.client.call_tool(self.name, kwargs))
        return json.dumps(result)
```

---

### Phase 3: 用户体验

#### 3.5 TUI 界面 (Textual)

```python
# 使用 Textual 构建 TUI (类似 Claude Code 的 Ink)
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input
from textual.containers import Container, Scroll

class JojoTUI(App):
    """jojo-code TUI 界面"""

    CSS = """
    Screen {
        layout: vertical;
    }
    # messages {
        height: 80%;
        border: solid green;
    }
    # input {
        height: 20%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Scroll(Static(id="messages")),
            Input(placeholder="Type your message...", id="input")
        )
        yield Footer()

    def on_input_submitted(self, event: Input.Submitted):
        """处理用户输入"""
        user_input = event.value
        # 调用 agent 处理
        # 更新消息显示
        self.query_one("#messages").update(...)
```

#### 3.6 Skills 系统

```python
# 参考 Claude Code 的 SkillTool
from pathlib import Path

class Skill:
    """Skill 定义"""

    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        manifest_path = self.path / "skill.yaml"
        return yaml.safe_load(manifest_path.read_text())

class SkillTool(BaseTool):
    """Skill 工具 - 执行预定义的技能"""

    name = "Skill"
    description = "Execute predefined skills for common tasks"

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self._load_skills()

    def _load_skills(self):
        """加载所有 Skills"""
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                skill = Skill(skill_path.name, skill_path)
                self.skills[skill.name] = skill

    def _run(self, skill_name: str, args: dict) -> str:
        skill = self.skills.get(skill_name)
        if not skill:
            raise ValueError(f"Unknown skill: {skill_name}")
        # 执行 skill
        return self._execute_skill(skill, args)
```

---

## 四、实施路线图 (Roadmap)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         jojo-code 开发路线图                                 │
│                    学习 Claude Code 设计，用 Python 实现                    │
└─────────────────────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════════════
                              阶段 0: 基础巩固 (0.5周)
══════════════════════════════════════════════════════════════════════════════

  任务                                    时间    依赖    状态
  ────────────────────────────────────────────────────────────────────────────
  [T0-1] 完善现有 LangGraph 状态机           2天    -       ✅ 完成
  [T0-2] 补充错误处理和日志                   2天    T0-1    ✅ 完成
  [T0-3] 优化工具注册中心 (registry)          1天    -       ✅ 完成

══════════════════════════════════════════════════════════════════════════════
                         阶段 1: 核心增强 (1-2周)
══════════════════════════════════════════════════════════════════════════════

  任务                                    时间    依赖    状态
  ────────────────────────────────────────────────────────────────────────────
  [T1-1] 权限系统升级 (三级模式)              3天    T0-1    ✅ 完成
         ├── PermissionMode (5种模式)
         ├── PermissionRule (规则引擎)
         │   ├── 支持通配符/正则/前缀匹配
         │   ├── 优先级机制
         │   └── RuleFactory 工厂类
         ├── PermissionManager (权限管理器)
         ├── DenialTracker (拒绝追踪)
         │   - 防止重复请求
         │   - 阈值检测
         │   - 自动过期清理
         ├── EnhancedPermissionManager (增强版)
         │   - 集成规则引擎
         │   - 集成拒绝追踪
         │   - 用户确认回调
         └── 贡献文件:
             - rule.py (规则引擎)
             - denial.py (拒绝追踪)
             - enhanced.py (增强版管理器)

  [T1-2] 任务框架 (Task System)              5天    T1-1    ✅ 完成
         ├── TaskType (6种任务类型, 与 Claude Code 一致)
         │   └── bash/agent/teammate/workflow/mcp/dream
         ├── TaskStatus (状态机)
         │   └── pending → running → completed/failed/killed
         ├── TaskExecutor (任务执行器)
         │   ├── 并发控制 (max_concurrent)
         │   ├── 重试机制 (max_retries)
         │   └── 超时控制
         ├── 任务 ID 生成 (1位前缀+8位随机)
         └── 贡献文件:
             - task/types.py (类型定义)
             - task/id.py (ID 生成)
             - task/executor.py (执行器)
             - task/__init__.py (模块导出)

  [T1-3] 错误处理标准化                       2天    -       ✅ 完成
         ├── 自定义异常类
         ├── 错误代码定义
         └── 重试机制

══════════════════════════════════════════════════════════════════════════════
                         阶段 2: 能力扩展 (2-3周)
══════════════════════════════════════════════════════════════════════════════

  任务                                    时间    依赖    状态
  ────────────────────────────────────────────────────────────────────────────
  [T2-1] 子 Agent 支持 (AgentTool)          5天    T1-2    ✅ 完成
         ├── SubAgent 类
         ├── AgentRegistry (注册中心)
         ├── AgentTool (工具封装)
         └── 并行执行支持

  [T2-2] MCP 客户端                         5天    T1-2    ✅ 完成
         ├── MCPClient (协议客户端)
         ├── MCPTool (工具封装)
         ├── MCP 工具发现
         └── MCP 资源管理

  [T2-3] 工具扩展 (+20 工具)                 3天    T0-3    ✅ 完成
         ├── WebFetchTool (网页抓取)
         ├── EditTool (文件编辑)
         ├── SearchTool (搜索)
         ├── TodoTool (待办事项)
         └── 更多垂直工具...

══════════════════════════════════════════════════════════════════════════════
                         阶段 3: 用户体验 (2周)
══════════════════════════════════════════════════════════════════════════════

  任务                                    时间    依赖    状态
  ────────────────────────────────────────────────────────────────────────────
  [T3-1] TUI 界面 (Textual)                 5天    T2-1    ⬜
         ├── 主界面布局
         ├── 消息展示
         ├── 工具权限审批
         └── 进度显示

  [T3-2] Skills 系统                        5天    T2-1    ⬜
         ├── Skill 定义格式
         ├── SkillTool
         ├── 内置 Skills
         └── 动态加载

  [T3-3] 会话记忆 (SessionMemory)           3天    -       ✅
         ├── 短期记忆 (当前会话)
         ├── 长期记忆 (持久化)
         └── 记忆检索

══════════════════════════════════════════════════════════════════════════════
                         阶段 4: 生态集成 (1-2周)
══════════════════════════════════════════════════════════════════════════════

  任务                                    时间    依赖    状态
  ────────────────────────────────────────────────────────────────────────────
  [T4-1] 多模型支持                         3天    -       ⬜
         ├── OpenAI 兼容
         ├── Anthropic
         ├── DeepSeek
         └── 模型路由

  [T4-2] 插件系统                           5天    T2-2    ⬜
         ├── Plugin 接口
         ├── 插件加载器
         └── 官方插件集

  [T4-3] API Server 增强                    3天    T3-1    ⬜
         ├── RESTful API
         ├── WebSocket
         └── SSE 事件流

══════════════════════════════════════════════════════════════════════════════
                         阶段 5: 高级功能 (可选)
══════════════════════════════════════════════════════════════════════════════

  任务                                    时间    依赖    状态
  ────────────────────────────────────────────────────────────────────────────
  [T5-1] Computer Use                      5天    T4-1    ⬜
         ├── 截图
         ├── 鼠标控制
         └── 键盘输入

  [T5-2] 多模态支持                         3天    -       ⬜
         ├── 图片理解
         └── 文件理解

  [T5-3] 团队协作                          5天    T3-3    ⬜
         ├── 团队空间
         ├── 共享记忆
         └── 协作任务

══════════════════════════════════════════════════════════════════════════════
                              总工期估算
══════════════════════════════════════════════════════════════════════════════

  阶段        时间       累计
  ─────────────────────────────────
  阶段 0      0.5 周     0.5 周
  阶段 1      1.5 周     2.0 周
  阶段 2      2.5 周     4.5 周
  阶段 3      2.0 周     6.5 周
  阶段 4      1.5 周     8.0 周
  阶段 5      1.5 周     9.5 周

  实际工期: 约 10 周 (2.5 个月)
  可根据优先级调整顺序

══════════════════════════════════════════════════════════════════════════════
                              里程碑
══════════════════════════════════════════════════════════════════════════════

  M1 (Week 2)   - 权限系统 + 任务框架完成 → 可用性提升
  M2 (Week 5)   - 子 Agent + MCP + 工具扩展 → 能力对齐 Claude Code
  M3 (Week 7)   - TUI + Skills + 会话记忆 → 体验完善
  M4 (Week 10)  - 生态集成 → 可发布版本

══════════════════════════════════════════════════════════════════════════════

---

## 五、关键参考点

### 5.1 权限系统设计

Claude Code 的权限系统非常值得学习:

1. **三级模式**: auto / manual / bypass
2. **规则引擎**: 支持通配符匹配
3. **拒绝追踪**: 防止重复请求
4. **用户确认回调**: 支持交互式确认

### 5.2 任务系统设计

1. **任务类型**: 7 种不同任务
2. **状态机**: 完整的状态转换
3. **输出持久化**: 基于文件的输出存储
4. **进度追踪**: 支持实时进度回调

### 5.3 工具系统设计

1. **Zod 验证**: 输入参数类型验证
2. **Tool 接口**: 统一的工具定义
3. **条件编译**: feature flags
4. **权限集成**: 每个工具都集成权限检查

---

## 六、总结

jojo-code 当前架构简洁，适合快速开发。参考 Claude Code 可以:

1. **短期**: 提升权限系统和任务管理能力
2. **中期**: 扩展子 Agent 和 MCP 支持
3. **长期**: 构建完整的开发者工具生态

建议按优先级逐步推进，避免一次性大改。