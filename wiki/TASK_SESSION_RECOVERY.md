# 任务: 实现会话恢复

## 背景
参考 OpenCode 的 session 管理，实现会话保存和恢复功能，让用户可以继续之前的对话。

## 需求

### 1. 会话存储
- 会话保存到 `~/.nano-code/sessions/<session_id>.json`
- 存储内容：消息历史、工具调用记录、创建时间、更新时间
- 自动保存间隔：每次交互后

### 2. 会话列表
- `/sessions` 命令列出所有会话
- 显示会话 ID、创建时间、消息数量、最后活动时间

### 3. 会话恢复
- `/continue <session_id>` 恢复指定会话
- `/continue` 恢复最近一个会话
- `/new` 开始新会话

### 4. 实现位置
- `src/nano_code/session/manager.py` - 会话管理器
- `src/nano_code/session/models.py` - 会话数据模型
- `src/nano_code/cli/commands.py` - CLI 命令处理
- `src/nano_code/cli/main.py` - 集成会话管理

### 5. 数据结构
```python
@dataclass
class Session:
    id: str  # UUID
    messages: list[dict]
    tool_calls: list[dict]
    created_at: datetime
    updated_at: datetime
    model: str
    token_count: int
```

### 6. 测试
- 测试会话保存
- 测试会话恢复
- 测试会话列表

## 验收标准
- [ ] 会话自动保存
- [ ] `/sessions` 列出所有会话
- [ ] `/continue` 恢复最近会话
- [ ] `/continue <id>` 恢复指定会话
- [ ] 测试覆盖率 > 80%
