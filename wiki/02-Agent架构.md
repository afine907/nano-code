# Agent 架构设计

## 设计理念

Nano-Code 采用经典的 **ReAct (Reasoning + Acting)** 模式，通过 LangGraph 实现状态机驱动的 Agent 循环。

核心循环：
```
Thinking → Tool Call → Execute → Observe → Thinking → ...
```

## 状态图结构

```
START
  │
  ▼
┌─────────────┐
│  thinking   │ ◄─────────────────┐
│   node      │                   │
└─────┬───────┘                   │
      │                           │
      ▼                           │
  [tool_calls?]                   │
      │                           │
  ┌───┴───┐                       │
  │       │                       │
  ▼       ▼                       │
continue  end                     │
  │       │                       │
  ▼       ▼                       │
execute   END                     │
  │                               │
  └───────────────────────────────┘
```

## 核心组件

### 1. AgentState（状态定义）

```python
class AgentState(TypedDict):
    messages: list[dict]      # 对话历史
    tool_calls: list[dict]    # 待执行的工具调用
    tool_results: list[str]   # 工具执行结果
    is_complete: bool         # 任务是否完成
    iteration: int            # 当前循环次数
```

关键设计：
- `messages` 使用 `Annotated[..., merge_lists]` 支持增量更新
- `iteration` 用于限制最大循环次数（默认 50）

### 2. thinking_node（思考节点）

职责：调用 LLM 决定下一步行动

```python
def thinking_node(state: AgentState) -> dict:
    # 1. 转换消息格式
    # 2. 添加工具结果到消息
    # 3. 调用 LLM（带工具绑定）
    # 4. 提取工具调用
    # 5. 判断是否完成
```

输出：
- `tool_calls`: LLM 决定要执行的工具
- `is_complete`: 无工具调用时为 True

### 3. execute_node（执行节点）

职责：执行工具调用并收集结果

```python
def execute_node(state: AgentState) -> dict:
    # 遍历 tool_calls
    # 调用 registry.execute()
    # 收集结果到 tool_results
```

### 4. should_continue（路由函数）

决定是否继续循环：

```python
def should_continue(state: AgentState) -> Literal["continue", "end"]:
    if state["tool_calls"]:        # 有工具调用 → 继续
        return "continue"
    if state["is_complete"]:       # 任务完成 → 结束
        return "end"
    if state["iteration"] >= 50:   # 达到上限 → 结束
        return "end"
    return "end"
```

## 执行流程示例

用户输入：`读取 README.md 文件`

```
1. thinking_node
   - LLM 决定调用 read_file(path="README.md")
   - tool_calls = [{"name": "read_file", "args": {"path": "README.md"}}]

2. should_continue
   - 有 tool_calls → "continue"

3. execute_node
   - 执行 read_file
   - tool_results = ["# Nano-Code\n...文件内容..."]

4. thinking_node（第二次）
   - LLM 看到工具结果
   - 无需更多工具调用
   - is_complete = True

5. should_continue
   - is_complete → "end"

6. END
   - 返回最终响应
```

## 扩展点

1. **添加新节点**：在 `graph.py` 中添加节点和边
2. **修改路由逻辑**：调整 `should_continue` 函数
3. **增加状态字段**：扩展 `AgentState` TypedDict
