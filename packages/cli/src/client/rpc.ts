/**
 * JSON-RPC Client for Nano Code
 *
 * 通过 stdio 与 Python Server 通信
 */

import { spawn, ChildProcess } from "child_process";
import { EventEmitter } from "events";
import type { StreamEvent, Tool, Config } from "./types.js";

interface JSONRPCRequest {
  jsonrpc: "2.0";
  id: string;
  method: string;
  params?: Record<string, unknown>;
}

interface PendingRequest {
  resolve: (value: unknown) => void;
  reject: (error: Error) => void;
}

export class AgentClient extends EventEmitter {
  private process: ChildProcess | null = null;
  private requestId = 0;
  private pendingRequests = new Map<string, PendingRequest>();
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
      } catch {
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
  async executeTool(name: string, args: Record<string, unknown>): Promise<string> {
    const result = await this.sendRequest<
      { success: boolean; result?: string; error?: string }
    >("tool.execute", { name, args });
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
