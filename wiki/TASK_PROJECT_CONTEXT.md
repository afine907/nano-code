# 任务: 实现项目上下文

## 背景
参考 OpenCode 的 `/init` 命令，让 Agent 能读取项目的 AGENTS.md 文件，理解项目结构和编码规范。

## 需求

### 1. AGENTS.md 支持
- 启动时自动查找项目根目录的 AGENTS.md
- 如果存在，将其作为系统消息注入上下文
- 支持热重载（文件修改后自动更新）

### 2. `/init` 命令
- 分析项目结构
- 生成 AGENTS.md 文件，包含：
  - 项目描述
  - 技术栈
  - 目录结构
  - 编码规范
  - 常用命令

### 3. 项目根目录检测
- 查找 `.git` 目录
- 查找 `pyproject.toml` / `package.json` 等项目文件
- 向上遍历目录树

### 4. 实现位置
- `src/nano_code/context/project.py` - 项目检测和 AGENTS.md 解析
- `src/nano_code/context/init.py` - `/init` 命令实现
- `src/nano_code/cli/main.py` - 集成项目上下文

### 5. AGENTS.md 模板
```markdown
# Project Context

## 项目描述
[自动生成或用户填写]

## 技术栈
- Python 3.11+
- LangGraph
- LangChain

## 目录结构
src/nano_code/
├── agent/     # Agent 核心
├── tools/     # 工具实现
├── memory/    # 记忆管理
└── cli/       # CLI 交互

## 编码规范
- 使用 ruff 格式化
- 使用 mypy 类型检查
- 测试覆盖率 > 80%

## 常用命令
- `uv run pytest` - 运行测试
- `uv run ruff check src/` - 代码检查
```

### 6. 测试
- 测试项目根目录检测
- 测试 AGENTS.md 读取
- 测试 `/init` 生成

## 验收标准
- [ ] 自动读取 AGENTS.md
- [ ] `/init` 生成 AGENTS.md
- [ ] 项目根目录正确检测
- [ ] 测试覆盖率 > 80%
