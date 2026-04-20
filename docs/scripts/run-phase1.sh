#!/bin/bash

# CLI 重构 - 并行任务启动脚本
# 使用 OpenCode 执行任务

set -e

PROJECT_DIR="/tmp/nano-code"
TASK_DIR="$PROJECT_DIR/docs/tasks"

echo "=========================================="
echo "Nano Code CLI 重构 - 并行任务启动"
echo "=========================================="
echo ""

# Phase 1 任务
PHASE1_TASKS=(
    "TASK_1.1_MONOREPO.md"
    "TASK_1.2_SERVER.md"
    "TASK_1.3_CLIENT.md"
)

# Phase 2 任务 (依赖 Phase 1)
PHASE2_TASKS=(
    "TASK_2.1_UI_COMPONENTS.md"
    "TASK_2.2_MARKDOWN.md"
    "TASK_2.3_ANIMATION.md"
    "TASK_2.4_HOOK.md"
)

# Phase 3 任务 (依赖 Phase 2)
PHASE3_TASKS=(
    "TASK_3.1_INTEGRATION.md"
)

# 读取任务内容并启动 OpenCode
run_task() {
    local task_file=$1
    local task_path="$TASK_DIR/$task_file"
    
    if [[ ! -f "$task_path" ]]; then
        echo "❌ Task file not found: $task_path"
        return 1
    fi
    
    echo "📋 Starting task: $task_file"
    
    # 读取任务内容
    local task_content=$(cat "$task_path")
    
    # 启动 OpenCode (后台)
    opencode run "
# Task: $task_file

$task_content

## 重要说明
- 工作目录: $PROJECT_DIR
- 创建新分支: feat/\$(basename $task_file .md | tr '[:upper:]' '[:lower:]')
- 完成后提交 PR
" &
    
    echo "✅ Started: $task_file (PID: $!)"
}

echo "🚀 Phase 1: 基础设施 (3 个任务并行)"
echo "=========================================="

for task in "${PHASE1_TASKS[@]}"; do
    run_task "$task"
done

echo ""
echo "⏳ 等待 Phase 1 完成..."
echo "   提示: Phase 1 完成后，运行 phase2 启动下一阶段"
echo ""
echo "=========================================="
echo "检查任务状态: ./check-status.sh"
echo "=========================================="
