#!/usr/bin/env python3
"""五个核心 Agent 完整示例

演示如何使用 ImpactAnalyzer → PRDAgent → SpecAgent → CodingAgent → VerificationAgent
完成一个完整的编码任务。

使用方法:
    uv run python examples/five_agents_demo.py
"""

from pathlib import Path

from jojo_code.agent.task_spec import TaskSpec
from jojo_code.agent.impact_analyzer import ImpactAnalyzer
from jojo_code.agent.prd_agent import PRDAgent
from jojo_code.agent.spec_agent import SpecAgent
from jojo_code.agent.coding_agent import CodingAgent
from jojo_code.agent.verification_agent import VerificationAgent
from jojo_code.agent.pipeline import AgentPipeline


def demo_manual_execution():
    """手动执行每个 Agent"""
    print("=" * 60)
    print("🔧 手动执行模式")
    print("=" * 60)
    
    # 1. 创建 TaskSpec
    task_spec = TaskSpec(
        task="添加用户登录功能，支持 JWT 认证",
        context={"user": "demo", "priority": "high"}
    )
    print(f"\n📝 任务: {task_spec.task}")
    print(f"ID: {task_spec.id}")
    
    # 2. ImpactAnalyzer - 分析影响
    print("\n" + "=" * 60)
    print("Phase 1: ImpactAnalyzer")
    print("=" * 60)
    analyzer = ImpactAnalyzer(task_spec, code_base_path=Path("."))
    task_spec = analyzer.run()
    
    print(f"✅ 影响分析完成")
    print(f"受影响组件: {task_spec.impact_analysis.affected_components}")
    print(f"风险等级: {task_spec.impact_analysis.risk_level}")
    print(f"决策记录: {len(task_spec.audit_trail)} 条")
    
    # 3. PRDAgent - 生成需求文档
    print("\n" + "=" * 60)
    print("Phase 2: PRDAgent")
    print("=" * 60)
    prd_agent = PRDAgent(task_spec)
    task_spec = prd_agent.run()
    
    print(f"✅ PRD 生成完成")
    print(f"标题: {task_spec.prd.title}")
    print(f"用户故事: {len(task_spec.prd.user_stories)} 个")
    print(f"验收标准: {len(task_spec.prd.acceptance_criteria)} 条")
    
    # 4. SpecAgent - 生成技术规格
    print("\n" + "=" * 60)
    print("Phase 3: SpecAgent")
    print("=" * 60)
    spec_agent = SpecAgent(task_spec)
    task_spec = spec_agent.run()
    
    print(f"✅ 技术规格生成完成")
    print(f"API 规格: {len(task_spec.spec.api_spec)} 字符")
    print(f"数据模型: {len(task_spec.spec.data_models)} 个")
    print(f"接口定义: {len(task_spec.spec.interfaces)} 个")
    print(f"依赖: {task_spec.spec.dependencies}")
    
    # 5. CodingAgent - 实现代码
    print("\n" + "=" * 60)
    print("Phase 4: CodingAgent")
    print("=" * 60)
    coding_agent = CodingAgent(task_spec, code_base_path=Path("."))
    task_spec = coding_agent.run()
    
    print(f"✅ 代码实现完成")
    if task_spec.code_result:
        print(f"修改文件: {task_spec.code_result.files_changed}")
        print(f"新建文件: {task_spec.code_result.files_created}")
    
    # 6. VerificationAgent - 验证实现
    print("\n" + "=" * 60)
    print("Phase 5: VerificationAgent")
    print("=" * 60)
    verify_agent = VerificationAgent(task_spec)
    task_spec = verify_agent.run()
    
    print(f"✅ 验证完成")
    print(f"通过: {task_spec.verification.passed}")
    print(f"得分: {task_spec.verification.score:.2%}")
    print(f"问题: {len(task_spec.verification.issues)} 个")
    
    # 7. 决策追踪
    print("\n" + "=" * 60)
    print("📊 决策追踪")
    print("=" * 60)
    for i, decision in enumerate(task_spec.audit_trail[:5], 1):
        print(f"{i}. [{decision.agent.value}] {decision.decision_type.value}")
        print(f"   理由: {decision.reasoning[:80]}...")
    
    print(f"\n总决策记录: {len(task_spec.audit_trail)} 条")
    
    return task_spec


def demo_pipeline_execution():
    """使用 Pipeline 自动执行"""
    print("\n\n" + "=" * 60)
    print("🚀 Pipeline 自动执行模式")
    print("=" * 60)
    
    # 创建 TaskSpec
    task_spec = TaskSpec(
        task="添加用户注册功能",
        context={"user": "demo", "priority": "high"}
    )
    print(f"\n📝 任务: {task_spec.task}")
    
    # 创建 Pipeline 并执行
    pipeline = AgentPipeline(task_spec, code_base_path=Path("."))
    result = pipeline.run()
    
    # 输出结果
    print(f"\n✅ Pipeline 执行完成")
    print(f"状态: {result.status.value}")
    print(f"阶段数: {len(result.stage_results)}")
    
    # 生成报告
    report = result.generate_report()
    print("\n" + "=" * 60)
    print("📄 执行报告")
    print("=" * 60)
    print(report[:500] + "..." if len(report) > 500 else report)
    
    return result


def demo_partial_execution():
    """部分执行示例"""
    print("\n\n" + "=" * 60)
    print("🎯 部分执行模式")
    print("=" * 60)
    
    task_spec = TaskSpec(task="添加 API 文档功能")
    
    # 只执行前三个阶段
    pipeline = AgentPipeline(task_spec, code_base_path=Path("."))
    result = pipeline.run(stop_at="spec_generation")
    
    print(f"\n✅ 执行到 Spec 生成阶段")
    print(f"阶段数: {len(result.stage_results)}")
    print(f"TaskSpec 状态: {task_spec.status.value}")
    
    # 验证 Spec 已生成
    assert task_spec.spec is not None
    print(f"✅ Spec 已生成: {len(task_spec.spec.api_spec)} 字符")
    
    return result


def demo_resume_execution():
    """恢复执行示例"""
    print("\n\n" + "=" * 60)
    print("🔄 恢复执行模式")
    print("=" * 60)
    
    # 模拟已完成的 TaskSpec
    task_spec = TaskSpec(task="添加密码重置功能")
    
    # 先执行 ImpactAnalyzer
    analyzer = ImpactAnalyzer(task_spec, code_base_path=Path("."))
    task_spec = analyzer.run()
    print(f"✅ ImpactAnalyzer 完成，状态: {task_spec.status.value}")
    
    # 从 PRD 阶段恢复执行
    pipeline = AgentPipeline(task_spec, code_base_path=Path("."))
    result = pipeline.run(start_from="prd_generation")
    
    print(f"\n✅ 从 PRD 阶段恢复执行完成")
    print(f"阶段数: {len(result.stage_results)}")
    
    return result


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🤖 jojo-Code 五核心 Agent 演示")
    print("=" * 60)
    
    try:
        # 手动执行模式
        task_spec = demo_manual_execution()
        
        # Pipeline 自动执行模式
        result = demo_pipeline_execution()
        
        # 部分执行模式
        demo_partial_execution()
        
        # 恢复执行模式
        demo_resume_execution()
        
        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
        
        print("\n📚 关键特性:")
        print("  1. TaskSpec 作为单一事实源 (SSOT)")
        print("  2. 五个 Agent 按序执行")
        print("  3. 决策可追溯 (audit_trail)")
        print("  4. 支持中断和恢复")
        print("  5. 自动推断验收标准")
        
        print("\n💡 使用建议:")
        print("  - 手动模式: 调试和学习时使用")
        print("  - Pipeline模式: 生产环境自动化执行")
        print("  - 部分执行: 增量开发或测试特定阶段")
        print("  - 恢复执行: 从失败或中断点继续")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
