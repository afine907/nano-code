import React from 'react';
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';

interface ToolExecutionProps {
  tool: {
    name: string;
    args: Record<string, unknown>;
  };
}

export function ToolExecution({ tool }: ToolExecutionProps) {
  return (
    <Box flexDirection="column" borderStyle="round" borderColor="yellow" paddingX={1}>
      <Box>
        <Text color="yellow">
          <Spinner type="dots" />
        </Text>
        <Text> 执行工具: </Text>
        <Text bold color="cyan">{tool.name}</Text>
      </Box>
      <Box marginLeft={2}>
        <Text dimColor>
          {JSON.stringify(tool.args, null, 2).slice(0, 100)}...
        </Text>
      </Box>
    </Box>
  );
}
