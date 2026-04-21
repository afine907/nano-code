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
  const [multiline, setMultiline] = useState(false);
  const [lines, setLines] = useState<string[]>([]);

  useInput((char, key) => {
    if (disabled) return;

    // Escape 或 Ctrl+M 切换 Plan/Build 模式
    if (key.escape || (key.ctrl && char === 'm')) {
      onToggleMode();
      return;
    }

    // Tab 切换多行模式 / 提交
    if (key.tab) {
      if (multiline) {
        // 多行模式下，Tab 完成输入
        const finalInput = [...lines, input].filter(l => l.trim()).join('\n');
        if (finalInput.trim()) {
          onSubmit(finalInput);
          setInput('');
          setLines([]);
          setMultiline(false);
        }
      } else {
        // 单行模式下，Tab 切换到多行模式
        setMultiline(true);
      }
      return;
    }

    // Enter
    if (key.return) {
      if (multiline) {
        // 多行模式下，Enter 换行
        setLines([...lines, input]);
        setInput('');
      } else {
        // 单行模式下，Enter 提交
        if (input.trim()) {
          onSubmit(input.trim());
          setInput('');
        }
      }
      return;
    }

    // Backspace
    if (key.backspace || key.delete) {
      if (input === '' && lines.length > 0 && multiline) {
        // 删除最后一行
        const newLines = [...lines];
        setInput(newLines.pop() || '');
        setLines(newLines);
      } else {
        setInput(prev => prev.slice(0, -1));
      }
      return;
    }

    // Ctrl+C 取消多行模式
    if (key.ctrl && char === 'c' && multiline) {
      setMultiline(false);
      setLines([]);
      setInput('');
      return;
    }

    // 普通字符
    if (char && !key.ctrl && !key.meta) {
      setInput(prev => prev + char);
    }
  });

  const promptIcon = mode === 'plan' ? '📋' : '🦞';

  return (
    <Box flexDirection="column" borderStyle="single" borderColor="gray" paddingX={1}>
      {/* 多行模式提示 */}
      {multiline && (
        <Box>
          <Text color="yellow" bold>
            📝 多行模式 (Enter换行, Tab提交, Ctrl+C取消)
          </Text>
        </Box>
      )}
      
      {/* 显示已输入的多行内容 */}
      {lines.length > 0 && (
        <Box flexDirection="column">
          {lines.map((line, i) => (
            <Text key={i} dimColor>{`  ${i + 1}: ${line}`}</Text>
          ))}
        </Box>
      )}
      
      {/* 当前输入行 */}
      <Box>
        <Text bold color="cyan">{promptIcon} </Text>
        <Text dimColor={multiline ? false : true}>
          {multiline ? `${lines.length + 1}: ` : ''}
        </Text>
        <Text>{input}</Text>
        {!input && !multiline && (
          <Text dimColor>(Tab多行, Esc切换模式)</Text>
        )}
        <Text backgroundColor="cyan"> </Text>
      </Box>
      
      {disabled && (
        <Text dimColor>处理中...</Text>
      )}
    </Box>
  );
}
