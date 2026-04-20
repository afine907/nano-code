# Task 2.1: 基础 UI 组件

## 背景
我们需要创建 ink 组件来实现 CLI 的用户界面。

## 前置依赖
- Task 1.1 已完成 (monorepo 结构已创建)

## 目标
实现 4 个基础 UI 组件：ChatView、MessageItem、InputBox、StatusBar。

## 任务步骤

### 1. 安装依赖

```bash
cd packages/cli
pnpm add ink-text-input ink-spinner
```

### 2. 创建组件目录

```
packages/cli/src/components/
├── ChatView.tsx
├── MessageItem.tsx
├── InputBox.tsx
└── StatusBar.tsx
```

### 3. 实现 MessageItem.tsx

```tsx
import React from "react";
import { Box, Text } from "ink";

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
}

export interface MessageItemProps {
  message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  // 角色颜色
  const roleColor = isUser ? "green" : isAssistant ? "blue" : "yellow";
  const roleLabel = isUser ? "You" : isAssistant ? "Assistant" : "System";

  return (
    <Box flexDirection="column" marginBottom={1}>
      {/* 角色和时间 */}
      <Box>
        <Text bold color={roleColor}>
          {roleLabel}:
        </Text>
        <Text dimColor> {message.timestamp.toLocaleTimeString()}</Text>
      </Box>

      {/* 消息内容 */}
      <Box marginLeft={2} flexDirection="column">
        {/* 简单文本渲染，后续 Task 2.2 会用 Markdown 组件替换 */}
        {message.content.split("\n").map((line, idx) => (
          <Text key={idx}>{line}</Text>
        ))}
      </Box>
    </Box>
  );
}
```

### 4. 实现 ChatView.tsx

```tsx
import React from "react";
import { Box, Text } from "ink";
import { MessageItem, Message } from "./MessageItem.js";

export interface ChatViewProps {
  messages: Message[];
  isStreaming: boolean;
}

export function ChatView({ messages, isStreaming }: ChatViewProps) {
  if (messages.length === 0) {
    return (
      <Box
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        flexGrow={1}
      >
        <Text dimColor>Welcome to Nano Code!</Text>
        <Text dimColor>Ask me anything about your code.</Text>
        <Text dimColor></Text>
        <Text dimColor>Commands: /help, /exit, /clear</Text>
      </Box>
    );
  }

  return (
    <Box flexDirection="column" flexGrow={1}>
      {messages.map((msg, idx) => (
        <MessageItem key={idx} message={msg} />
      ))}
      
      {isStreaming && (
        <Box>
          <Text dimColor>Thinking...</Text>
        </Box>
      )}
    </Box>
  );
}
```

### 5. 实现 InputBox.tsx

```tsx
import React, { useState } from "react";
import { Box, Text, useInput } from "ink";
import TextInput from "ink-text-input";

export interface InputBoxProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export function InputBox({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = "Type a message...",
}: InputBoxProps) {
  const [multiline, setMultiline] = useState(false);
  const [lines, setLines] = useState<string[]>([]);

  // 全局快捷键
  useInput(
    (input, key) => {
      // 多行模式下 Enter 添加新行
      if (key.return && multiline && !disabled) {
        if (value.trim()) {
          setLines([...lines, value]);
          onChange("");
        }
      }
    },
    { isActive: multiline }
  );

  const handleSubmit = () => {
    if (disabled) return;
    
    if (multiline && lines.length > 0) {
      // 多行模式：合并所有行
      const fullText = [...lines, value].join("\n");
      onChange(fullText);
      setLines([]);
      setMultiline(false);
    }
    
    onSubmit();
  };

  const toggleMultiline = () => {
    if (multiline && lines.length > 0) {
      // 退出多行模式时合并
      onChange([...lines, value].join("\n"));
      setLines([]);
    }
    setMultiline(!multiline);
  };

  return (
    <Box flexDirection="column">
      {/* 多行提示 */}
      {multiline && lines.length > 0 && (
        <Box marginBottom={1} flexDirection="column">
          {lines.map((line, idx) => (
            <Text key={idx} dimColor>
              {`>>> ${line}`}
            </Text>
          ))}
        </Box>
      )}

      {/* 输入框 */}
      <Box
        borderStyle="round"
        borderColor={disabled ? "gray" : "cyan"}
        paddingX={1}
      >
        <Text dimColor>{multiline ? ">>> " : "> "}</Text>
        <TextInput
          value={value}
          onChange={onChange}
          onSubmit={handleSubmit}
          placeholder={disabled ? "Thinking..." : placeholder}
          showCursor={!disabled}
        />
      </Box>

      {/* 提示 */}
      <Box marginTop={1}>
        <Text dimColor>
          {multiline
            ? "Enter 换行 | Ctrl+D 发送"
            : "Enter 发送 | Ctrl+D 多行模式"}
        </Text>
        {!multiline && (
          <Text dimColor> | /help 帮助 | /exit 退出</Text>
        )}
      </Box>
    </Box>
  );
}
```

### 6. 实现 StatusBar.tsx

```tsx
import React from "react";
import { Box, Text } from "ink";

export interface StatusBarProps {
  status: "idle" | "thinking" | "executing" | "error";
  model?: string;
}

export function StatusBar({ status, model = "gpt-4o-mini" }: StatusBarProps) {
  const statusConfig = {
    idle: { color: "gray", text: "Ready" },
    thinking: { color: "yellow", text: "Thinking..." },
    executing: { color: "cyan", text: "Executing..." },
    error: { color: "red", text: "Error" },
  };

  const config = statusConfig[status];

  return (
    <Box marginTop={1} flexDirection="row">
      <Box marginRight={2}>
        <Text dimColor>Model: </Text>
        <Text color="green">{model}</Text>
      </Box>
      <Box>
        <Text dimColor>Status: </Text>
        <Text color={config.color}>{config.text}</Text>
      </Box>
    </Box>
  );
}
```

### 7. 创建导出文件

创建 `packages/cli/src/components/index.ts`:

```tsx
export { ChatView } from "./ChatView.js";
export type { ChatViewProps } from "./ChatView.js";

export { MessageItem } from "./MessageItem.js";
export type { MessageItemProps, Message } from "./MessageItem.js";

export { InputBox } from "./InputBox.js";
export type { InputBoxProps } from "./InputBox.js";

export { StatusBar } from "./StatusBar.js";
export type { StatusBarProps } from "./StatusBar.js";
```

## 验证步骤

1. 构建项目:
```bash
pnpm build
```

2. 创建测试文件 `tests/components.test.tsx`:
```tsx
import React from "react";
import { render } from "ink-testing-library";
import { MessageItem } from "../src/components/MessageItem.js";

describe("Components", () => {
  it("should render MessageItem", () => {
    const { lastFrame } = render(
      <MessageItem
        message={{
          role: "user",
          content: "Hello",
          timestamp: new Date(),
        }}
      />
    );
    
    expect(lastFrame()).toContain("You:");
    expect(lastFrame()).toContain("Hello");
  });
});
```

3. 运行测试:
```bash
pnpm test
```

## 注意事项

1. 使用 `.js` 后缀导入 (ESM 要求)
2. 组件保持简单，后续可以优化
3. 确保类型导出正确

## 预期产出

- `packages/cli/src/components/` 目录下的 5 个文件
- 组件可以独立渲染
- 测试通过
