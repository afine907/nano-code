# LLM 配置

## 支持的 API

Nano-Code 支持三种 LLM 后端：

### 1. OpenAI 兼容 API（推荐）

适用于 LongCat、DeepSeek、Ollama 等兼容 OpenAI API 的服务。

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.longcat.chat/openai/v1
NANO_CODE_MODEL=gpt-4o-mini
```

### 2. Anthropic Claude

```env
ANTHROPIC_API_KEY=your-anthropic-key
NANO_CODE_MODEL=claude-sonnet-4-20250514
```

### 3. OpenAI 默认

```env
OPENAI_API_KEY=your-openai-key
NANO_CODE_MODEL=gpt-4o-mini
```

## 配置优先级

```
OPENAI_BASE_URL 存在?
    ├── 是 → 使用 OpenAI 兼容 API
    └── 否 → ANTHROPIC_API_KEY 存在?
                ├── 是 → 使用 Claude
                └── 否 → 使用 OpenAI 默认
```

## 配置文件

### .env 文件

创建 `.env` 文件（参考 `.env.example`）：

```env
# OpenAI 兼容 API（如 LongCat）
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.longcat.chat/openai/v1

# 或 Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-xxx

# 模型选择
NANO_CODE_MODEL=gpt-4o-mini
```

### config.py 配置

使用 Pydantic Settings 管理：

```python
class Settings(BaseSettings):
    model: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    anthropic_api_key: str | None = None
    storage_path: Path = Path.home() / ".nano-code"
```

## LLM 客户端实现

### get_llm() 函数

```python
def get_llm(model: str | None = None, temperature: float = 0.7) -> BaseChatModel:
    settings = get_settings()
    model_name = model or settings.model

    # 1. 自定义 OpenAI 兼容 API
    if base_url := settings.openai_base_url:
        return ChatOpenAI(model=model_name, base_url=base_url, ...)

    # 2. Anthropic Claude
    if settings.anthropic_api_key:
        return ChatAnthropic(model=claude_model, ...)

    # 3. OpenAI 默认
    return ChatOpenAI(model=model_name, ...)
```

## 常用模型

| 提供商 | 模型名 | 特点 |
|--------|--------|------|
| OpenAI | gpt-4o-mini | 快速、便宜 |
| OpenAI | gpt-4o | 更强推理 |
| Anthropic | claude-sonnet-4-20250514 | 平衡性能 |
| Anthropic | claude-opus-4-20250514 | 最强能力 |
| LongCat | deepseek-chat | 国产选择 |

## 工具绑定

LLM 通过 `bind_tools()` 获取工具定义：

```python
tools = registry.get_langchain_tools()
llm_with_tools = llm.bind_tools(tools)

response = llm_with_tools.invoke(messages)
# response.tool_calls 包含工具调用信息
```
