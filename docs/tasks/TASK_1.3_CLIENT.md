# Task 1.3: TypeScript JSON-RPC Client

## 背景
我们需要创建一个 TypeScript 客户端，用于启动 Python Server 并通过 JSON-RPC 通信。

## 前置依赖
- Task 1.1 已完成 (monorepo 结构已创建)

## 目标
在 `packages/cli/src/client/` 目录下实现 JSON-RPC 客户端。

## 任务步骤

### 1. 创建目录结构

```
packages/cli/src/client/
├── index.ts        # 导出
├── rpc.ts          # RPC 客户端
└── types.ts        # 类型定义
```

### 2. 实现类型定义 (types.ts)

```typescript
/**
 * JSON-RPC 类型定义
 */

export interface JSONRPCRequest {
  jsonrpc: "2.0";
  id: string;
  method: string;
  params?: Record<string, unknown>;
}

export interface JSONRPCResponse<T = unknown> {
  jsonrpc: "2.0";
  id: string;
  result?: T;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}

export interface JSONRPCNotification {
  jsonrpc: "2.0";
  method: string;
  params: unknown;
}

/**
 * 流式事件
 */
export type StreamEventType = 
  | "thinking" 
  | "tool_call" 
  | "tool_result" 
  | "response" 
  | "done" 
  | "error";

export interface StreamEvent {
  type: StreamEventType;
  content: string;
  metadata?: {
    toolName?: string;
    toolArgs?: Record<string, unknown>;
    duration?: number;
  };
}

/**
 * 工具定义
 */
export interface Tool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

/**
 * 配置
 */
export interface Config {
  model: string;
  provider: string;
  baseUrl?: string;
}

/**
 * 消息
 */
export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result?: string;
}
```

### 3. 实现 RPC 客户端 (rpc.ts)

```typescript
/**
 * JSON-RPC Client for Nano Code
 * 
 * 通过 stdio 与 Python Server 通信
 */

import { spawn, ChildProcess } from "child_process";
import { EventEmitter } from "events";
import {
  JSONRPCRequest,
  JSONRPCResponse,
  JSONRPCNotification,
  StreamEvent,
  Tool,
  Config,
} from "./types.js";

export class AgentClient extends EventEmitter {
  private process: ChildProcess | null = null;
  private requestId = 0;
  private pendingRequests = new Map<
    string,
    { resolve: (value: unknown) => void; reject: (error: Error) => void }
  >();
  private buffer = "";

  /**
   * 连接到 Python Server
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      // 启动 Python Server
      this.process = spawn("python", ["-m", "nano_code.server.rpc"], {
        stdio: ["pipe", "pipe", "pipe"],
      });

      // 处理 stdout
      this.process.stdout?.on("data", (data: Buffer) => {
        this.buffer += data.toString();
        this.processBuffer();
      });

      // 处理 stderr (日志)
      this.process.stderr?.on("data", (data: Buffer) => {
        console.error("[Server]", data.toString().trim());
      });

      // 处理错误
      this.process.on("error", (error: Error) => {
        reject(error);
      });

      // 处理退出
      this.process.on("exit", (code) => {
        if (code !== 0 && code !== null) {
          console.error(`Server exited with code ${code}`);
        }
      });

      // 等待服务器启动
      setTimeout(resolve, 100);
    });
  }

  /**
   * 处理响应缓冲区
   */
  private processBuffer(): void {
    const lines = this.buffer.split("\n");
    this.buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const response = JSON.parse(line);

        // 流式通知
        if (response.method === "stream") {
          this.emit("stream", response.params as StreamEvent);
        }
        // 请求响应
        else if (response.id) {
          const pending = this.pendingRequests.get(response.id);
          if (pending) {
            this.pendingRequests.delete(response.id);
            if (response.error) {
              pending.reject(new Error(response.error.message));
            } else {
              pending.resolve(response.result);
            }
          }
        }
      } catch (e) {
        // 忽略解析错误
      }
    }
  }

  /**
   * 发送 JSON-RPC 请求
   */
  async sendRequest<T = unknown>(
    method: string,
    params: Record<string, unknown> = {}
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const id = String(++this.requestId);
      const request: JSONRPCRequest = {
        jsonrpc: "2.0",
        id,
        method,
        params,
      };

      this.pendingRequests.set(id, {
        resolve: resolve as (value: unknown) => void,
        reject,
      });

      this.process?.stdin?.write(JSON.stringify(request) + "\n");

      // 超时
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error("Request timeout"));
        }
      }, 60000);
    });
  }

  /**
   * 流式对话
   */
  async stream(prompt: string, mode: "build" | "plan" = "build"): Promise<void> {
    await this.sendRequest("agent.stream", { prompt, mode });
  }

  /**
   * 获取工具列表
   */
  async getTools(): Promise<Tool[]> {
    const result = await this.sendRequest<{ tools: Tool[] }>("tools.list");
    return result.tools;
  }

  /**
   * 执行工具
   */
  async executeTool(
    name: string,
    args: Record<string, unknown>
  ): Promise<string> {
    const result = await this.sendRequest<{ success: boolean; result?: string; error?: string }>(
      "tool.execute",
      { name, args }
    );
    if (!result.success) {
      throw new Error(result.error || "Tool execution failed");
    }
    return result.result || "";
  }

  /**
   * 获取配置
   */
  async getConfig(): Promise<Config> {
    return this.sendRequest<Config>("config.get");
  }

  /**
   * 设置配置
   */
  async setConfig(config: Partial<Config>): Promise<void> {
    await this.sendRequest("config.set", config);
  }

  /**
   * 关闭连接
   */
  close(): void {
    this.process?.kill();
    this.process = null;
    this.pendingRequests.clear();
  }
}

// 导出单例
let _client: AgentClient | null = null;

export function getAgentClient(): AgentClient {
  if (!_client) {
    _client = new AgentClient();
  }
  return _client;
}
```

### 4. 创建导出文件 (index.ts)

```typescript
export { AgentClient, getAgentClient } from "./rpc.js";
export type {
  JSONRPCRequest,
  JSONRPCResponse,
  StreamEvent,
  StreamEventType,
  Tool,
  Config,
  Message,
  ToolCall,
} from "./types.js";
```

### 5. 编写测试 (tests/client.test.ts)

```typescript
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { AgentClient } from "../src/client/rpc.js";

describe("AgentClient", () => {
  let client: AgentClient;

  beforeAll(async () => {
    client = new AgentClient();
    await client.connect();
  });

  afterAll(() => {
    client.close();
  });

  it("should connect to server", () => {
    expect(client).toBeDefined();
  });

  it("should get tools list", async () => {
    const tools = await client.getTools();
    expect(Array.isArray(tools)).toBe(true);
  });

  it("should get config", async () => {
    const config = await client.getConfig();
    expect(config).toHaveProperty("model");
    expect(config).toHaveProperty("provider");
  });

  it("should handle stream events", async () => {
    const events: any[] = [];
    
    client.on("stream", (event) => {
      events.push(event);
    });

    // 注意: 这个测试需要有效的 API Key
    // await client.stream("hello");
    // expect(events.length).toBeGreaterThan(0);
  });
});
```

## 验证步骤

1. 安装测试依赖:
```bash
cd packages/cli
pnpm add -D vitest
```

2. 运行测试:
```bash
pnpm test
```

3. 手动测试:
```typescript
import { AgentClient } from "./src/client/rpc.js";

const client = new AgentClient();
await client.connect();

client.on("stream", (event) => {
  console.log("Event:", event);
});

const tools = await client.getTools();
console.log("Tools:", tools);

client.close();
```

## 注意事项

1. 确保 Python Server 已经实现 (Task 1.2)
2. 处理好进程启动和清理
3. 处理好 JSON 解析错误

## 预期产出

- `packages/cli/src/client/` 目录下的 3 个文件
- 测试文件
- 测试通过
