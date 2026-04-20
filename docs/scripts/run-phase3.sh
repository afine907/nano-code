#!/bin/bash

# Phase 3 启动脚本
# 前置条件: Phase 2 已完成

set -e

PROJECT_DIR="/tmp/nano-code"
TASK_DIR="$PROJECT_DIR/docs/tasks"

echo "=========================================="
echo "🚀 Phase 3: 集成与测试"
echo "=========================================="

# 检查 Phase 2 是否完成
echo ""
echo "📋 检查 Phase 2 前置条件..."

if [[ ! -d "$PROJECT_DIR/packages/cli/src/components" ]]; then
    echo "❌ Phase 2 未完成: 缺少组件目录"
    exit 1
fi

if [[ ! -d "$PROJECT_DIR/packages/cli/src/hooks" ]]; then
    echo "❌ Phase 2 未完成: 缺少 hooks 目录"
    exit 1
fi

echo "✅ Phase 2 已完成，开始 Phase 3"
echo ""

TASK_FILE="TASK_3.1_INTEGRATION.md"
TASK_PATH="$TASK_DIR/$TASK_FILE"

if [[ ! -f "$TASK_PATH" ]]; then
    echo "❌ Task file not found: $TASK_PATH"
    exit 1
fi

echo "📋 Starting task: $TASK_FILE"

TASK_CONTENT=$(cat "$TASK_PATH")

opencode run "
# Task: $TASK_FILE

$TASK_CONTENT

## 重要说明
- 工作目录: $PROJECT_DIR
- 创建新分支: feat/app-integration
- 完成后提交 PR
- 运行 CLI 测试: pnpm dev
"

echo ""
echo "=========================================="
echo "🎉 所有任务完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "  1. 测试 CLI: cd packages/cli && pnpm dev"
echo "  2. 合并 PR"
echo "  3. 发布新版本"
