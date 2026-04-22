#!/usr/bin/env node
import React from 'react';
import { render } from 'ink';
import { App } from './app.js';

// 检查 TTY 支持
if (!process.stdin.isTTY) {
  console.error('错误: 此 CLI 需要在终端 (TTY) 环境中运行');
  console.error('请在终端中运行此命令，而不是通过管道或脚本');
  process.exit(1);
}

// 启动 CLI
const { waitUntilExit } = render(<App />);

// 等待退出
waitUntilExit().then(() => {
  process.exit(0);
});
