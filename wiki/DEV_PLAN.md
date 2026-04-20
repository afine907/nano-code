# Nano-Code 核心能力开发计划

## 项目信息
- 项目路径: /home/admin/.openclaw/workspace/nano-code
- 测试命令: `uv run pytest tests/ -v`
- 格式化: `uv run ruff format src/ tests/`
- 检查: `uv run ruff check src/ tests/ --fix`

## 任务清单

### Task 1: Plan 模式 (分支: feat/plan-mode)
实现只读规划模式，Agent 先分析后执行。

**实现步骤**:
1. 创建 `src/nano_code/agent/modes.py` - 定义 AgentMode 枚举
2. 修改 `src/nano_code/agent/state.py` - 添加 mode 字段
3. 修改 `src/nano_code/agent/nodes.py` - execute_node 检查模式
4. 修改 `src/nano_code/tools/registry.py` - 添加工具分类（读/写）
5. 修改 `src/nano_code/cli/console.py` - 添加模式切换 UI
6. 创建 `tests/test_agent/test_modes.py` - 测试

**关键代码**:
```python
# modes.py
from enum import Enum

class AgentMode(Enum):
    BUILD = "build"  # 完全访问
    PLAN = "plan"    # 只读模式

# registry.py
WRITE_TOOLS = {"write_file", "edit_file", "run_command"}
READ_TOOLS = {"read_file", "list_directory", "grep_search", "glob_search"}
```

### Task 2: 会话恢复 (分支: feat/session-recovery)
实现会话保存和恢复。

**实现步骤**:
1. 创建 `src/nano_code/session/` 目录
2. 创建 `session/models.py` - Session 数据模型
3. 创建 `session/manager.py` - 会话管理器
4. 修改 `cli/main.py` - 集成会话管理
5. 创建 `tests/test_session/` - 测试

### Task 3: 项目上下文 (分支: feat/project-context)
读取 AGENTS.md 理解项目。

**实现步骤**:
1. 创建 `src/nano_code/context/` 目录
2. 创建 `context/project.py` - 项目检测和 AGENTS.md 解析
3. 创建 `context/init.py` - /init 命令实现
4. 修改 `cli/main.py` - 集成项目上下文

### Task 4: Web 搜索 (分支: feat/web-search-tools)
添加联网搜索能力。

**实现步骤**:
1. 添加依赖: `duckduckgo-search`
2. 创建 `src/nano_code/tools/web_tools.py`
3. 修改 `tools/registry.py` - 注册新工具
4. 创建 `tests/test_tools/test_web_tools.py`

## 开发流程
1. 切换到对应分支
2. 阅读任务文件 TASK_*.md
3. 实现功能
4. 运行测试: `uv run pytest tests/ -v`
5. 格式化代码: `uv run ruff format src/ tests/`
6. 提交代码

## 注意事项
- 每个功能独立开发，不要跨分支修改
- 保持测试覆盖率 > 80%
- 使用现有的代码风格
