import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';
import type { Mode } from '../app.js';

interface InputBoxProps {
  onSubmit: (input: string) => void;
  disabled: boolean;
  mode: Mode;
  onToggleMode: () => void;
}

export function InputBox({ onSubmit, disabled, mode, onToggleMode }: InputBoxProps) {
  const [input, setInput] = useState('');
  const [lines, setLines] = useState<string[]>([]);

  useInput((char, key) => {
    if (disabled) return;

    // Enter 提交 (Shift+Enter 换行在 terminal 中很难检测，用 Tab 代替)
    if (key.return && !key.shift) {
      // 合并所有行
      const allLines = [...lines, input].filter(l => l.trim());
      if (allLines.length > 0) {
        onSubmit(allLines.join('\n'));
        setInput('');
        setLines([]);
      }
      return;
    }

    // Shift+Enter 或 Tab 换行
    if ((key.return && key.shift) || key.tab) {
      if (input.trim() || lines.length > 0) {
        setLines([...lines, input]);
        setInput('');
      }
      return;
    }

    // Escape 取消多行输入
    if (key.escape) {
      if (lines.length > 0 || input) {
        setLines([]);
        setInput('');
      }
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
  });

  const promptIcon = mode === 'plan' ? '📋' : '🦞';
  const isMultiline = lines.length > 0;

  return (
    <Box flexDirection="column" borderStyle="single" borderColor="gray" paddingX={1}>
      {/* 多行提示 */}
      {isMultiline && (
        <Box>
          <Text color="yellow" dimColor>
            📝 多行输入 (Enter提交, Tab换行, Esc取消)
          </Text>
        </Box>
      )}
      
      {/* 已输入的行 */}
      {lines.length > 0 && (
        <Box flexDirection="column">
          {lines.map((line, i) => (
            <Text key={i} dimColor>{`  ${i + 1}: ${line}`}</Text>
          ))}
        </Box>
      )}
      
      {/* 当前行 */}
      <Box>
        <Text bold color="cyan">{promptIcon} </Text>
        {isMultiline && <Text dimColor>{`${lines.length + 1}: `}</Text>}
        <Text>{input}</Text>
        {!input && !isMultiline && (
          <Text dimColor>(Enter提交, Tab换行, /mode 切换模式)</Text>
        )}
        <Text backgroundColor="cyan"> </Text>
      </Box>
      
      {disabled && <Text dimColor>处理中...</Text>}
    </Box>
  );
}
