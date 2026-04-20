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
