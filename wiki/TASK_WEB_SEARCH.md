# 任务: 实现 Web 搜索工具

## 背景
为 Agent 添加联网搜索能力，可以搜索最新信息、查找文档、获取技术资料。

## 需求

### 1. 搜索工具
- `web_search(query: str, count: int = 5)` - 网页搜索
- 返回：标题、URL、摘要

### 2. 搜索引擎
优先级：
1. DuckDuckGo (免费，无需 API key)
2. Tavily (需 API key，质量更高)
3. SerpAPI (需 API key)

### 3. 工具实现
```python
@tool
def web_search(query: str, count: int = 5) -> str:
    """搜索网页
    
    Args:
        query: 搜索关键词
        count: 返回结果数量 (1-10)
    
    Returns:
        搜索结果，格式：
        1. 标题
           URL: https://...
           摘要: ...
    """
    # 使用 duckduckgo-search 库
    from duckduckgo_search import DDGS
    
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=count):
            results.append({
                "title": r["title"],
                "url": r["href"],
                "snippet": r["body"],
            })
    
    # 格式化输出
    ...
```

### 4. 网页抓取工具 (可选)
- `web_fetch(url: str)` - 获取网页内容
- 返回 Markdown 格式

### 5. 实现位置
- `src/nano_code/tools/web_tools.py` - Web 工具实现
- `src/nano_code/tools/registry.py` - 注册新工具
- `tests/test_tools/test_web_tools.py` - 测试

### 6. 依赖
```toml
[project.dependencies]
duckduckgo-search = ">=6.0"
```

### 7. 测试
- 测试基本搜索
- 测试结果格式化
- 测试错误处理（网络问题）

## 验收标准
- [ ] `web_search` 工具可用
- [ ] 无需 API key 即可使用
- [ ] 返回格式化的搜索结果
- [ ] 测试覆盖率 > 80%
