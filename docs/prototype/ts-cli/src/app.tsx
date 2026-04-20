import React, { useState, useCallback, useEffect } from 'react';
import { Box, Text, useApp } from 'ink';
import { ChatView } from './components/ChatView.js';
import { InputBox } from './components/InputBox.js';
import { StatusBar } from './components/StatusBar.js';
import { useAgent } from './hooks/useAgent.js';

export function App() {
  const {
    messages,
    sendMessage,
    isStreaming,
    status,
    currentTool,
    model
  } = useAgent();
  
  const [input, setInput] = useState('');
  const { exit } = useApp();
  
  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isStreaming) return;
    
    // 处理命令
    if (input.startsWith('/')) {
      const cmd = input.trim().toLowerCase();
      if (cmd === '/exit' || cmd === '/quit') {
        exit();
        return;
      }
      if (cmd === '/clear') {
        // clearMessages();
        setInput('');
        return;
      }
    }
    
    await sendMessage(input);
    setInput('');
  }, [input, isStreaming, sendMessage, exit]);
  
  return (
    <Box flexDirection="column" height="100%" padding={1}>
      {/* 标题 */}
      <Box marginBottom={1}>
        <Text bold color="cyan">
          🤖 Nano Code
        </Text>
        <Text dimColor> v0.1.0</Text>
        <Text dimColor> | </Text>
        <Text color="green">{model}</Text>
      </Box>
      
      {/* 聊天区域 */}
      <Box flexGrow={1} flexDirection="column">
        <ChatView
          messages={messages}
          isStreaming={isStreaming}
          currentTool={currentTool}
        />
      </Box>
      
      {/* 输入框 */}
      <Box marginTop={1}>
        <InputBox
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          disabled={isStreaming}
          placeholder={isStreaming ? "Thinking..." : "Type a message..."}
        />
      </Box>
      
      {/* 状态栏 */}
      <StatusBar status={status} />
    </Box>
  );
}
