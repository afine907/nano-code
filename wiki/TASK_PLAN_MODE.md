# 任务: 实现 Plan 模式

## 背景
参考 Claude Code 的 Plan 模式，实现一个只读规划模式，让 Agent 先分析问题、制定计划，再切换到执行模式。

## 需求

### 1. 模式切换
- 在 CLI 中支持 `Tab` 键切换 Build/Plan 模式
- Plan 模式下，Agent 只读，不修改文件
- Build 模式下，Agent 可以执行写操作

### 2. Plan 模式行为
- 不执行任何写操作（write_file, edit_file, run_command）
- 工具调用时检查模式，阻止写操作
- 返回详细的执行计划，列出将要进行的操作

### 3. 实现位置
- `src/nano_code/agent/modes.py` - 模式定义
- `src/nano_code/agent/nodes.py` - 修改 execute_node 支持模式检查
- `src/nano_code/cli/console.py` - 添加模式切换 UI
- `src/nano_code/tools/registry.py` - 工具分类（读/写）

### 4. 测试
- 测试 Plan 模式下写操作被阻止
- 测试模式切换
- 测试 Build 模式正常执行

## 参考代码
```python
# modes.py
from enum import Enum

class AgentMode(Enum):
    BUILD = "build"  # 可以执行所有操作
    PLAN = "plan"    # 只读模式，只分析不修改

# 在 AgentState 中添加 mode 字段
# 在 execute_node 中检查模式
```

## 验收标准
- [ ] Plan 模式下，write_file, edit_file, run_command 被阻止
- [ ] Tab 键可以切换模式
- [ ] 模式状态在 UI 中显示
- [ ] 测试覆盖率 > 80%
