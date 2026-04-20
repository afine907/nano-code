# Nano Code CLI 重构方案：TypeScript + ink

## 目标

将 CLI 层从 Python (rich + prompt_toolkit) 迁移到 TypeScript (ink)，实现与 Claude Code 对齐的交互体验。

## 当前架构

```
┌─────────────────────────────────────────────────────────┐
│                    Python CLI (rich)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  Input      │  │  Output     │  │  Streaming      │  │
│  │  (prompt_   │  │  (rich)     │  │  (手动实现)     │  │
│  │  toolkit)   │  │             │  │                 │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Python Core (不变)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  Agent      │  │  Tools      │  │  LLM            │  │
│  │  (LangGraph)│  │  (Registry) │  │  (LangChain)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 目标架构

```
┌─────────────────────────────────────────────────────────┐
│                  TypeScript CLI (ink)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  Input      │  │  Output     │  │  Streaming      │  │
│  │  (ink Input)│  │  (ink React)│  │  (原生支持)     │  │
│  │  多行编辑   │  │  原地更新   │  │  实时渲染       │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ JSON-RPC over stdio
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 Python Server (新增)                    │
│  ┌─────────────────────────────────────────────────┐    │
│  │  JSON-RPC Server                                │    │
│  │  - stream(prompt) -> AsyncIterator              │    │
│  │  - execute_tool(name, args) -> result           │    │
│  │  - get_tools() -> Tool[]                        │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Python Core (不变)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  Agent      │  │  Tools      │  │  LLM            │  │
│  │  (LangGraph)│  │  (Registry) │  │  (LangChain)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 技术选型

### TypeScript CLI 层

| 组件 | 技术 | 说明 |
|------|------|------|
| 框架 | ink 4.x | React for CLI |
| 输入 | ink-text-input | 多行输入 |
| 输出 | ink-box, ink-spinner | 组件化输出 |
| Markdown | marked-terminal | Markdown 渲染 |
| 语法高亮 | highlight.js | 代码高亮 |
| 通信 | JSON-RPC 2.0 | over stdio |
| 运行时 | Node.js 20+ | 或 Bun |

### Python Server 层

| 组件 | 技术 | 说明 |
|------|------|------|
| 通信 | jsonrpcserver | JSON-RPC 2.0 |
| 异步 | asyncio | 异步流式输出 |
| 序列化 | orjson | 高性能 JSON |

## 新目录结构

```
nano-code/
├── packages/
│   ├── cli/                    # TypeScript CLI
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── src/
│   │   │   ├── index.ts        # 入口
│   │   │   ├── app.tsx         # ink App 组件
│   │   │   ├── components/
│   │   │   │   ├── ChatView.tsx      # 聊天界面
│   │   │   │   ├── MessageList.tsx   # 消息列表
│   │   │   │   ├── InputBox.tsx      # 多行输入框
│   │   │   │   ├── StatusBar.tsx     # 状态栏
│   │   │   │   ├── ToolExecution.tsx # 工具执行动画
│   │   │   │   └── Markdown.tsx      # Markdown 渲染
│   │   │   ├── hooks/
│   │   │   │   ├── useAgent.ts       # Agent 连接
│   │   │   │   └── useConfig.ts      # 配置管理
│   │   │   ├── client/
│   │   │   │   └── rpc.ts            # JSON-RPC 客户端
│   │   │   └── types/
│   │   │       └── index.ts          # 类型定义
│   │   └── README.md
│   │
│   └── core/                    # Python Core (原 src/)
│       ├── pyproject.toml
│       ├── nano_code/
│       │   ├── __init__.py
│       │   ├── server/          # 新增
│       │   │   ├── __init__.py
│       │   │   ├── rpc.py       # JSON-RPC Server
│       │   │   └── protocol.py  # 协议定义
│       │   ├── agent/           # 保持不变
│       │   ├── tools/           # 保持不变
│       │   ├── core/            # 保持不变
│       │   └── context/         # 保持不变
│       └── tests/
│
├── package.json                 # Monorepo 根
├── pnpm-workspace.yaml
├── tsconfig.base.json
└── README.md
```

## 核心 API 设计

### JSON-RPC 接口

```typescript
// 请求
interface Request {
  jsonrpc: "2.0";
  id: string;
  method: string;
  params: Record<string, unknown>;
}

// 响应
interface Response<T> {
  jsonrpc: "2.0";
  id: string;
  result?: T;
  error?: { code: number; message: string; data?: unknown };
}

// 方法定义
interface Methods {
  // 流式对话
  "agent.stream": {
    params: { prompt: string; mode?: "build" | "plan" };
    result: AsyncIterator<StreamEvent>;
  };
  
  // 执行工具
  "tool.execute": {
    params: { name: string; args: Record<string, unknown> };
    result: { success: boolean; result: string };
  };
  
  // 获取工具列表
  "tools.list": {
    params: {};
    result: { tools: Tool[] };
  };
  
  // 获取配置
  "config.get": {
    params: {};
    result: { model: string; provider: string };
  };
  
  // 设置配置
  "config.set": {
    params: { model?: string; apiKey?: string; baseUrl?: string };
    result: { success: boolean };
  };
}

// 流式事件
interface StreamEvent {
  type: "thinking" | "tool_call" | "tool_result" | "response" | "done";
  content: string;
  metadata?: {
    toolName?: string;
    toolArgs?: Record<string, unknown>;
    duration?: number;
  };
}
```

### TypeScript 组件示例

```tsx
// packages/cli/src/app.tsx
import React, { useState, useCallback } from 'react';
import { Box, Text, useApp } from 'ink';
import { ChatView } from './components/ChatView';
import { InputBox } from './components/InputBox';
import { StatusBar } from './components/StatusBar';
import { useAgent } from './hooks/useAgent';

export function App() {
  const { messages, sendMessage, isStreaming, status } = useAgent();
  const [input, setInput] = useState('');
  
  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isStreaming) return;
    await sendMessage(input);
    setInput('');
  }, [input, isStreaming, sendMessage]);
  
  return (
    <Box flexDirection="column" height="100%">
      <ChatView messages={messages} isStreaming={isStreaming} />
      <InputBox
        value={input}
        onChange={setInput}
        onSubmit={handleSubmit}
        disabled={isStreaming}
      />
      <StatusBar status={status} />
    </Box>
  );
}
```

```tsx
// packages/cli/src/components/ChatView.tsx
import React from 'react';
import { Box, Text } from 'ink';
import { MessageList } from './MessageList';
import { ToolExecution } from './ToolExecution';

export function ChatView({ messages, isStreaming }) {
  return (
    <Box flexDirection="column" flexGrow={1} overflowY="auto">
      <MessageList messages={messages} />
      {isStreaming && <ToolExecution />}
    </Box>
  );
}
```

```tsx
// packages/cli/src/components/InputBox.tsx
import React, { useState } from 'react';
import { Box, Text, useInput } from 'ink';
import TextInput from 'ink-text-input';

export function InputBox({ value, onChange, onSubmit, disabled }) {
  const [multiline, setMultiline] = useState(false);
  const [lines, setLines] = useState<string[]>([]);
  
  useInput((input, key) => {
    if (key.return && !multiline) {
      onSubmit();
    } else if (key.return && multiline) {
      setLines([...lines, value]);
      onChange('');
    } else if (key.escape) {
      setMultiline(!multiline);
    }
  });
  
  return (
    <Box borderStyle="round" borderColor="cyan" paddingX={1}>
      <Text dimColor>{multiline ? '>>> ' : '> '}</Text>
      <TextInput
        value={value}
        onChange={onChange}
        onSubmit={onSubmit}
        placeholder={disabled ? 'Thinking...' : 'Type a message...'}
      />
      {multiline && <Text dimColor> [ESC to toggle]</Text>}
    </Box>
  );
}
```

### Python Server 示例

```python
# packages/core/nano_code/server/rpc.py
import asyncio
import json
import sys
from typing import AsyncIterator, Any
from dataclasses import dataclass

from nano_code.agent.graph import get_agent_graph
from nano_code.agent.state import create_initial_state
from nano_code.tools.registry import get_tool_registry


@dataclass
class StreamEvent:
    type: str  # thinking | tool_call | tool_result | response | done
    content: str
    metadata: dict | None = None


class JSONRPCServer:
    """JSON-RPC 2.0 Server over stdio"""
    
    def __init__(self):
        self.graph = get_agent_graph()
        self.registry = get_tool_registry()
    
    async def handle_request(self, request: dict) -> dict:
        """处理 JSON-RPC 请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            handler = getattr(self, f"handle_{method.replace('.', '_')}")
            result = await handler(params)
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(e)}
            }
    
    async def handle_agent_stream(self, params: dict) -> None:
        """流式对话 - 发送多个响应"""
        prompt = params.get("prompt")
        mode = params.get("mode", "build")
        
        state = create_initial_state(prompt, mode=mode)
        
        async for event in self._stream_graph(state):
            self._send_notification("stream", event)
        
        self._send_notification("stream", {"type": "done"})
    
    async def _stream_graph(self, state: dict) -> AsyncIterator[dict]:
        """流式执行 Graph"""
        for chunk in self.graph.stream(state):
            for node_name, node_output in chunk.items():
                if node_name == "thinking":
                    yield {
                        "type": "thinking",
                        "content": node_output.get("messages", [{}])[-1].get("content", "")
                    }
                elif node_name == "execute":
                    for tool_call in state.get("tool_calls", []):
                        yield {
                            "type": "tool_call",
                            "content": f"Calling {tool_call['name']}...",
                            "metadata": {"toolName": tool_call["name"], "toolArgs": tool_call["args"]}
                        }
                    for result in node_output.get("tool_results", []):
                        yield {"type": "tool_result", "content": result}
    
    async def handle_tools_list(self, params: dict) -> dict:
        """获取工具列表"""
        tools = []
        for name, tool in self.registry._tools.items():
            tools.append({
                "name": name,
                "description": tool.description,
                "parameters": tool.args_schema.schema() if hasattr(tool, 'args_schema') else {}
            })
        return {"tools": tools}
    
    async def handle_tool_execute(self, params: dict) -> dict:
        """执行工具"""
        name = params.get("name")
        args = params.get("args", {})
        result = self.registry.execute(name, args)
        return {"success": True, "result": result}
    
    def _send_notification(self, method: str, params: dict) -> None:
        """发送通知"""
        notification = {"jsonrpc": "2.0", "method": method, "params": params}
        sys.stdout.write(json.dumps(notification) + "\n")
        sys.stdout.flush()
    
    async def run(self) -> None:
        """运行服务器"""
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            try:
                request = json.loads(line)
                response = await self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError:
                pass


if __name__ == "__main__":
    server = JSONRPCServer()
    asyncio.run(server.run())
```

## 实施计划

### Phase 1: 基础设施 (1-2 天)

1. **创建 monorepo 结构**
   - 初始化 pnpm workspace
   - 配置 TypeScript
   - 配置 Python 包

2. **实现 JSON-RPC Server**
   - Python 端协议实现
   - 流式输出支持
   - 基础测试

3. **实现 TypeScript RPC 客户端**
   - 进程启动
   - 消息解析
   - 事件订阅

### Phase 2: CLI 组件 (2-3 天)

1. **基础组件**
   - ChatView
   - MessageList
   - InputBox
   - StatusBar

2. **高级组件**
   - Markdown 渲染
   - 代码高亮
   - 工具执行动画
   - 流式输出

3. **交互功能**
   - 多行输入
   - 历史记录
   - 自动补全

### Phase 3: 功能迁移 (1-2 天)

1. **配置管理**
   - 向导迁移
   - 环境变量读取

2. **命令支持**
   - /help, /exit, /clear
   - /config, /model

3. **测试 & 文档**
   - E2E 测试
   - 用户文档

### Phase 4: 优化 & 发布 (1 天)

1. **性能优化**
   - 渲染优化
   - 内存管理

2. **打包发布**
   - npm 发布
   - PyPI 发布
   - 安装脚本

## 预期效果对比

| 功能 | 当前 (Python/rich) | 目标 (TypeScript/ink) |
|------|-------------------|----------------------|
| 流式输出 | ⚠️ 手动 flush，有延迟 | ✅ 原生支持，实时渲染 |
| 原地更新 | ❌ 只能追加输出 | ✅ 可原地更新内容 |
| 多行输入 | ⚠️ 需要 Tab 换行 | ✅ 自然换行 |
| 动画效果 | ⚠️ 简单 loading | ✅ 流畅动画 |
| Markdown | ✅ 支持 | ✅ 支持 + 更好渲染 |
| 代码高亮 | ⚠️ 基础 | ✅ 完整高亮 |
| 性能 | ⚠️ 一般 | ✅ 更快响应 |

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 跨进程通信复杂度 | 中 | 使用成熟的 JSON-RPC 库 |
| Python 依赖管理 | 低 | 保持原有 pyproject.toml |
| TypeScript 学习曲线 | 低 | ink API 简单直观 |
| 打包复杂度 | 中 | 使用 pkg 或 nexe 打包单二进制 |

## 总结

这个方案通过引入 TypeScript CLI 层，实现了：

1. **与 Claude Code 对齐的体验** - ink 框架提供与 Claude Code 相同的技术栈
2. **最小化 Python 改动** - Agent、Tools、LLM 层完全不变
3. **渐进式迁移** - 可逐步替换，不破坏现有功能
4. **保持 Python 优势** - AI/ML 生态完整保留

预计总工作量：**5-8 天**
