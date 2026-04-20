import React from "react";
import { Box, Text } from "ink";

export interface StatusBarProps {
  status: "idle" | "thinking" | "executing" | "error";
  model?: string;
}

export function StatusBar({ status, model = "gpt-4o-mini" }: StatusBarProps) {
  const statusConfig = {
    idle: { color: "gray", text: "Ready" },
    thinking: { color: "yellow", text: "Thinking..." },
    executing: { color: "cyan", text: "Executing..." },
    error: { color: "red", text: "Error" },
  };

  const config = statusConfig[status];

  return (
    <Box marginTop={1} flexDirection="row">
      <Box marginRight={2}>
        <Text dimColor>Model: </Text>
        <Text color="green">{model}</Text>
      </Box>
      <Box>
        <Text dimColor>Status: </Text>
        <Text color={config.color}>{config.text}</Text>
      </Box>
    </Box>
  );
}
