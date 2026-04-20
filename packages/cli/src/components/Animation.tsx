import React from "react";
import { Box, Text } from "ink";
import Spinner from "ink-spinner";

export interface ToolExecutionProps {
  toolName: string;
  args?: Record<string, unknown>;
}

export function ToolExecution({ toolName, args }: ToolExecutionProps) {
  // 格式化参数显示
  const formatArgs = (args?: Record<string, unknown>): string => {
    if (!args) return "";

    const entries = Object.entries(args);
    if (entries.length === 0) return "";

    const displayEntries = entries.slice(0, 3);
    const formatted = displayEntries
      .map(([key, value]) => {
        const valueStr =
          typeof value === "string"
            ? value.length > 30
              ? value.slice(0, 30) + "..."
              : value
            : JSON.stringify(value);
        return `${key}=${valueStr}`;
      })
      .join(", ");

    if (entries.length > 3) {
      return `${formatted}, ...`;
    }
    return formatted;
  };

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="yellow"
      paddingX={1}
      marginBottom={1}
    >
      {/* 工具名称 + 加载动画 */}
      <Box>
        <Text color="yellow">
          <Spinner type="dots" />
        </Text>
        <Text> </Text>
        <Text bold color="cyan">
          {toolName}
        </Text>
      </Box>

      {/* 参数显示 */}
      {args && Object.keys(args).length > 0 && (
        <Box marginLeft={2}>
          <Text dimColor>{formatArgs(args)}</Text>
        </Box>
      )}
    </Box>
  );
}

export interface ThinkingIndicatorProps {
  message?: string;
}

export function ThinkingIndicator({
  message = "Thinking",
}: ThinkingIndicatorProps) {
  return (
    <Box>
      <Text color="cyan">
        <Spinner type="dots" />
      </Text>
      <Text dimColor> {message}...</Text>
    </Box>
  );
}
