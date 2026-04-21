import { spawn, ChildProcess } from 'child_process';
import { existsSync } from 'fs';
import type { JsonRpcRequest, JsonRpcResponse, StreamChunk } from './types.js';

export class JsonRpcClient {
  private process: ChildProcess | null = null;
  private requestId = 0;
  private pendingRequests = new Map<
    string | number,
    {
      resolve: (value: unknown) => void;
      reject: (error: Error) => void;
    }
  >();
  private buffer = '';

  constructor(
    private pythonPath: string = 'python3',
    private serverModule: string = 'jojo_code.server.main'
  ) {
    // 尝试找到 venv 中的 Python
    const possiblePaths = [
      process.cwd() + '/../../.venv/bin/python3',  // packages/cli -> jojo-code/.venv
      process.cwd() + '/.venv/bin/python3',        // jojo-code/.venv
      '/home/admin/.openclaw/workspace/jojo-code/.venv/bin/python3',  // 绝对路径
    ];
    
    for (const path of possiblePaths) {
      if (existsSync(path)) {
        this.pythonPath = path;
        break;
      }
    }
    this.startServer();
  }

  private startServer() {
    const proc = spawn(this.pythonPath, ['-m', this.serverModule], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    if (!proc.stdout || !proc.stdin || !proc.stderr) {
      throw new Error('Failed to create stdio pipes');
    }

    this.process = proc;

    // 处理 stdout (JSON-RPC 响应)
    proc.stdout.on('data', (data: Buffer) => {
      this.buffer += data.toString();
      this.processBuffer();
    });

    // 处理 stderr (日志)
    proc.stderr.on('data', (data: Buffer) => {
      console.error('[Python]', data.toString());
    });

    // 处理进程退出
    proc.on('close', (code) => {
      console.error(`Python server exited with code ${code}`);
      this.process = null;
    });
  }

  private processBuffer() {
    const lines = this.buffer.split('\n');
    this.buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.trim()) continue;
      
      try {
        const response: JsonRpcResponse = JSON.parse(line);
        const pending = this.pendingRequests.get(response.id);
        
        if (pending) {
          this.pendingRequests.delete(response.id);
          
          if (response.error) {
            pending.reject(new Error(response.error.message));
          } else {
            pending.resolve(response.result);
          }
        }
      } catch (e) {
        console.error('Failed to parse response:', line, e);
      }
    }
  }

  async request<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
    return new Promise((resolve, reject) => {
      const proc = this.process;
      if (!proc?.stdin) {
        reject(new Error('Server not running'));
        return;
      }

      const id = ++this.requestId;
      const request: JsonRpcRequest = {
        jsonrpc: '2.0',
        id,
        method,
        params,
      };

      this.pendingRequests.set(id, {
        resolve: resolve as (value: unknown) => void,
        reject,
      });

      proc.stdin.write(JSON.stringify(request) + '\n');
    });
  }

  async *stream(
    method: string,
    params: Record<string, unknown> = {}
  ): AsyncGenerator<StreamChunk> {
    // 对于流式响应，使用特殊的方法名
    const streamId = `stream-${++this.requestId}`;
    
    // 发送请求
    const proc = this.process;
    if (!proc?.stdin) {
      throw new Error('Server not running');
    }

    const request: JsonRpcRequest = {
      jsonrpc: '2.0',
      id: streamId,
      method,
      params: { ...params, stream: true },
    };

    // 创建队列来收集流式响应
    const queue: StreamChunk[] = [];
    let done = false;
    let resolveNext: ((value: IteratorResult<StreamChunk>) => void) | null = null;

    this.pendingRequests.set(streamId, {
      resolve: (value) => {
        if (resolveNext) {
          const chunk = value as StreamChunk;
          if (chunk.type === 'done') {
            done = true;
            resolveNext({ value: chunk, done: true });
          } else {
            queue.push(chunk);
            resolveNext({ value: chunk, done: false });
          }
          resolveNext = null;
        } else {
          const chunk = value as StreamChunk;
          if (chunk.type !== 'done') {
            queue.push(chunk);
          }
        }
      },
      reject: (error) => {
        done = true;
        queue.push({ type: 'error', message: error.message });
      },
    });

    proc.stdin.write(JSON.stringify(request) + '\n');

    // 返回异步生成器
    while (!done) {
      if (queue.length > 0) {
        yield queue.shift()!;
      } else {
        // 等待新数据
        await new Promise<void>((resolve) => {
          resolveNext = () => resolve();
        });
      }
    }

    // 处理剩余数据
    while (queue.length > 0) {
      yield queue.shift()!;
    }
  }

  close() {
    if (this.process) {
      this.process.kill();
      this.process = null;
    }
  }
}
