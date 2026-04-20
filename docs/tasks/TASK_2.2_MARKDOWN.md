# Task 2.2: Markdown 渲染组件

## 背景
我们需要在 CLI 中渲染 Markdown 内容，包括代码高亮。

## 前置依赖
- Task 1.1 已完成 (monorepo 结构已创建)

## 目标
实现 Markdown 组件，支持标题、粗体、列表、代码块、语法高亮。

## 任务步骤

### 1. 安装依赖

```bash
cd packages/cli
pnpm add marked highlight.js
```

### 2. 实现 Markdown.tsx

```tsx
import React from "react";
import { Text, Box } from "ink";
import { marked } from "marked";
import hljs from "highlight.js";

export interface MarkdownProps {
  content: string;
}

// ANSI 颜色映射
const COLORS: Record<string, string> = {
  keyword: "magenta",
  string: "green",
  number: "yellow",
  comment: "gray",
  function: "cyan",
  class: "blue",
  variable: "white",
  default: "white",
};

/**
 * 对代码进行语法高亮
 */
function highlightCode(code: string, lang: string): string {
  try {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  } catch {
    return code;
  }
}

/**
 * 将 HTML 转换为 ANSI 颜色文本
 */
function htmlToAnsi(html: string): string {
  // 简化处理：移除 HTML 标签
  return html
    .replace(/<span class="hljs-(\w+)">/g, "")
    .replace(/<\/span>/g, "");
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
        // 开始代码块
        inCodeBlock = true;
        codeLang = line.slice(3).trim();
        codeContent = [];
      } else {
        // 结束代码块
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
            {codeLang && (
              <Text dimColor>{codeLang}</Text>
            )}
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
        <Text key={idx} dimColor>
          {`  • ${line.slice(2)}`}
        </Text>
      );
      return;
    }

    // 数字列表
    const numMatch = line.match(/^(\d+)\.\s/);
    if (numMatch) {
      elements.push(
        <Text key={idx}>
          {`  ${numMatch[1]}. ${line.slice(numMatch[0].length)}`}
        </Text>
      );
      return;
    }

    // 行内代码
    if (line.includes("`")) {
      const parts = line.split(/`([^`]+)`/);
      const children = parts.map((part, i) => {
        if (i % 2 === 1) {
          return (
            <Text key={i} color="yellow" backgroundColor="gray">
              {` ${part} `}
            </Text>
          );
        }
        // 处理粗体
        if (part.includes("**")) {
          const boldParts = part.split(/\*\*([^*]+)\*\*/);
          return boldParts.map((bp, j) => {
            if (j % 2 === 1) {
              return (
                <Text key={`${i}-${j}`} bold>
                  {bp}
                </Text>
              );
            }
            return <Text key={`${i}-${j}`}>{bp}</Text>;
          });
        }
        return <Text key={i}>{part}</Text>;
      });
      
      elements.push(
        <Text key={idx}>{children}</Text>
      );
      return;
    }

    // 粗体
    if (line.includes("**")) {
      const parts = line.split(/\*\*([^*]+)\*\*/);
      elements.push(
        <Text key={idx}>
          {parts.map((part, i) => {
            if (i % 2 === 1) {
              return (
                <Text key={i} bold>
                  {part}
                </Text>
              );
            }
            return <Text key={i}>{part}</Text>;
          })}
        </Text>
      );
      return;
    }

    // 普通文本
    elements.push(<Text key={idx}>{line}</Text>);
  });

  return <Box flexDirection="column">{elements}</Box>;
}
```

### 3. 更新 components/index.ts

```tsx
export { Markdown } from "./Markdown.js";
export type { MarkdownProps } from "./Markdown.js";
```

### 4. 测试

创建 `tests/markdown.test.tsx`:

```tsx
import React from "react";
import { render } from "ink-testing-library";
import { Markdown } from "../src/components/Markdown.js";

describe("Markdown", () => {
  it("should render headings", () => {
    const { lastFrame } = render(
      <Markdown content="# Title\n## Subtitle\n### Sub-subtitle" />
    );
    
    expect(lastFrame()).toContain("Title");
    expect(lastFrame()).toContain("Subtitle");
    expect(lastFrame()).toContain("Sub-subtitle");
  });

  it("should render code blocks", () => {
    const { lastFrame } = render(
      <Markdown content="```python\nprint('hello')\n```" />
    );
    
    expect(lastFrame()).toContain("python");
    expect(lastFrame()).toContain("print('hello')");
  });

  it("should render inline code", () => {
    const { lastFrame } = render(
      <Markdown content="Use `nano-code` to start" />
    );
    
    expect(lastFrame()).toContain("nano-code");
  });

  it("should render lists", () => {
    const { lastFrame } = render(
      <Markdown content="- Item 1\n- Item 2" />
    );
    
    expect(lastFrame()).toContain("Item 1");
    expect(lastFrame()).toContain("Item 2");
  });

  it("should render bold text", () => {
    const { lastFrame } = render(
      <Markdown content="This is **bold** text" />
    );
    
    expect(lastFrame()).toContain("bold");
  });
});
```

## 验证步骤

```bash
pnpm test tests/markdown.test.tsx
```

## 注意事项

1. ink 不支持直接渲染 HTML，需要转换为 Text 组件
2. 语法高亮简化处理，后续可以优化
3. 处理边界情况（嵌套 Markdown）

## 预期产出

- `packages/cli/src/components/Markdown.tsx`
- 测试文件
- 测试通过
