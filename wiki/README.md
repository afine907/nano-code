# Nano-Code Wiki

Nano-Code 是一个基于 LangGraph 构建的迷你编程 Agent，用于学习 AI Agent 架构。

## 文档目录

| 文档 | 说明 |
|------|------|
| [01-项目结构](01-项目结构.md) | 目录结构、核心文件说明、架构层次 |
| [02-Agent架构](02-Agent架构.md) | LangGraph 状态机设计、节点实现、执行流程 |
| [03-工具系统](03-工具系统.md) | 工具注册、工具定义、添加新工具 |
| [04-LLM配置](04-LLM配置.md) | API 配置、支持的模型、优先级 |
| [05-记忆系统](05-记忆系统.md) | 对话记忆、Token 计数、自动压缩 |
| [06-开发指南](06-开发指南.md) | 环境设置、常用命令、代码风格 |
| [07-权限系统](07-权限系统.md) | 路径隔离、命令过滤、用户确认、审计日志 |
| [08-代码审查记录](08-代码审查记录.md) | PR #3 代码审查报告 |
| [09-PR交互增强](09-PR交互增强.md) | PR #3 CLI 交互增强功能说明 |
| [DEV_PLAN](DEV_PLAN.md) | 核心能力开发计划 |
| [TASK_PLAN_MODE](TASK_PLAN_MODE.md) | Plan 模式任务需求 |
| [TASK_PROJECT_CONTEXT](TASK_PROJECT_CONTEXT.md) | 项目上下文任务需求 |
| [TASK_SESSION_RECOVERY](TASK_SESSION_RECOVERY.md) | 会话恢复任务需求 |
| [TASK_WEB_SEARCH](TASK_WEB_SEARCH.md) | Web 搜索任务需求 |
| [ENHANCEMENT_SUMMARY](ENHANCEMENT_SUMMARY.md) | 工具增强功能总结 |
| [FINAL_STATUS](FINAL_STATUS.md) | 最终状态报告 |
| [PR_DESCRIPTION](PR_DESCRIPTION.md) | PR 描述文档 |
| [SUBMIT_GUIDE](SUBMIT_GUIDE.md) | 提交指南 |
| [tool-permission-design](tool-permission-design.md) | 工具权限详细设计 |

## 快速开始

```bash
# 安装依赖
uv sync

# 配置 API Key
cp .env.example .env

# 运行 CLI
uv run nano-code
```

## 核心概念

### Agent 循环

```
Thinking → Tool Call → Execute → Observe → Thinking → ...
```

### 三层架构

```
CLI Layer → Agent Loop → Tool Layer
```

### 关键技术

- **LangGraph**: 状态机驱动的 Agent 循环
- **LangChain**: 工具定义和 LLM 抽象
- **Pydantic**: 配置和状态管理
- **Rich/Prompt Toolkit**: 交互式 CLI
