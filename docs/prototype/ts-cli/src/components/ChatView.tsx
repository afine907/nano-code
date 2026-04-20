import React from 'react';
import { Box, Text } from 'ink';
import { MessageItem } from './MessageItem.js';
import { ToolExecution } from './ToolExecution.js';

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

interface ChatViewProps {
  messages: Message[];
  isStreaming: boolean;
  currentTool?: { name: string; args: Record<string, unknown> };
}

export function ChatView({ messages, isStreaming, currentTool }: ChatViewProps) {
  return (
    <Box flexDirection="column" flexGrow={1}>
      {messages.length === 0 ? (
        <Box flexDirection="column" alignItems="center" justifyContent="center" flexGrow={1}>
          <Text dimColor>Welcome to Nano Code!</Text>
          <Text dimColor>Ask me anything about your code.</Text>
        </Box>
      ) : (
        messages.map((msg, idx) => (
          <MessageItem key={idx} message={msg} />
        ))
      )}
      
      {isStreaming && currentTool && (
        <ToolExecution tool={currentTool} />
      )}
    </Box>
  );
}
