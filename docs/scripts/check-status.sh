#!/bin/bash

# 检查任务状态

echo "=========================================="
echo "任务状态检查"
echo "=========================================="

cd /tmp/nano-code

echo ""
echo "📦 分支状态:"
git branch -a | grep -E "feat/(cli|jsonrpc|ui|markdown|animation|hook)" || echo "  无相关分支"

echo ""
echo "📁 文件检查:"
echo ""

# Phase 1 检查
echo "Phase 1 - 基础设施:"
echo "  Task 1.1 Monorepo:"
[[ -f "package.json" ]] && [[ -f "pnpm-workspace.yaml" ]] && echo "    ✅ 已完成" || echo "    ⏳ 进行中"

echo "  Task 1.2 Server:"
[[ -d "src/nano_code/server" ]] && echo "    ✅ 已完成" || echo "    ⏳ 进行中"

echo "  Task 1.3 Client:"
[[ -d "packages/cli/src/client" ]] && echo "    ✅ 已完成" || echo "    ⏳ 进行中"

# Phase 2 检查
echo ""
echo "Phase 2 - CLI 组件:"
[[ -d "packages/cli/src/components" ]] && echo "  ✅ 组件目录存在" || echo "  ⏳ 组件目录不存在"
[[ -d "packages/cli/src/hooks" ]] && echo "  ✅ Hooks 目录存在" || echo "  ⏳ Hooks 目录不存在"

# Phase 3 检查
echo ""
echo "Phase 3 - 集成:"
[[ -f "packages/cli/src/app.tsx" ]] && echo "  ✅ App 已创建" || echo "  ⏳ App 未创建"

echo ""
echo "=========================================="
