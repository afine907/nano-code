import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';
import TextInput from 'ink-text-input';

interface InputBoxProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export function InputBox({ value, onChange, onSubmit, disabled, placeholder }: InputBoxProps) {
  const [multiline, setMultiline] = useState(false);
  const [lines, setLines] = useState<string[]>([]);
  
  // 全局快捷键
  useInput((input, key) => {
    // Ctrl+C 退出
    if (key.ctrl && input === 'c') {
      process.exit(0);
    }
    
    // Enter 提交（非多行模式）
    if (key.return && !multiline && !disabled) {
      onSubmit();
    }
    
    // 多行模式下的 Enter 添加新行
    if (key.return && multiline && !disabled) {
      setLines([...lines, value]);
      onChange('');
    }
    
    // Ctrl+D 切换多行模式
    if (key.ctrl && input === 'd') {
      setMultiline(!multiline);
    }
  });
  
  return (
    <Box flexDirection="column">
      {/* 多行提示 */}
      {multiline && (
        <Box marginBottom={1}>
          <Text dimColor>
            多行模式 (Ctrl+D 退出)
          </Text>
          {lines.map((line, idx) => (
            <Text key={idx} dimColor>{`>>> ${line}`}</Text>
          ))}
        </Box>
      )}
      
      {/* 输入框 */}
      <Box borderStyle="round" borderColor={disabled ? "gray" : "cyan"} paddingX={1}>
        <Text dimColor>{multiline ? '>>> ' : '> '}</Text>
        <TextInput
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          showCursor={!disabled}
        />
      </Box>
      
      {/* 提示 */}
      <Box marginTop={1}>
        <Text dimColor>
          Enter 发送 {multiline ? '| Ctrl+D 切换单行' : '| Ctrl+D 切换多行'}
        </Text>
      </Box>
    </Box>
  );
}
