# 五核心 Agent 架构设计

> 版本: 1.0
> 日期: 2026-04-28
> 作者: jojo
> 依赖: agentops-system-design.md v1.0, task_spec.py

---

## 1. 架构概览

### 1.1 设计原则

- **TaskSpec 作为单一事实源 (SSOT)**：所有 Agent 通过 TaskSpec 对象传递上下文，无直接 Agent-to-Agent 通信
- **决策可追溯性**：每个 Agent 的所有决策写入 audit_trail，形成完整决策链
- **单向数据流**：严格按顺序执行，每个 Agent 只能修改属于自己职责范围内的字段

### 1.2 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        TaskSpec (SSOT)                          │
│                                                                 │
│  id │ task │ status │ context │ impact │ prd │ spec │ code │ verif │
│                                               audit_trail[]   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    ▼                   ▼                   ▼
┌─────────┐      ┌─────────┐      ┌──────────────┐
│  User   │─────▶│ Impact  │─────▶│    PRD       │
│ Request │      │ Analyzer│      │    Agent      │
└─────────┘      └─────────┘      └──────┬───────┘
                                         │
                                         ▼
                                    ┌─────────┐
                                    │  Spec  │
                                    │ Agent  │
                                    └────┬────┘
                                         │
                                         ▼
                                    ┌─────────┐
                                    │ Coding │
                                    │ Agent  │
                                    └────┬────┘
                                         │
                                         ▼
                                    ┌─────────────┐
                                    │Verification │
                                    │   Agent     │
                                    └─────────────┘
```

### 1.3 Agent 执行顺序

```
User Input → ImpactAnalyzer → PRDAgent → SpecAgent → CodingAgent → VerificationAgent → Done
                │                   │            │             │                │
                ▼                   ▼            ▼             ▼                ▼
          ImpactAnalysis        PRD          Spec       CodeResult      VerificationResult
                │                   │            │             │                │
                └───────────────────┴────────────┴─────────────┴────────────────┘
                                       │
                                       ▼
                              TaskSpec.audit_trail[]
```

---

## 2. TaskSpec - 单一事实源 (SSOT)

### 2.1 设计目标

TaskSpec 是五个 Agent 之间唯一的数据交换载体，确保：
- 数据一致性：所有 Agent 读取同一份数据
- 状态可恢复：从 TaskSpec 可完全恢复任务状态
- 职责隔离：每个 Agent 只修改特定字段

### 2.2 核心字段

| 字段 | 类型 | 写入 Agent | 说明 |
|------|------|------------|------|
| `id` | `str` | System | 任务唯一标识 |
| `task` | `str` | User | 原始用户任务描述 |
| `status` | `TaskStatus` | All | 当前任务状态 |
| `context` | `dict` | All | 共享上下文（用户偏好、环境变量等） |
| `impact_analysis` | `ImpactAnalysis` | ImpactAnalyzer | 影响分析结果 |
| `prd` | `PRD` | PRDAgent | 产品需求文档 |
| `spec` | `Spec` | SpecAgent | 技术规格说明 |
| `code_result` | `CodeResult` | CodingAgent | 代码变更结果 |
| `verification` | `VerificationResult` | VerificationAgent | 验证结果 |
| `audit_trail` | `list[DecisionRecord]` | All | 决策审计日志 |

### 2.3 状态流转

```
PENDING → IMPACT_ANALYZED → PRD_COMPLETED → SPEC_COMPLETED → CODING_COMPLETED → VERIFIED
                                                                               ↓
                                                                            FAILED
```

---

## 3. 决策可追溯性设计

### 3.1 DecisionRecord 结构

每个决策记录包含：

```python
@dataclass
class DecisionRecord:
    id: str                    # 决策唯一 ID
    agent: AgentType           # 产生决策的 Agent
    decision_type: DecisionType # 决策类型 (INPUT/OUTPUT/REASONING/TOOL_CALL/ERROR/APPROVAL)
    timestamp: datetime        # 决策时间戳
    content: Any               # 决策内容
    reasoning: str             # 决策理由
    confidence: float          # 置信度 (0.0-1.0)
    parent_id: Optional[str]   # 父决策 ID（用于链式追溯）
    metadata: dict             # 额外元数据
```

### 3.2 追溯链示例

```
ImpactAnalyzer 分析影响范围
├── Decision #1: INPUT - 接收任务 "添加用户登录功能"
├── Decision #2: REASONING - 识别受影响组件: ["auth", "api", "database"]
├── Decision #3: OUTPUT - 生成 ImpactAnalysis 对象
│
PRDAgent 编写需求文档
├── Decision #4: INPUT - 读取 ImpactAnalysis
├── Decision #5: REASONING - 拆解为 3 个用户故事
├── Decision #6: TOOL_CALL - 调用 read_file 读取现有 auth 模块
├── Decision #7: OUTPUT - 生成 PRD 对象
│
...（以此类推）
```

### 3.3 查询接口

```python
# 按 Agent 查询决策
spec_decisions = task_spec.get_decisions_by_agent(AgentType.SPEC_AGENT)

# 按类型查询决策
tool_calls = task_spec.get_decisions_by_type(DecisionType.TOOL_CALL)

# 追溯特定决策的父决策链
def get_decision_chain(task_spec: TaskSpec, decision_id: str) -> list[DecisionRecord]:
    chain = []
    current = next((d for d in task_spec.audit_trail if d.id == decision_id), None)
    while current:
        chain.append(current)
        if current.parent_id:
            current = next((d for d in task_spec.audit_trail if d.id == current.parent_id), None)
        else:
            break
    return chain
```

---

## 4. Agent 详细设计

### 4.1 ImpactAnalyzer (影响分析器)

**职责**：分析用户任务对现有系统的影响范围

**输入接口**：
```python
@dataclass
class ImpactAnalyzerInput:
    task: str                    # 用户任务描述
    context: dict[str, Any]      # 共享上下文
    repo_path: str = "."         # 代码仓库路径
```

**输出接口**：
```python
@dataclass
class ImpactAnalysis:
    summary: str                 # 影响分析摘要
    affected_components: list[str]  # 受影响的组件列表
    risk_level: str              # 风险等级: low/medium/high
    suggestions: list[str]       # 建议的执行策略
    metadata: dict               # 额外元数据（文件列表、依赖关系等）
```

**行为**：
1. 读取 `task` 字段
2. 使用代码分析工具扫描相关文件
3. 生成 `ImpactAnalysis` 对象
4. 写入 `TaskSpec.impact_analysis`
5. 记录决策到 `audit_trail`

**写入字段**：
- `TaskSpec.impact_analysis`
- `TaskSpec.audit_trail`（多条记录）

---

### 4.2 PRDAgent (产品需求 Agent)

**职责**：基于影响分析编写产品需求文档 (PRD)

**输入接口**：
```python
@dataclass
class PRDAgentInput:
    task: str                    # 用户任务描述
    impact_analysis: ImpactAnalysis  # 来自 ImpactAnalyzer
    context: dict[str, Any]      # 共享上下文
```

**输出接口**：
```python
@dataclass
class PRD:
    title: str                   # PRD 标题
    background: str              # 背景说明
    goals: list[str]             # 目标列表
    user_stories: list[dict]     # 用户故事 [{"as": "开发者", "i want": "...", "so that": "..."}]
    acceptance_criteria: list[str]  # 验收标准
    out_of_scope: list[str]      # 不包含的范围
    metadata: dict               # 额外元数据
```

**行为**：
1. 读取 `task` 和 `impact_analysis`
2. 分析用户需求，拆解为用户故事
3. 定义验收标准
4. 生成 `PRD` 对象
5. 写入 `TaskSpec.prd`
6. 记录决策到 `audit_trail`

**读取字段**：
- `TaskSpec.task`
- `TaskSpec.impact_analysis`

**写入字段**：
- `TaskSpec.prd`
- `TaskSpec.audit_trail`

---

### 4.3 SpecAgent (技术规格 Agent)

**职责**：基于 PRD 编写技术规格说明

**输入接口**：
```python
@dataclass
class SpecAgentInput:
    task: str                    # 用户任务描述
    prd: PRD                      # 来自 PRDAgent
    impact_analysis: ImpactAnalysis  # 来自 ImpactAnalyzer
    context: dict[str, Any]      # 共享上下文
```

**输出接口**：
```python
@dataclass
class Spec:
    api_spec: str                # API 规格说明 (OpenAPI 格式或文本)
    data_models: list[dict]      # 数据模型定义
    interfaces: list[dict]        # 接口定义
    dependencies: list[str]       # 新增依赖列表
    metadata: dict                # 额外元数据
```

**行为**：
1. 读取 `prd` 和 `impact_analysis`
2. 设计 API 接口和数据模型
3. 确定技术栈和依赖
4. 生成 `Spec` 对象
5. 写入 `TaskSpec.spec`
6. 记录决策到 `audit_trail`

**读取字段**：
- `TaskSpec.prd`
- `TaskSpec.impact_analysis`

**写入字段**：
- `TaskSpec.spec`
- `TaskSpec.audit_trail`

---

### 4.4 CodingAgent (编码 Agent)

**职责**：基于技术规格实现代码变更

**输入接口**：
```python
@dataclass
class CodingAgentInput:
    task: str                    # 用户任务描述
    prd: PRD                      # 来自 PRDAgent
    spec: Spec                    # 来自 SpecAgent
    context: dict[str, Any]      # 共享上下文
```

**输出接口**：
```python
@dataclass
class CodeResult:
    files_changed: list[str]     # 修改的文件列表
    files_created: list[str]     # 新建的文件列表
    diff_summary: str            # 变更摘要
    test_results: dict           # 测试结果 {"passed": 10, "failed": 0, "coverage": 85.0}
    metadata: dict               # 额外元数据
```

**行为**：
1. 读取 `prd`、`spec`
2. 实现代码变更
3. 运行测试
4. 生成 `CodeResult` 对象
5. 写入 `TaskSpec.code_result`
6. 记录决策到 `audit_trail`

**读取字段**：
- `TaskSpec.prd`
- `TaskSpec.spec`

**写入字段**：
- `TaskSpec.code_result`
- `TaskSpec.audit_trail`

---

### 4.5 VerificationAgent (验证 Agent)

**职责**：验证实现是否符合 PRD 和 Spec 要求

**输入接口**：
```python
@dataclass
class VerificationAgentInput:
    task: str                    # 用户任务描述
    prd: PRD                      # 来自 PRDAgent
    spec: Spec                    # 来自 SpecAgent
    code_result: CodeResult      # 来自 CodingAgent
    context: dict[str, Any]      # 共享上下文
```

**输出接口**：
```python
@dataclass
class VerificationResult:
    passed: bool                 # 是否通过验证
    score: float                 # 综合评分 (0.0-1.0)
    issues: list[dict]           # 发现的问题 [{"severity": "high", "description": "..."}]
    suggestions: list[str]       # 改进建议
    metadata: dict               # 额外元数据
```

**行为**：
1. 读取 `prd`、`spec`、`code_result`
2. 检查验收标准是否满足
3. 验证 API 实现是否符合规格
4. 运行集成测试
5. 生成 `VerificationResult` 对象
6. 写入 `TaskSpec.verification`
7. 记录决策到 `audit_trail`
8. 更新 `TaskSpec.status` 为 `VERIFIED` 或 `FAILED`

**读取字段**：
- `TaskSpec.prd`
- `TaskSpec.spec`
- `TaskSpec.code_result`

**写入字段**：
- `TaskSpec.verification`
- `TaskSpec.status`
- `TaskSpec.audit_trail`

---

## 5. 上下文传递机制

### 5.1 传递流程

```
┌──────────────┐
│  TaskSpec    │ ◀─── 所有 Agent 读取/写入同一对象
│  (SSOT)      │
└──────┬───────┘
       │
       │ 每个 Agent 执行时：
       │ 1. 从 TaskSpec 读取所需字段
       │ 2. 执行处理逻辑
       │ 3. 将结果写入 TaskSpec 对应字段
       │ 4. 记录决策到 audit_trail
       │
       ▼
┌──────────────────────────────────────────────────────┐
│                  Agent 执行伪代码                     │
│                                                      │
│  def run_agent(task_spec: TaskSpec):                 │
│      # 1. 读取输入                                    │
│      input_data = extract_input(task_spec)            │
│      task_spec.add_decision(INPUT, input_data)        │
│                                                      │
│      # 2. 执行处理                                    │
│      result = process(input_data)                    │
│      task_spec.add_decision(REASONING, ..., result)  │
│                                                      │
│      # 3. 写入输出                                    │
│      write_output(task_spec, result)                  │
│      task_spec.add_decision(OUTPUT, result)           │
│                                                      │
│      # 4. 更新状态                                    │
│      task_spec.update_status()                        │
│      return task_spec                                 │
└──────────────────────────────────────────────────────┘
```

### 5.2 字段访问矩阵

| Agent | task | impact_analysis | prd | spec | code_result | verification |
|-------|------|-----------------|-----|------|-------------|--------------|
| ImpactAnalyzer | 读 | - | - | - | - | - |
| PRDAgent | 读 | 读 | 写 | - | - | - |
| SpecAgent | 读 | 读 | 读 | 写 | - | - |
| CodingAgent | 读 | - | 读 | 读 | 写 | - |
| VerificationAgent | 读 | - | 读 | 读 | 读 | 写 |

---

## 6. 错误处理

### 6.1 Agent 失败处理

当某个 Agent 执行失败时：

1. 记录 `ERROR` 类型决策到 `audit_trail`
2. 设置 `TaskSpec.status = TaskStatus.FAILED`
3. 在 `TaskSpec.context["error"]` 中记录错误信息
4. 可选：触发回滚或重试逻辑

### 6.2 错误恢复

```python
def recover_from_failure(task_spec: TaskSpec) -> TaskSpec:
    """从失败状态恢复"""
    # 查找最后一个成功的 Agent
    decisions = task_spec.get_decisions_by_type(DecisionType.ERROR)
    if decisions:
        last_error = decisions[-1]
        # 根据错误类型决定恢复策略
        ...
    return task_spec
```

---

## 7. 实现文件清单

```
src/jojo_code/agent/
├── task_spec.py          # TaskSpec 及相关数据结构 (已创建)
├── impact_analyzer.py    # ImpactAnalyzer 实现 (待实现)
├── prd_agent.py          # PRDAgent 实现 (待实现)
├── spec_agent.py         # SpecAgent 实现 (待实现)
├── coding_agent.py       # CodingAgent 实现 (待实现)
├── verification_agent.py # VerificationAgent 实现 (待实现)
├── pipeline.py           # Agent 流水线编排 (待实现)
└── README.md             # Agent 模块说明 (待实现)
```

---

## 8. 使用示例

```python
from jojo_code.agent.task_spec import TaskSpec, TaskStatus
from jojo_code.agent.impact_analyzer import ImpactAnalyzer
from jojo_code.agent.prd_agent import PRDAgent
# ... 其他导入

# 1. 创建 TaskSpec
task_spec = TaskSpec(
    task="添加用户登录功能，支持 JWT 认证",
    context={"user": "jojo", "priority": "high"}
)

# 2. 按顺序执行 Agent
task_spec = ImpactAnalyzer().run(task_spec)
task_spec = PRDAgent().run(task_spec)
task_spec = SpecAgent().run(task_spec)
task_spec = CodingAgent().run(task_spec)
task_spec = VerificationAgent().run(task_spec)

# 3. 检查结果
if task_spec.status == TaskStatus.VERIFIED:
    print("任务验证通过！")
    print(f"变更文件: {task_spec.code_result.files_changed}")
else:
    print("任务失败")
    print(f"审计日志条数: {len(task_spec.audit_trail)}")

# 4. 追溯决策链
for decision in task_spec.audit_trail:
    print(f"[{decision.agent.value}] {decision.decision_type.value}: {decision.reasoning}")
```

---

## 9. 扩展方向

### 9.1 并行执行

某些 Agent 可以并行执行（如果设计允许）：
- ImpactAnalyzer 和 PRDAgent 的部分工作可并行
- SpecAgent 的某些接口设计可独立于 PRD 部分内容

### 9.2 人工审批节点

在关键节点（如 PRD 完成后、代码合并前）插入人工审批：
```python
task_spec.add_decision(
    agent=AgentType.PRD_AGENT,
    decision_type=DecisionType.APPROVAL,
    content="PRD 已审批通过",
    reasoning="所有验收标准清晰可测"
)
```

### 9.3 版本控制集成

TaskSpec 可序列化为 JSON 存储到 Git，实现版本化管理：
```python
import json
with open(f"task_specs/{task_spec.id}.json", "w") as f:
    json.dump(task_spec.to_dict(), f, indent=2)
```
