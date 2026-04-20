# Task 2.3: 工具执行动画组件

## 背景
我们需要在工具执行时显示动画效果，提升用户体验。

## 前置依赖
- Task 1.1 已完成 (monorepo 结构已创建)

## 目标
实现 ToolExecution 和 ThinkingIndicator 组件。

## 任务步骤

### 1. 实现 ToolExecution.tsx

```tsx
import React from "react";
import { Box, Text } from "ink";
import Spinner from "ink-spinner";

export interface ToolExecutionProps {
  toolName: string;
  args?: Record<string, unknown>;
}

/**
 * 工具执行动画组件
 */
export function ToolExecution({ toolName, args }: ToolExecutionProps) {
  // 格式化参数显示
  const formatArgs = (args?: Record<string, unknown>): string => {
    if (!args) return "";
    
    const entries = Object.entries(args);
    if (entries.length === 0) return "";
    
    // 只显示前 3 个参数
    const displayEntries = entries.slice(0, 3);
    const formatted = displayEntries
      .map(([key, value]) => {
        const valueStr = typeof value === "string" 
          ? value.length > 30 ? value.slice(0, 30) + "..." : value
          : JSON.stringify(value);
        return `${key}=${valueStr}`;
      })
      .join(", ");
    
    if (entries.length > 3) {
      return `${formatted}, ...`;
    }
    return formatted;
  };

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="yellow"
      paddingX={1}
      marginBottom={1}
    >
      {/* 工具名称 + 加载动画 */}
      <Box>
        <Text color="yellow">
          <Spinner type="dots" />
        </Text>
        <Text> </Text>
        <Text bold color="cyan">
          {toolName}
        </Text>
      </Box>

      {/* 参数显示 */}
      {args && Object.keys(args).length > 0 && (
        <Box marginLeft={2}>
          <Text dimColor>{formatArgs(args)}</Text>
        </Box>
      )}
    </Box>
  );
}
```

### 2. 实现 ThinkingIndicator.tsx

```tsx
import React from "react";
import { Box, Text } from "ink";
import Spinner from "ink-spinner";

export interface ThinkingIndicatorProps {
  message?: string;
}

/**
 * 思考中指示器
 */
export function ThinkingIndicator({ message = "Thinking" }: ThinkingIndicatorProps) {
  return (
    <Box>
      <Text color="cyan">
        <Spinner type="dots" />
      </Text>
      <Text dimColor> {message}...</Text>
    </Box>
  );
}

/**
 * 不同类型的加载指示器
 */
export function LoadingDots() {
  return (
    <Text color="cyan">
      <Spinner type="dots" />
    </Text>
  );
}

export function LoadingBounce() {
  return (
    <Text color="yellow">
      <Spinner type="bounce" />
    </Text>
  );
}

export function LoadingCircle() {
  return (
    <Text color="green">
      <Spinner type="circle" />
    </Text>
  );
}
```

### 3. 更新 components/index.ts

```tsx
export { ToolExecution } from "./ToolExecution.js";
export type { ToolExecutionProps } from "./ToolExecution.js";

export { 
  ThinkingIndicator, 
  LoadingDots, 
  LoadingBounce, 
  LoadingCircle 
} from "./ThinkingIndicator.js";
export type { ThinkingIndicatorProps } from "./ThinkingIndicator.js";
```

### 4. 测试

创建 `tests/animation.test.tsx`:

```tsx
import React from "react";
import { render } from "ink-testing-library";
import { ToolExecution } from "../src/components/ToolExecution.js";
import { ThinkingIndicator } from "../src/components/ThinkingIndicator.js";

describe("Animation Components", () => {
  it("should render ToolExecution", () => {
    const { lastFrame } = render(
      <ToolExecution toolName="read_file" args={{ path: "/src/main.py" }} />
    );
    
    expect(lastFrame()).toContain("read_file");
    expect(lastFrame()).toContain("path=/src/main.py");
  });

  it("should render ToolExecution without args", () => {
    const { lastFrame } = render(
      <ToolExecution toolName="list_directory" />
    );
    
    expect(lastFrame()).toContain("list_directory");
  });

  it("should render ThinkingIndicator", () => {
    const { lastFrame } = render(<ThinkingIndicator />);
    
    expect(lastFrame()).toContain("Thinking");
  });

  it("should render custom thinking message", () => {
    const { lastFrame } = render(
      <ThinkingIndicator message="Processing" />
    );
    
    expect(lastFrame()).toContain("Processing");
  });
});
```

## 验证步骤

```bash
pnpm test tests/animation.test.tsx
```

## 注意事项

1. ink-spinner 提供多种动画类型：dots, bounce, circle 等
2. 参数显示要简洁，避免过长
3. 动画要在工具执行完成后停止

## 预期产出

- `packages/cli/src/components/ToolExecution.tsx`
- `packages/cli/src/components/ThinkingIndicator.tsx`
- 测试文件
- 测试通过
