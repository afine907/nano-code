#!/usr/bin/env node
import React, { useState, useCallback } from "react";
import { render, Box, Text, useApp, useInput } from "ink";
import {
  ChatView,
  InputBox,
  StatusBar,
  MessageItem,
  ToolExecution,
} from "./components/index.js";
import { useAgent } from "./hooks/useAgent.js";

export function App() {
  const {
    messages,
    sendMessage,
    clearMessages,
    isStreaming,
    status,
    currentTool,
    model,
    error,
  } = useAgent();

  const [input, setInput] = useState("");
  const { exit } = useApp();

  // 全局快捷键
  useInput((inputChar, key) => {
    // Ctrl+C 退出
    if (key.ctrl && inputChar === "c") {
      exit();
    }
  });

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isStreaming) return;

    // 处理命令
    if (input.startsWith("/")) {
      const cmd = input.trim().toLowerCase();

      switch (cmd) {
        case "/exit":
        case "/quit":
        case "/q":
          exit();
          return;

        case "/clear":
          clearMessages();
          setInput("");
          return;

        case "/help":
          console.log(`
Nano Code CLI - Help

Commands:
  /help     Show this help
  /exit     Exit the CLI
  /clear    Clear conversation
  /model    Show current model

Shortcuts:
  Ctrl+C    Exit
        `);
          setInput("");
          return;

        case "/model":
          console.log(`Current model: ${model}`);
          setInput("");
          return;

        default:
          console.log(`Unknown command: ${cmd}`);
          setInput("");
          return;
      }
    }

    // 发送消息
    await sendMessage(input);
    setInput("");
  }, [input, isStreaming, sendMessage, clearMessages, exit, model]);

  return (
    <Box flexDirection="column" height="100%" padding={1}>
      {/* 标题栏 */}
      <Box marginBottom={1} justifyContent="space-between">
        <Box>
          <Text bold color="cyan">
            🤖 Nano Code
          </Text>
          <Text dimColor> v0.1.0</Text>
        </Box>
        <Box>
          <Text dimColor>Model: </Text>
          <Text color="green">{model}</Text>
        </Box>
      </Box>

      {/* 聊天区域 */}
      <Box flexGrow={1} flexDirection="column">
        <ChatView messages={messages} isStreaming={isStreaming} />

        {/* 工具执行动画 */}
        {currentTool && (
          <ToolExecution toolName={currentTool.name} args={currentTool.args} />
        )}

        {/* 错误显示 */}
        {error && (
          <Box borderStyle="round" borderColor="red" paddingX={1}>
            <Text color="red">Error: {error}</Text>
          </Box>
        )}
      </Box>

      {/* 输入框 */}
      <Box marginTop={1}>
        <InputBox
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          disabled={isStreaming}
          placeholder={
            isStreaming ? "Thinking..." : "Type a message... (/help for commands)"
          }
        />
      </Box>

      {/* 状态栏 */}
      <StatusBar status={status} model={model} />
    </Box>
  );
}

// 入口
render(<App />);
