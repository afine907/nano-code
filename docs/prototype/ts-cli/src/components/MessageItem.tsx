import React from 'react';
import { Box, Text } from 'ink';
import { Markdown } from './Markdown.js';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface MessageItemProps {
  message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  
  return (
    <Box flexDirection="column" marginBottom={1}>
      {/* 角色标识 */}
      <Box>
        {isUser && <Text bold color="green">You:</Text>}
        {isAssistant && <Text bold color="blue">Assistant:</Text>}
        {message.role === 'system' && <Text bold color="yellow">System:</Text>}
        <Text dimColor> {message.timestamp.toLocaleTimeString()}</Text>
      </Box>
      
      {/* 消息内容 */}
      <Box marginLeft={2} flexDirection="column">
        {isAssistant ? (
          <Markdown content={message.content} />
        ) : (
          <Text>{message.content}</Text>
        )}
      </Box>
    </Box>
  );
}
