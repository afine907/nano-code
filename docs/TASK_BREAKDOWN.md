# CLI 重构任务拆分计划

## 项目结构

```
nano-code/
├── packages/
│   ├── cli/                    # Task 1.1, 1.3, 2.x 负责
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── app.tsx
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── client/
│   │   └── tests/
│   │
│   └── core/                    # Task 1.2 负责
│       ├── pyproject.toml
│       └── nano_code/
│           └── server/
│
├── package.json
├── pnpm-workspace.yaml
└── tsconfig.base.json
```

## Phase 1: 基础设施 (并行)

### Task 1.1: Monorepo 初始化 (独立)

**负责**: OpenCode Agent 1
**时间**: 30 分钟
**分支**: `feat/cli-monorepo`

**任务内容**:
1. 创建 monorepo 根目录结构
2. 配置 pnpm workspace
3. 配置 TypeScript 基础配置
4. 创建 packages/cli 目录骨架
5. 配置 ink + React 依赖
6. 创建基础入口文件

**产出文件**:
```
nano-code/
├── package.json              # monorepo 根配置
├── pnpm-workspace.yaml       # workspace 配置
├── tsconfig.base.json        # TypeScript 基础配置
└── packages/
    └── cli/
        ├── package.json      # CLI 包配置
        ├── tsconfig.json     # 继承 base
        └── src/
            └── index.ts      # 入口文件 (空)
```

**验证标准**:
- `pnpm install` 成功
- `pnpm --filter @nano-code/cli build` 成功

---

### Task 1.2: Python JSON-RPC Server (独立)

**负责**: OpenCode Agent 2
**时间**: 1 小时
**分支**: `feat/jsonrpc-server`

**任务内容**:
1. 在 `src/nano_code/server/` 创建 JSON-RPC Server
2. 实现 stdio 通信
3. 实现以下方法:
   - `agent.stream` - 流式对话
   - `tools.list` - 获取工具列表
   - `tool.execute` - 执行工具
   - `config.get` - 获取配置
   - `config.set` - 设置配置
4. 实现流式事件通知
5. 编写单元测试

**产出文件**:
```
src/nano_code/
└── server/
    ├── __init__.py
    ├── rpc.py           # JSON-RPC Server
    └── protocol.py      # 协议定义
tests/
└── test_server.py       # 单元测试
```

**API 定义**:
```python
# 请求
{"jsonrpc": "2.0", "id": "1", "method": "agent.stream", "params": {"prompt": "..."}}

# 响应
{"jsonrpc": "2.0", "id": "1", "result": {"status": "streaming"}}

# 流式通知
{"jsonrpc": "2.0", "method": "stream", "params": {"type": "response", "content": "..."}}
```

**验证标准**:
- 单元测试通过
- 可以通过 stdin/stdout 与 Server 交互

---

### Task 1.3: TypeScript JSON-RPC Client (依赖 Task 1.1)

**负责**: OpenCode Agent 3
**时间**: 1 小时
**分支**: `feat/jsonrpc-client`

**依赖**: Task 1.1 (需要 monorepo 结构)

**任务内容**:
1. 在 `packages/cli/src/client/` 创建 RPC 客户端
2. 实现进程启动 (spawn Python server)
3. 实现 JSON-RPC 请求发送
4. 实现流式事件监听
5. 编写测试

**产出文件**:
```
packages/cli/src/
└── client/
    ├── index.ts        # 导出
    ├── rpc.ts          # RPC 客户端
    └── types.ts        # 类型定义
tests/
└── client.test.ts
```

**类型定义**:
```typescript
interface StreamEvent {
  type: 'thinking' | 'tool_call' | 'tool_result' | 'response' | 'done';
  content: string;
  metadata?: Record<string, unknown>;
}

interface AgentClient {
  connect(): Promise<void>;
  stream(prompt: string): Promise<void>;
  getTools(): Promise<Tool[]>;
  close(): void;
  on(event: 'stream', handler: (e: StreamEvent) => void): void;
}
```

**验证标准**:
- 可以启动 Python Server
- 可以发送请求并接收响应
- 可以接收流式事件

---

## Phase 2: CLI 组件 (并行)

### Task 2.1: 基础 UI 组件 (依赖 Task 1.1)

**负责**: OpenCode Agent 4
**时间**: 1.5 小时
**分支**: `feat/ui-components`

**依赖**: Task 1.1 (需要 ink 环境)

**任务内容**:
1. 实现 `ChatView` 组件 - 聊天消息列表
2. 实现 `MessageItem` 组件 - 单条消息
3. 实现 `InputBox` 组件 - 多行输入框
4. 实现 `StatusBar` 组件 - 状态栏

**产出文件**:
```
packages/cli/src/
└── components/
    ├── ChatView.tsx
    ├── MessageItem.tsx
    ├── InputBox.tsx
    └── StatusBar.tsx
```

**组件 API**:
```tsx
// ChatView
<ChatView messages={messages} isStreaming={isStreaming} />

// InputBox
<InputBox
  value={input}
  onChange={setInput}
  onSubmit={handleSubmit}
  disabled={isStreaming}
/>

// StatusBar
<StatusBar status="idle" model="gpt-4o-mini" />
```

**验证标准**:
- 组件可以独立渲染
- 输入框支持多行 (Ctrl+D 切换)
- 状态栏正确显示状态

---

### Task 2.2: Markdown 渲染组件 (依赖 Task 1.1)

**负责**: OpenCode Agent 5
**时间**: 1 小时
**分支**: `feat/markdown-renderer`

**依赖**: Task 1.1 (需要 ink 环境)

**任务内容**:
1. 实现 `Markdown` 组件
2. 支持标题、粗体、列表
3. 支持代码块 + 语法高亮
4. 支持行内代码

**产出文件**:
```
packages/cli/src/
└── components/
    └── Markdown.tsx
```

**组件 API**:
```tsx
<Markdown content="# Title\n\n**bold** text\n\n```python\nprint('hello')\n```" />
```

**验证标准**:
- 正确渲染 Markdown
- 代码块有高亮
- 处理边界情况

---

### Task 2.3: 工具执行动画组件 (依赖 Task 1.1)

**负责**: OpenCode Agent 6
**时间**: 45 分钟
**分支**: `feat/tool-animation`

**依赖**: Task 1.1 (需要 ink 环境)

**任务内容**:
1. 实现 `ToolExecution` 组件 - 工具执行动画
2. 实现 `ThinkingIndicator` 组件 - 思考动画
3. 实现加载动画效果

**产出文件**:
```
packages/cli/src/
└── components/
    ├── ToolExecution.tsx
    └── ThinkingIndicator.tsx
```

**组件 API**:
```tsx
<ToolExecution
  toolName="read_file"
  args={{ path: "/src/main.py" }}
/>

<ThinkingIndicator />
```

**验证标准**:
- 动画流畅
- 正确显示工具信息

---

### Task 2.4: useAgent Hook (依赖 Task 1.3)

**负责**: OpenCode Agent 7
**时间**: 1 小时
**分支**: `feat/use-agent-hook`

**依赖**: Task 1.3 (需要 RPC 客户端)

**任务内容**:
1. 实现 `useAgent` Hook
2. 管理消息状态
3. 管理流式状态
4. 提供发送消息方法

**产出文件**:
```
packages/cli/src/
└── hooks/
    ├── index.ts
    └── useAgent.ts
```

**Hook API**:
```typescript
const {
  messages,      // Message[]
  sendMessage,   // (prompt: string) => Promise<void>
  isStreaming,   // boolean
  status,        // 'idle' | 'thinking' | 'executing'
  currentTool,   // { name, args } | undefined
  model,         // string
} = useAgent();
```

**验证标准**:
- Hook 正确管理状态
- 可以发送消息并更新消息列表

---

## Phase 3: 集成与测试 (串行)

### Task 3.1: App 集成 (依赖 Phase 2 全部)

**负责**: OpenCode Agent 8
**时间**: 1 小时
**分支**: `feat/app-integration`

**依赖**: Task 2.1, 2.2, 2.3, 2.4

**任务内容**:
1. 创建 `App.tsx` 主组件
2. 集成所有组件
3. 实现 CLI 入口
4. 测试完整流程

**产出文件**:
```
packages/cli/src/
├── app.tsx
└── index.ts
```

**验证标准**:
- CLI 可以启动
- 可以与 Agent 对话
- 流式输出正常

---

### Task 3.2: E2E 测试 (依赖 Task 3.1)

**负责**: OpenCode Agent 9
**时间**: 1 小时
**分支**: `feat/e2e-tests`

**依赖**: Task 3.1

**任务内容**:
1. 编写 E2E 测试
2. 测试完整对话流程
3. 测试错误处理

**产出文件**:
```
packages/cli/tests/
└── e2e/
    └── chat.test.ts
```

**验证标准**:
- E2E 测试通过

---

## 任务依赖图

```
Phase 1 (并行):
┌─────────┐   ┌─────────┐   ┌─────────┐
│ Task 1.1│   │ Task 1.2│   │ Task 1.3│
│ Monorepo│   │ Server  │   │ Client  │
└────┬────┘   └────┬────┘   └────┬────┘
     │             │             │
     └─────────────┼─────────────┘
                   │
                   ▼
Phase 2 (并行):
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Task 2.1│   │ Task 2.2│   │ Task 2.3│   │ Task 2.4│
│ UI 组件 │   │Markdown │   │ 动画    │   │ Hook    │
└────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘
     │             │             │             │
     └─────────────┴─────────────┴─────────────┘
                   │
                   ▼
Phase 3 (串行):
          ┌─────────┐   ┌─────────┐
          │ Task 3.1│──▶│ Task 3.2│
          │ 集成    │   │ E2E测试 │
          └─────────┘   └─────────┘
```

## 并行执行计划

### Round 1 (Phase 1) - 3 个 Agent 并行

| Agent | 任务 | 分支 |
|-------|------|------|
| Agent 1 | Task 1.1 Monorepo | `feat/cli-monorepo` |
| Agent 2 | Task 1.2 Server | `feat/jsonrpc-server` |
| Agent 3 | Task 1.3 Client | `feat/jsonrpc-client` |

### Round 2 (Phase 2) - 4 个 Agent 并行

| Agent | 任务 | 分支 |
|-------|------|------|
| Agent 4 | Task 2.1 UI 组件 | `feat/ui-components` |
| Agent 5 | Task 2.2 Markdown | `feat/markdown-renderer` |
| Agent 6 | Task 2.3 动画 | `feat/tool-animation` |
| Agent 7 | Task 2.4 Hook | `feat/use-agent-hook` |

### Round 3 (Phase 3) - 串行

| Agent | 任务 | 分支 |
|-------|------|------|
| Agent 8 | Task 3.1 集成 | `feat/app-integration` |
| Agent 9 | Task 3.2 E2E | `feat/e2e-tests` |

## 预计时间

| Phase | 并行时间 | 实际时间 |
|-------|---------|---------|
| Phase 1 | 1 小时 | 1 小时 (3 并行) |
| Phase 2 | 1.5 小时 | 1.5 小时 (4 并行) |
| Phase 3 | 2 小时 | 2 小时 (串行) |
| **总计** | **4.5 小时** | **~5 小时** |

对比串行执行: 8 小时 → 并行后: 5 小时

## 合并策略

1. 每个 Task 完成后创建 PR
2. Phase 1 的 3 个 PR 可以独立合并
3. Phase 2 的 PR 合并到 `feat/cli-refactor` 分支
4. Phase 3 完成后合并到 `master`

## 验收清单

### Phase 1 验收
- [ ] `pnpm install` 成功
- [ ] Python Server 可以通过 stdio 交互
- [ ] TypeScript Client 可以启动 Server

### Phase 2 验收
- [ ] 所有组件可以独立渲染
- [ ] Markdown 正确渲染
- [ ] 动画流畅
- [ ] Hook 正确工作

### Phase 3 验收
- [ ] CLI 可以启动并对话
- [ ] 流式输出正常
- [ ] E2E 测试通过
