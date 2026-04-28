# 五核心 Agent 快速开始

## 架构概览

```
用户任务 → ImpactAnalyzer → PRDAgent → SpecAgent → CodingAgent → VerificationAgent → 完成
             │                   │            │             │                │
             └───────────────────┴────────────┴─────────────┴────────────────┘
                                       │
                                       ▼
                              TaskSpec (单一事实源)
                                       │
                                       ▼
                              AuditTrail (决策追踪)
```

## 核心组件

### 1. TaskSpec - 单一事实源

所有 Agent 通过 TaskSpec 传递上下文，确保数据一致性和可追溯性。

```python
from jojo_code.agent.task_spec import TaskSpec

task_spec = TaskSpec(
    task="添加用户登录功能",
    context={"priority": "high"}
)
```

### 2. 五个核心 Agent

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **ImpactAnalyzer** | 分析代码影响 | 任务描述 | ImpactAnalysis |
| **PRDAgent** | 生成需求文档 | ImpactAnalysis | PRD |
| **SpecAgent** | 生成技术规格 | PRD | Spec |
| **CodingAgent** | 实现代码 | Spec, PRD | CodeResult |
| **VerificationAgent** | 验证实现 | CodeResult, Spec, PRD | VerificationResult |

### 3. Pipeline - 自动化流水线

```python
from jojo_code.agent.pipeline import AgentPipeline

# 自动执行所有阶段
pipeline = AgentPipeline(task_spec)
result = pipeline.run()

# 部分执行
result = pipeline.run(stop_at="spec_generation")

# 恢复执行
result = pipeline.run(start_from="prd_generation")
```

## 使用示例

### 手动执行

```python
from jojo_code.agent.impact_analyzer import ImpactAnalyzer
from jojo_code.agent.prd_agent import PRDAgent
from jojo_code.agent.spec_agent import SpecAgent
from jojo_code.agent.coding_agent import CodingAgent
from jojo_code.agent.verification_agent import VerificationAgent

# 按顺序执行每个 Agent
task_spec = TaskSpec(task="添加用户认证功能")

task_spec = ImpactAnalyzer(task_spec).run()
task_spec = PRDAgent(task_spec).run()
task_spec = SpecAgent(task_spec).run()
task_spec = CodingAgent(task_spec).run()
task_spec = VerificationAgent(task_spec).run()

# 检查结果
if task_spec.verification.passed:
    print("✅ 任务验证通过！")
```

### Pipeline 自动执行

```python
from jojo_code.agent.pipeline import AgentPipeline

pipeline = AgentPipeline(task_spec)
result = pipeline.run()

# 生成报告
report = result.generate_report()
print(report)
```

## 决策追踪

每个 Agent 的决策都记录在 `audit_trail` 中：

```python
for decision in task_spec.audit_trail:
    print(f"[{decision.agent.value}] {decision.decision_type.value}")
    print(f"  理由: {decision.reasoning}")
    print(f"  置信度: {decision.confidence}")
```

## 验收标准自动推断

VerificationAgent 从 Spec 和 PRD 自动推断验收标准，无需预设：

```python
# 自动推断的验收标准包括：
# - 用户故事验证
# - API 端点可访问性
# - 数据模型正确性
# - 接口实现完整性
# - 依赖安装验证
# - 测试结果验证
```

## 测试

```bash
# 运行所有测试
uv run pytest tests/test_agent/ -v

# 运行特定 Agent 测试
uv run pytest tests/test_agent/test_impact_analyzer.py -v
uv run pytest tests/test_agent/test_pipeline.py -v
```

## 核心痛点解决

| 痛点 | 解决方案 |
|------|----------|
| ImpactAnalyzer 依赖外部工具 | 纯 Python 实现，无 ctags 依赖 |
| Agent 上下文传递不清晰 | TaskSpec 作为单一事实源 |
| Verification 依赖预设标准 | 从 Spec 自动推断验收标准 |
| Agent 决策不可追溯 | AuditTrail 记录完整决策链 |

## 文件结构

```
src/jojo_code/agent/
├── task_spec.py           # TaskSpec 定义
├── impact_analyzer.py     # 影响分析器
├── prd_agent.py          # 需求文档生成器
├── spec_agent.py         # 技术规格生成器
├── coding_agent.py       # 代码实现器
├── verification_agent.py # 验收验证器
└── pipeline.py           # 自动化流水线

tests/test_agent/
├── test_task_spec.py
├── test_impact_analyzer.py
├── test_prd_agent.py
├── test_spec_agent.py
├── test_coding_agent.py
├── test_verification_agent.py
└── test_pipeline.py
```

## 下一步

1. **集成 LLM**: 每个 Agent 可以调用 LLM 生成更智能的内容
2. **工具注册**: CodingAgent 可以注册工具来实际修改代码
3. **错误恢复**: 增强错误处理和自动重试机制
4. **并行优化**: 某些阶段可以并行执行
5. **人工审批**: 在关键节点插入人工审批流程

## 参考

- [架构设计文档](docs/five-agents-design.md)
- [示例脚本](examples/five_agents_demo.py)
