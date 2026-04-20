import React from "react";
import { Text, Box } from "ink";

export interface MarkdownProps {
  content: string;
}

/**
 * Markdown 渲染组件
 */
export function Markdown({ content }: MarkdownProps) {
  // 按行分割处理
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];

  let inCodeBlock = false;
  let codeContent: string[] = [];
  let codeLang = "";
  let codeKey = 0;

  lines.forEach((line, idx) => {
    // 代码块开始/结束
    if (line.startsWith("```")) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeLang = line.slice(3).trim();
        codeContent = [];
      } else {
        inCodeBlock = false;
        const code = codeContent.join("\n");

        elements.push(
          <Box
            key={`code-${codeKey++}`}
            flexDirection="column"
            borderStyle="round"
            borderColor="gray"
            paddingX={1}
            marginBottom={1}
          >
            {codeLang && <Text dimColor>{codeLang}</Text>}
            <Text color="cyan">{code}</Text>
          </Box>
        );

        codeContent = [];
        codeLang = "";
      }
      return;
    }

    // 代码块内容
    if (inCodeBlock) {
      codeContent.push(line);
      return;
    }

    // 空行
    if (!line.trim()) {
      elements.push(<Text key={`empty-${idx}`}> </Text>);
      return;
    }

    // 标题
    if (line.startsWith("### ")) {
      elements.push(
        <Text key={idx} bold color="cyan">
          {line.slice(4)}
        </Text>
      );
      return;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <Text key={idx} bold color="green">
          {line.slice(3)}
        </Text>
      );
      return;
    }
    if (line.startsWith("# ")) {
      elements.push(
        <Text key={idx} bold color="white">
          {line.slice(2)}
        </Text>
      );
      return;
    }

    // 列表项
    if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push(
        <Text key={idx} dimColor>{`  • ${line.slice(2)}`}</Text>
      );
      return;
    }

    // 普通文本
    elements.push(<Text key={idx}>{line}</Text>);
  });

  return <Box flexDirection="column">{elements}</Box>;
}
