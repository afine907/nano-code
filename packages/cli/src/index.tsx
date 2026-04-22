#!/usr/bin/env node
import React from 'react';
import { render } from 'ink';
import { App } from './app.js';
import { ErrorBoundary } from './components/ErrorBoundary.js';

// 检查 TTY 支持
if (!process.stdin.isTTY) {
  console.error('错误: 此 CLI 需要在终端 (TTY) 环境中运行');
  console.error('请在终端中运行此命令，而不是通过管道或脚本');
  process.exit(1);
}

// 确保 stdin 支持必要的方法
if (typeof process.stdin.setRawMode !== 'function') {
  console.error('错误: 当前终端不支持 raw mode');
  console.error('请尝试在不同的终端中运行');
  process.exit(1);
}

// 检查 TTY 支持
if (!process.stdin.isTTY) {
  console.error('错误: 此 CLI 需要在终端 (TTY) 环境中运行');
  console.error('请在终端中运行此命令，而不是通过管道或脚本');
  process.exit(1);
}

// 启动 CLI
try {
  const { waitUntilExit } = render(
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );

  // 等待退出
  waitUntilExit().then(() => {
    process.exit(0);
  });
} catch (error) {
  console.error('CLI 启动失败:', error instanceof Error ? error.message : error);
  process.exit(1);
}
