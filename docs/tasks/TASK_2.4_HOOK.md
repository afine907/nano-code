# Task 2.4: useAgent Hook

## 背景
我们需要一个 React Hook 来管理 Agent 状态和消息。

## 前置依赖
- Task 1.3 已完成 (RPC Client 已实现)

## 目标
实现 useAgent Hook，提供消息管理、流式状态、发送消息等功能。

## 任务步骤

### 1. 创建 hooks 目录

```
packages/cli/src/hooks/
├── index.ts
└── useAgent.ts
```

### 2. 实现 useAgent.ts

```tsx
import { useState, useCallback, useEffect, useRef } from "react";
import { AgentClient } from "../client/rpc.js";
import type { StreamEvent, Message, ToolCall, Config } from "../client/types.js";

export interface UseAgentReturn {
  // 状态
  messages: Message[];
  isStreaming: boolean;
  status: "idle" | "thinking" | "executing" | "error";
  currentTool: { name: string; args: Record<string, unknown> } | undefined;
  model: string;
  config: Config | null;
  error: string | undefined;
  
  // 方法
  sendMessage: (prompt: string) => Promise<void>;
  clearMessages: () => void;
  reconnect: () => Promise<void>;
}

/**
 * Agent Hook
 * 
 * 管理与 Python Agent 的通信
 */
export function useAgent(): UseAgentReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState<"idle" | "thinking" | "executing" | "error">("idle");
  const [currentTool, setCurrentTool] = useState<{ name: string; args: Record<string, unknown> } | undefined>();
  const [model, setModel] = useState("gpt-4o-mini");
  const [config, setConfig] = useState<Config | null>(null);
  const [error, setError] = useState<string | undefined>();
  
  const clientRef = useRef<AgentClient | null>(null);
  const currentResponseRef = useRef<string>("");

  // 初始化客户端
  useEffect(() => {
    const initClient = async () => {
      try {
        const client = new AgentClient();
        await client.connect();
        clientRef.current = client;
        
        // 获取配置
        const cfg = await client.getConfig();
        setConfig(cfg);
        setModel(cfg.model);
        
        // 监听流式事件
        client.on("stream", handleStreamEvent);
        
        console.log("Agent client connected");
      } catch (err) {
        setError(`Failed to connect: ${err}`);
        setStatus("error");
      }
    };
    
    initClient();
    
    return () => {
      clientRef.current?.close();
    };
  }, []);

  // 处理流式事件
  const handleStreamEvent = useCallback((event: StreamEvent) => {
    switch (event.type) {
      case "thinking":
        setStatus("thinking");
        break;

      case "tool_call":
        setStatus("executing");
        if (event.metadata?.toolName) {
          setCurrentTool({
            name: event.metadata.toolName,
            args: event.metadata.toolArgs || {},
          });
        }
        break;

      case "tool_result":
        // 工具执行完成
        setCurrentTool(undefined);
        break;

      case "response":
        // 追加响应内容
        currentResponseRef.current += event.content;
        
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === "assistant") {
            // 更新最后一条消息
            return [
              ...prev.slice(0, -1),
              { ...last, content: currentResponseRef.current },
            ];
          }
          // 新增消息
          return [
            ...prev,
            {
              role: "assistant" as const,
              content: event.content,
              timestamp: new Date(),
            },
          ];
        });
        break;

      case "done":
        setIsStreaming(false);
        setStatus("idle");
        setCurrentTool(undefined);
        currentResponseRef.current = "";
        break;

      case "error":
        setIsStreaming(false);
        setStatus("error");
        setError(event.content);
        setCurrentTool(undefined);
        currentResponseRef.current = "";
        break;
    }
  }, []);

  // 发送消息
  const sendMessage = useCallback(async (prompt: string) => {
    if (!clientRef.current || isStreaming) {
      return;
    }

    // 添加用户消息
    const userMessage: Message = {
      role: "user",
      content: prompt,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    
    // 重置状态
    setIsStreaming(true);
    setStatus("thinking");
    setError(undefined);
    currentResponseRef.current = "";

    try {
      await clientRef.current.stream(prompt);
    } catch (err) {
      setIsStreaming(false);
      setStatus("error");
      setError(`Failed to send message: ${err}`);
    }
  }, [isStreaming]);

  // 清空消息
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(undefined);
  }, []);

  // 重新连接
  const reconnect = useCallback(async () => {
    clientRef.current?.close();
    clientRef.current = null;
    
    try {
      const client = new AgentClient();
      await client.connect();
      clientRef.current = client;
      client.on("stream", handleStreamEvent);
      
      const cfg = await client.getConfig();
      setConfig(cfg);
      setModel(cfg.model);
      setStatus("idle");
      setError(undefined);
    } catch (err) {
      setError(`Failed to reconnect: ${err}`);
      setStatus("error");
    }
  }, [handleStreamEvent]);

  return {
    messages,
    isStreaming,
    status,
    currentTool,
    model,
    config,
    error,
    sendMessage,
    clearMessages,
    reconnect,
  };
}
```

### 3. 创建导出文件 (hooks/index.ts)

```tsx
export { useAgent } from "./useAgent.js";
export type { UseAgentReturn } from "./useAgent.js";
```

### 4. 测试

创建 `tests/hooks.test.ts`:

```tsx
import { renderHook, act } from "@testing-library/react";
import { useAgent } from "../src/hooks/useAgent.js";

// Mock AgentClient
jest.mock("../src/client/rpc.js", () => ({
  AgentClient: jest.fn().mockImplementation(() => ({
    connect: jest.fn().mockResolvedValue(undefined),
    getConfig: jest.fn().mockResolvedValue({ model: "gpt-4o-mini", provider: "openai" }),
    stream: jest.fn().mockResolvedValue(undefined),
    on: jest.fn(),
    close: jest.fn(),
  })),
}));

describe("useAgent", () => {
  it("should initialize with empty messages", () => {
    const { result } = renderHook(() => useAgent());
    
    expect(result.current.messages).toEqual([]);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.status).toBe("idle");
  });

  it("should add user message on send", async () => {
    const { result } = renderHook(() => useAgent());
    
    await act(async () => {
      await result.current.sendMessage("Hello");
    });
    
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("Hello");
  });

  it("should clear messages", async () => {
    const { result } = renderHook(() => useAgent());
    
    await act(async () => {
      await result.current.sendMessage("Hello");
    });
    
    expect(result.current.messages).toHaveLength(1);
    
    act(() => {
      result.current.clearMessages();
    });
    
    expect(result.current.messages).toHaveLength(0);
  });
});
```

## 验证步骤

```bash
pnpm add -D @testing-library/react
pnpm test tests/hooks.test.ts
```

## 注意事项

1. 处理好流式事件的顺序
2. 确保内存不泄漏 (useEffect cleanup)
3. 处理错误情况

## 预期产出

- `packages/cli/src/hooks/useAgent.ts`
- `packages/cli/src/hooks/index.ts`
- 测试文件
- 测试通过
