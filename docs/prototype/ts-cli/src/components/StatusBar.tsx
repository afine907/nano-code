import React from 'react';
import { Box, Text } from 'ink';

interface StatusBarProps {
  status: 'idle' | 'thinking' | 'executing' | 'error';
}

export function StatusBar({ status }: StatusBarProps) {
  const statusConfig = {
    idle: { color: 'gray', text: 'Ready' },
    thinking: { color: 'yellow', text: 'Thinking...' },
    executing: { color: 'cyan', text: 'Executing...' },
    error: { color: 'red', text: 'Error' },
  };
  
  const config = statusConfig[status];
  
  return (
    <Box marginTop={1}>
      <Text dimColor>Status: </Text>
      <Text color={config.color}>{config.text}</Text>
    </Box>
  );
}
