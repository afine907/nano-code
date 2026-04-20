import React from 'react';
import { Text } from 'ink';
import chalk from 'chalk';

interface MarkdownProps {
  content: string;
}

// 简化的 Markdown 渲染
// 生产环境建议使用 marked-terminal
export function Markdown({ content }: MarkdownProps) {
  // 处理代码块
  const renderContent = (text: string): React.ReactNode[] => {
    const lines = text.split('\n');
    const result: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeContent: string[] = [];
    let codeLang = '';
    
    lines.forEach((line, idx) => {
      if (line.startsWith('```')) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeLang = line.slice(3);
          codeContent = [];
        } else {
          inCodeBlock = false;
          result.push(
            <Text key={idx} color="cyan" backgroundColor="gray">
              {codeContent.join('\n')}
            </Text>
          );
        }
      } else if (inCodeBlock) {
        codeContent.push(line);
      } else if (line.startsWith('# ')) {
        result.push(<Text key={idx} bold>{line.slice(2)}</Text>);
      } else if (line.startsWith('**') && line.endsWith('**')) {
        result.push(<Text key={idx} bold>{line.slice(2, -2)}</Text>);
      } else if (line.startsWith('- ')) {
        result.push(<Text key={idx} dimColor>  • {line.slice(2)}</Text>);
      } else {
        result.push(<Text key={idx}>{line}</Text>);
      }
    });
    
    return result;
  };
  
  return <>{renderContent(content)}</>;
}
