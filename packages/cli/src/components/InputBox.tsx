import React from "react";
import { Box, Text, useInput } from "ink";
import TextInput from "ink-text-input";

export interface InputBoxProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export function InputBox({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = "Type a message...",
}: InputBoxProps) {
  // 全局快捷键
  useInput(
    (input, key) => {
      // Enter 提交
      if (key.return && !disabled) {
        onSubmit();
      }
    },
    { isActive: !disabled }
  );

  return (
    <Box flexDirection="column">
      {/* 输入框 */}
      <Box
        borderStyle="round"
        borderColor={disabled ? "gray" : "cyan"}
        paddingX={1}
      >
        <Text dimColor>{"> "}</Text>
        <TextInput
          value={value}
          onChange={onChange}
          placeholder={disabled ? "Thinking..." : placeholder}
          showCursor={!disabled}
        />
      </Box>

      {/* 提示 */}
      <Box marginTop={1}>
        <Text dimColor>Enter 发送 | /help 帮助 | /exit 退出</Text>
      </Box>
    </Box>
  );
}
