import React from "react";
import { Box, Text } from "ink";
import { MessageItem, Message } from "./MessageItem.js";

export interface ChatViewProps {
  messages: Message[];
  isStreaming: boolean;
}

export function ChatView({ messages, isStreaming }: ChatViewProps) {
  if (messages.length === 0) {
    return (
      <Box
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        flexGrow={1}
      >
        <Text dimColor>Welcome to Nano Code!</Text>
        <Text dimColor>Ask me anything about your code.</Text>
        <Text dimColor></Text>
        <Text dimColor>Commands: /help, /exit, /clear</Text>
      </Box>
    );
  }

  return (
    <Box flexDirection="column" flexGrow={1}>
      {messages.map((msg, idx) => (
        <MessageItem key={idx} message={msg} />
      ))}

      {isStreaming && (
        <Box>
          <Text dimColor>Thinking...</Text>
        </Box>
      )}
    </Box>
  );
}
