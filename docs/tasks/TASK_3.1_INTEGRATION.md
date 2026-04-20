# Task 3.1: App 集成

## 背景
我们需要将所有组件集成到主应用中。

## 前置依赖
- Task 2.1, 2.2, 2.3, 2.4 已完成

## 目标
创建 App.tsx 主组件，集成所有功能。

## 任务步骤

### 1. 实现 App.tsx

```tsx
#!/usr/bin/env node
import React, { useState, useCallback } from "react";
import { render, Box, Text, useApp, useInput } from "ink";
import { ChatView, InputBox, StatusBar, MessageItem, Markdown } from "./components/index.js";
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
  Ctrl+D    Toggle multiline mode
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
      <Box flexGrow={1} flexDirection="column" overflowY="auto">
        <ChatView messages={messages} isStreaming={isStreaming} />
        
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
          placeholder={isStreaming ? "Thinking..." : "Type a message... (/help for commands)"}
        />
      </Box>

      {/* 状态栏 */}
      <StatusBar status={status} model={model} />
    </Box>
  );
}

// 入口
if (import.meta.url === `file://${process.argv[1]}`) {
  render(<App />);
}

export default App;
```

### 2. 更新入口文件 (src/index.ts)

```tsx
#!/usr/bin/env node
import React from "react";
import { render } from "ink";
import { App } from "./app.js";

// 启动应用
render(<App />);
```

### 3. 更新 package.json

添加 bin 和 scripts:

```json
{
  "bin": {
    "nano-code": "./dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "dev": "ts-node --esm src/index.ts",
    "start": "node dist/index.js"
  }
}
```

### 4. 测试运行

```bash
# 开发模式
pnpm dev

# 或构建后运行
pnpm build
pnpm start
```

## 验证步骤

1. 启动 CLI:
```bash
pnpm dev
```

2. 测试命令:
```
/help
/clear
/exit
```

3. 测试对话:
```
Hello, who are you?
```

## 注意事项

1. 确保 Python Server 可以启动
2. 处理好错误情况
3. 退出时清理资源

## 预期产出

- `packages/cli/src/app.tsx`
- `packages/cli/src/index.ts`
- CLI 可以正常启动和运行
