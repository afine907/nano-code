import { useState, useEffect, useCallback } from 'react';
import type { Message, ToolCall } from '../app.js';
import { JsonRpcClient } from '../client/jsonrpc.js';

interface UseAgentReturn {
  messages: Message[];
  isLoading: boolean;
  model: string;
  toolCalls: ToolCall[];
  sessionStats: {
    duration: number;
    totalToolCalls: number;
  };
  sendMessage: (input: string) => Promise<void>;
  clearHistory: () => void;
}

export function useAgent(): UseAgentReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [model, setModel] = useState('gpt-4o-mini');
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [startTime] = useState(Date.now());
  
  const client = useState(() => new JsonRpcClient())[0];

  // 获取当前模型
  useEffect(() => {
    client.request<{ model: string }>('get_model', {}).then(result => {
      if (result && result.model) setModel(result.model);
    }).catch(() => {
      // 使用默认模型
    });
  }, [client]);

  const sendMessage = useCallback(async (input: string) => {
    console.log('[DEBUG] sendMessage called with:', input);
    
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    console.log('[DEBUG] Adding user message');
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setToolCalls([]);

    try {
      console.log('[DEBUG] Calling client.request');
      // 使用同步请求（暂时不用流式）
      const result = await client.request<{ content: string }>('chat', { message: input });
      console.log('[DEBUG] Got result:', result);
      
      const assistantMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: result?.content || 'No response',
        timestamp: new Date(),
      };

      console.log('[DEBUG] Adding assistant message');
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('[DEBUG] Error:', error);
      const errorMessage: Message = {
        id: `msg-${Date.now() + 2}`,
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      console.log('[DEBUG] Setting isLoading to false');
      setIsLoading(false);
      setToolCalls([]);
    }
  }, [client]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    client.request('clear', {}).catch(() => {});
  }, [client]);

  const duration = Math.floor((Date.now() - startTime) / 1000);

  return {
    messages,
    isLoading,
    model,
    toolCalls,
    sessionStats: {
      duration,
      totalToolCalls: messages.reduce(
        (sum, m) => sum + (m.toolCalls?.length || 0),
        0
      ),
    },
    sendMessage,
    clearHistory,
  };
}
