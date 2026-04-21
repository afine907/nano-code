import React, { useState, useCallback } from 'react';
import { Box, Text, useApp, useInput } from 'ink';
import { ChatView } from './components/ChatView.js';
import { InputBox } from './components/InputBox.js';
import { StatusBar } from './components/StatusBar.js';
import { useAgent } from './hooks/useAgent.js';

export type Mode = 'plan' | 'build';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: ToolCall[];
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  status: 'pending' | 'running' | 'completed' | 'error';
  result?: string;
}

export function App() {
  const { exit } = useApp();
  const [mode, setMode] = useState<Mode>('build');
  
  const {
    messages,
    isLoading,
    model,
    toolCalls,
    sessionStats,
    sendMessage,
    clearHistory,
  } = useAgent();

  const handleSubmit = useCallback(async (input: string) => {
    if (input.startsWith('/')) {
      handleCommand(input);
      return;
    }
    await sendMessage(input);
  }, [sendMessage]);

  const handleCommand = (cmd: string) => {
    const command = cmd.trim().toLowerCase();
    
    switch (command) {
      case '/help':
        break;
      case '/clear':
        clearHistory();
        break;
      case '/mode':
        setMode(m => m === 'plan' ? 'build' : 'plan');
        break;
      case '/exit':
      case '/quit':
        exit();
        break;
      default:
        break;
    }
  };

  // 切换模式
  const toggleMode = useCallback(() => {
    setMode(m => m === 'plan' ? 'build' : 'plan');
  }, []);

  return (
    <Box flexDirection="column" height="100%">
      {/* 欢迎信息 */}
      <Box borderStyle="round" borderColor="blue" paddingX={1}>
        <Text bold color="blue">
          🤖 jojo-Code - 编码助手
        </Text>
      </Box>
      
      {/* 主聊天区域 */}
      <Box flexGrow={1} flexDirection="column">
        <ChatView messages={messages} isLoading={isLoading} />
      </Box>
      
      {/* 工具执行状态 */}
      {toolCalls.length > 0 && (
        <Box borderStyle="single" borderColor="yellow" paddingX={1}>
          <Text color="yellow">
            ⚡ 执行工具: {toolCalls.map(t => t.name).join(', ')}
          </Text>
        </Box>
      )}
      
      {/* 输入框 */}
      <InputBox 
        onSubmit={handleSubmit} 
        disabled={isLoading}
        mode={mode}
      />
      
      {/* 状态栏 */}
      <StatusBar
        mode={mode}
        model={model}
        messages={messages.length}
        tools={toolCalls.length}
        duration={sessionStats.duration}
      />
    </Box>
  );
}
