import { useState, useCallback, useEffect } from 'react';
import { spawn, ChildProcess } from 'child_process';
import { EventEmitter } from 'events';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
}

interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result?: string;
}

interface StreamEvent {
  type: 'thinking' | 'tool_call' | 'tool_result' | 'response' | 'done';
  content: string;
  metadata?: {
    toolName?: string;
    toolArgs?: Record<string, unknown>;
  };
}

// JSON-RPC 客户端
class AgentClient extends EventEmitter {
  private process: ChildProcess | null = null;
  private requestId = 0;
  private pendingRequests = new Map<string, { resolve: Function; reject: Function }>();
  
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      // 启动 Python 服务器
      this.process = spawn('python', ['-m', 'nano_code.server.rpc'], {
        stdio: ['pipe', 'pipe', 'pipe'],
      });
      
      this.process.stdout?.on('data', (data) => {
        const lines = data.toString().split('\n');
        lines.forEach((line: string) => {
          if (!line.trim()) return;
          
          try {
            const response = JSON.parse(line);
            
            if (response.method === 'stream') {
              // 流式事件
              this.emit('stream', response.params);
            } else if (response.id) {
              // 请求响应
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
        });
      });
      
      this.process.stderr?.on('data', (data) => {
        console.error('Server error:', data.toString());
      });
      
      this.process.on('error', (error) => {
        reject(error);
      });
      
      // 等待服务器启动
      setTimeout(resolve, 100);
    });
  }
  
  async sendRequest(method: string, params: Record<string, unknown> = {}): Promise<unknown> {
    return new Promise((resolve, reject) => {
      const id = String(++this.requestId);
      const request = {
        jsonrpc: '2.0',
        id,
        method,
        params,
      };
      
      this.pendingRequests.set(id, { resolve, reject });
      this.process?.stdin?.write(JSON.stringify(request) + '\n');
      
      // 超时
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error('Request timeout'));
        }
      }, 60000);
    });
  }
  
  async stream(prompt: string, mode: 'build' | 'plan' = 'build'): Promise<void> {
    await this.sendRequest('agent.stream', { prompt, mode });
  }
  
  async getTools(): Promise<unknown> {
    return this.sendRequest('tools.list');
  }
  
  async getConfig(): Promise<unknown> {
    return this.sendRequest('config.get');
  }
  
  close(): void {
    this.process?.kill();
  }
}

// React Hook
export function useAgent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState<'idle' | 'thinking' | 'executing' | 'error'>('idle');
  const [currentTool, setCurrentTool] = useState<{ name: string; args: Record<string, unknown> } | undefined>();
  const [model, setModel] = useState('gpt-4o-mini');
  
  const client = useState(() => new AgentClient())[0];
  
  // 连接到服务器
  useEffect(() => {
    client.connect().then(async () => {
      const config = await client.getConfig() as { model?: string };
      if (config?.model) {
        setModel(config.model);
      }
    });
    
    // 监听流式事件
    client.on('stream', (event: StreamEvent) => {
      switch (event.type) {
        case 'thinking':
          setStatus('thinking');
          break;
        
        case 'tool_call':
          setStatus('executing');
          setCurrentTool({
            name: event.metadata?.toolName || 'unknown',
            args: event.metadata?.toolArgs || {},
          });
          break;
        
        case 'tool_result':
          setCurrentTool(undefined);
          break;
        
        case 'response':
          setMessages(prev => {
            const last = prev[prev.length - 1];
            if (last?.role === 'assistant') {
              // 追加到上一条消息
              return [...prev.slice(0, -1), { ...last, content: last.content + event.content }];
            }
            // 新消息
            return [...prev, {
              role: 'assistant' as const,
              content: event.content,
              timestamp: new Date(),
            }];
          });
          break;
        
        case 'done':
          setIsStreaming(false);
          setStatus('idle');
          setCurrentTool(undefined);
          break;
      }
    });
    
    return () => {
      client.close();
    };
  }, [client]);
  
  const sendMessage = useCallback(async (prompt: string) => {
    // 添加用户消息
    setMessages(prev => [...prev, {
      role: 'user',
      content: prompt,
      timestamp: new Date(),
    }]);
    
    setIsStreaming(true);
    setStatus('thinking');
    
    try {
      await client.stream(prompt);
    } catch (error) {
      setStatus('error');
      setIsStreaming(false);
      console.error('Error:', error);
    }
  }, [client]);
  
  return {
    messages,
    sendMessage,
    isStreaming,
    status,
    currentTool,
    model,
  };
}
