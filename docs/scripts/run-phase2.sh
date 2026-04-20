#!/bin/bash

# Phase 2 启动脚本
# 前置条件: Phase 1 已完成

set -e

PROJECT_DIR="/tmp/nano-code"
TASK_DIR="$PROJECT_DIR/docs/tasks"

echo "=========================================="
echo "🚀 Phase 2: CLI 组件 (4 个任务并行)"
echo "=========================================="

# 检查 Phase 1 是否完成
echo ""
echo "📋 检查 Phase 1 前置条件..."

if [[ ! -f "$PROJECT_DIR/package.json" ]]; then
    echo "❌ Phase 1 未完成: 缺少 monorepo 配置"
    echo "   请先运行 ./run-phase1.sh"
    exit 1
fi

if [[ ! -d "$PROJECT_DIR/packages/cli" ]]; then
    echo "❌ Phase 1 未完成: 缺少 packages/cli 目录"
    exit 1
fi

echo "✅ Phase 1 已完成，开始 Phase 2"
echo ""

PHASE2_TASKS=(
    "TASK_2.1_UI_COMPONENTS.md"
    "TASK_2.2_MARKDOWN.md"
    "TASK_2.3_ANIMATION.md"
    "TASK_2.4_HOOK.md"
)

run_task() {
    local task_file=$1
    local task_path="$TASK_DIR/$task_file"
    
    if [[ ! -f "$task_path" ]]; then
        echo "❌ Task file not found: $task_path"
        return 1
    fi
    
    echo "📋 Starting task: $task_file"
    
    local task_content=$(cat "$task_path")
    
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

for task in "${PHASE2_TASKS[@]}"; do
    run_task "$task"
done

echo ""
echo "⏳ 等待 Phase 2 完成..."
echo "   完成后运行 ./run-phase3.sh"
