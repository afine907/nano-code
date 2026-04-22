import React, { useState } from 'react';
import { Box, Text, useInput, useApp } from 'ink';
import type { Mode } from '../app.js';

interface InputBoxProps {
  onSubmit: (input: string) => void;
  disabled: boolean;
  mode: Mode;
  onToggleMode: () => void;
  model: string;
}

export function InputBox({ onSubmit, disabled, mode, onToggleMode, model }: InputBoxProps) {
  const { exit } = useApp();
  const [input, setInput] = useState('');
  const [lines, setLines] = useState<string[]>([]);
  
  const isRawModeSupported = Boolean(process.stdin.isTTY);

  useInput((char, key) => {
    if (disabled) return;

    if (key.ctrl && char === 'c') {
      exit();
      return;
    }

    // Enter 提交
    if (key.return && !key.shift) {
      const allLines = [...lines, input].filter(l => l.trim());
      if (allLines.length > 0) {
        onSubmit(allLines.join('\n'));
        setInput('');
        setLines([]);
      }
      return;
    }

    // Tab 换行
    if (key.tab) {
      if (input.trim() || lines.length > 0) {
        setLines([...lines, input]);
        setInput('');
      }
      return;
    }

    // Escape 取消
    if (key.escape) {
      setLines([]);
      setInput('');
      return;
    }

    // Backspace
    if (key.backspace || key.delete) {
      if (input === '' && lines.length > 0) {
        const newLines = [...lines];
        setInput(newLines.pop() || '');
        setLines(newLines);
      } else {
        setInput(prev => prev.slice(0, -1));
      }
      return;
    }

    // 普通字符
    if (char && !key.ctrl && !key.meta) {
      setInput(prev => prev + char);
    }
  }, { isActive: isRawModeSupported });

  const modeIcon = mode === 'plan' ? '📋' : '🦞';
  const isMultiline = lines.length > 0;

  return (
    <Box flexDirection="column" paddingX={1}>
      {/* 多行模式提示 */}
      {isMultiline && (
        <Box marginBottom={0}>
          {lines.map((line, i) => (
            <Box key={i}>
              <Text dimColor>  {line}</Text>
            </Box>
          ))}
        </Box>
      )}
      
      {/* 输入行 */}
      <Box>
        <Text bold color={mode === 'plan' ? 'magenta' : 'cyan'}>
          {modeIcon}
        </Text>
        <Text> {input}</Text>
        {disabled && <Text dimColor> ...</Text>}
        {!input && !isMultiline && !disabled && (
          <Text dimColor> (Tab 换行, /help 命令)</Text>
        )}
        <Text color="cyan">▌</Text>
      </Box>
      
      {/* 底部状态 */}
      <Box marginTop={0}>
        <Text dimColor>
          {mode.toUpperCase()} · {model}
        </Text>
      </Box>
    </Box>
  );
}
