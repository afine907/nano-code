import React from "react";
import { Box, Text } from "ink";

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
}

export interface MessageItemProps {
  message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  // 角色颜色
  const roleColor = isUser ? "green" : isAssistant ? "blue" : "yellow";
  const roleLabel = isUser ? "You" : isAssistant ? "Assistant" : "System";

  return (
    <Box flexDirection="column" marginBottom={1}>
      {/* 角色和时间 */}
      <Box>
        <Text bold color={roleColor}>
          {roleLabel}:
        </Text>
        <Text dimColor> {message.timestamp.toLocaleTimeString()}</Text>
      </Box>

      {/* 消息内容 */}
      <Box marginLeft={2} flexDirection="column">
        {message.content.split("\n").map((line, idx) => (
          <Text key={idx}>{line}</Text>
        ))}
      </Box>
    </Box>
  );
}
