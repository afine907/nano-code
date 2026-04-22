import React from 'react';
import { Box, Text } from 'ink';
import type { Message, ToolCall } from '../app.js';

interface ChatViewProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatView({ messages, isLoading }: ChatViewProps) {
  if (messages.length === 0 && !isLoading) {
    return (
      <Box paddingX={1} paddingY={1}>
        <Text dimColor>
          输入问题开始对话，/help 查看命令
        </Text>
      </Box>
    );
  }

  return (
    <Box flexDirection="column" paddingX={1}>
      {messages.map(msg => (
        <MessageItem key={msg.id} message={msg} />
      ))}
      {isLoading && (
        <Box paddingY={1}>
          <Text dimColor>  ○</Text>
        </Box>
      )}
    </Box>
  );
}

function MessageItem({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  
  // 用户消息 - 简洁显示
  if (isUser) {
    return (
      <Box flexDirection="column" marginBottom={1}>
        <Text color="cyan">{message.content}</Text>
      </Box>
    );
  }
  
  // 助手消息
  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text>{message.content}</Text>
      {message.toolCalls && message.toolCalls.length > 0 && (
        <Box paddingLeft={1} marginTop={0}>
          {message.toolCalls.map((tool, i) => (
            <ToolCallItem key={i} tool={tool} />
          ))}
        </Box>
      )}
    </Box>
  );
}

function ToolCallItem({ tool }: { tool: ToolCall }) {
  const statusIcon = {
    pending: '○',
    running: '◐',
    completed: '●',
    error: '✗',
  }[tool.status];

  return (
    <Box>
      <Text dimColor>
        {statusIcon} {tool.name}
      </Text>
    </Box>
  );
}
