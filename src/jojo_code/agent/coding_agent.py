"""Coding Agent - 代码实现生成器

基于 Spec 和 PRD 生成代码，协调工具调用来修改文件、创建文件、
运行测试，并将决策记录到 audit_trail。
"""

import logging
from pathlib import Path
from typing import Any

from jojo_code.agent.task_spec import (
    AgentType,
    CodeResult,
    DecisionType,
    Spec,
    TaskSpec,
)

logger = logging.getLogger(__name__)


class CodingAgent:
    """代码实现生成器

    基于 Spec 和 PRD 生成代码实现，协调工具调用完成：
    - 文件创建和修改
    - 测试执行
    - 代码生成结果记录

    所有决策记录到 audit_trail 实现可追溯性。
    """

    def __init__(self, task_spec: TaskSpec, tool_registry: Any = None):
        """初始化 Coding Agent

        Args:
            task_spec: 任务规范，包含 Spec、PRD 等信息
            tool_registry: 工具注册表，用于执行工具调用
        """
        self.task_spec = task_spec
        self.tool_registry = tool_registry

    def run(self) -> CodeResult:
        """执行代码生成

        基于 Spec 和 PRD 生成代码实现，协调工具调用完成文件操作、
        测试执行等任务。

        Returns:
            CodeResult: 代码生成结果
        """
        self.task_spec.add_decision(
            agent=AgentType.CODING_AGENT,
            decision_type=DecisionType.INPUT,
            content={
                "task": self.task_spec.task,
                "has_spec": self.task_spec.spec is not None,
                "has_prd": self.task_spec.prd is not None,
            },
            reasoning="Starting code generation based on Spec and PRD",
        )

        if not self.task_spec.spec:
            logger.warning("No Spec found, cannot generate code")
            return self._create_empty_result()

        spec = self.task_spec.spec
        prd = self.task_spec.prd

        files_created = []
        files_changed = []
        test_results = {}

        try:
            implementation_plan = self._create_implementation_plan(spec, prd)
            self.task_spec.add_decision(
                agent=AgentType.CODING_AGENT,
                decision_type=DecisionType.REASONING,
                content=implementation_plan,
                reasoning="Created implementation plan based on Spec",
                confidence=0.85,
            )

            for file_action in implementation_plan.get("files_to_create", []):
                result = self._create_file(file_action)
                if result["success"]:
                    files_created.append(result["path"])
                    self.task_spec.add_decision(
                        agent=AgentType.CODING_AGENT,
                        decision_type=DecisionType.TOOL_CALL,
                        content={"action": "create_file", "path": result["path"]},
                        reasoning=f"Created file: {result['path']}",
                    )

            for file_action in implementation_plan.get("files_to_modify", []):
                result = self._modify_file(file_action)
                if result["success"]:
                    files_changed.append(result["path"])
                    self.task_spec.add_decision(
                        agent=AgentType.CODING_AGENT,
                        decision_type=DecisionType.TOOL_CALL,
                        content={"action": "modify_file", "path": result["path"]},
                        reasoning=f"Modified file: {result['path']}",
                    )

            test_results = self._run_tests()

            diff_summary = self._generate_diff_summary(files_created, files_changed)

            code_result = CodeResult(
                files_changed=files_changed,
                files_created=files_created,
                diff_summary=diff_summary,
                test_results=test_results,
                metadata={
                    "spec_title": prd.title if prd else "Unknown",
                    "files_count": len(files_created) + len(files_changed),
                    "tests_passed": test_results.get("passed", False),
                },
            )

            self.task_spec.code_result = code_result
            self.task_spec.update_status()

            self.task_spec.add_decision(
                agent=AgentType.CODING_AGENT,
                decision_type=DecisionType.OUTPUT,
                content=code_result.to_dict(),
                reasoning=f"Code generation completed: {len(files_created)} created, {len(files_changed)} modified",
                confidence=0.9,
            )

            return code_result

        except Exception as e:
            logger.error(f"Error during code generation: {e}")
            self.task_spec.add_decision(
                agent=AgentType.CODING_AGENT,
                decision_type=DecisionType.ERROR,
                content=str(e),
                reasoning="Error occurred during code generation",
            )
            return self._create_empty_result()

    def _create_implementation_plan(self, spec: Spec, prd: Any) -> dict[str, Any]:
        """基于 Spec 和 PRD 创建实现计划

        Args:
            spec: 技术规格
            prd: 需求规格

        Returns:
            实现计划字典
        """
        plan = {
            "files_to_create": [],
            "files_to_modify": [],
        }

        for model in spec.data_models:
            file_path = f"src/jojo_code/models/{model['name'].lower()}.py"
            plan["files_to_create"].append({
                "path": file_path,
                "content": self._generate_model_code(model),
                "description": f"Data model: {model['name']}",
            })

        for interface in spec.interfaces:
            file_path = f"src/jojo_code/services/{interface['name'].lower()}.py"
            plan["files_to_create"].append({
                "path": file_path,
                "content": self._generate_service_code(interface),
                "description": f"Service: {interface['name']}",
            })

        return plan

    def _generate_model_code(self, model: dict[str, Any]) -> str:
        """生成数据模型代码

        Args:
            model: 数据模型定义

        Returns:
            模型代码字符串
        """
        name = model.get("name", "Model")
        fields = model.get("fields", [])
        description = model.get("description", "")

        lines = [
            '"""Auto-generated data model"""',
            "",
            "from dataclasses import dataclass",
            "from datetime import datetime",
            "from typing import Optional",
            "",
            "",
        ]

        if description:
            lines.append(f'"""{description}"""')
            lines.append("")

        lines.extend([
            "@dataclass",
            f"class {name}:",
        ])

        if not fields:
            lines.append("    pass")
        else:
            for field in fields:
                field_name = field.get("name", "field")
                field_type = field.get("type", "str")
                lines.append(f"    {field_name}: {field_type}")

        return "\n".join(lines)

    def _generate_service_code(self, interface: dict[str, Any]) -> str:
        """生成服务代码

        Args:
            interface: 接口定义

        Returns:
            服务代码字符串
        """
        name = interface.get("name", "Service")
        methods = interface.get("methods", [])
        description = interface.get("description", "")

        class_name = name.lstrip("I")
        if not class_name:
            class_name = "Service"

        lines = [
            '"""Auto-generated service"""',
            "",
            "from typing import Any",
            "",
            "",
        ]

        if description:
            lines.append(f'"""{description}"""')
            lines.append("")

        lines.append(f"class {class_name}:")
        lines.append(f'    """{description or class_name} service"""')
        lines.append("")

        if not methods:
            lines.append("    pass")
        else:
            for method in methods:
                method_name = method.get("name", "execute")
                params = method.get("params", [])
                returns = method.get("returns", "None")

                param_str = ", ".join([f"{p}: Any" for p in params])
                lines.append(f"    def {method_name}(self, {param_str}) -> {returns}:")
                lines.append(f'        """{method.get("description", "")}"""')
                lines.append("        pass")
                lines.append("")

        return "\n".join(lines)

    def _create_file(self, file_action: dict[str, Any]) -> dict[str, Any]:
        """创建文件

        Args:
            file_action: 文件操作信息

        Returns:
            操作结果字典
        """
        path = file_action["path"]
        content = file_action["content"]

        try:
            if self.tool_registry:
                result = self.tool_registry.execute("write_file", {
                    "path": path,
                    "content": content,
                })
                return {"success": True, "path": path, "message": result}
            else:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                Path(path).write_text(content, encoding="utf-8")
                return {"success": True, "path": path}

        except Exception as e:
            logger.error(f"Failed to create file {path}: {e}")
            return {"success": False, "path": path, "error": str(e)}

    def _modify_file(self, file_action: dict[str, Any]) -> dict[str, Any]:
        """修改文件

        Args:
            file_action: 文件操作信息

        Returns:
            操作结果字典
        """
        path = file_action["path"]

        try:
            if self.tool_registry:
                result = self.tool_registry.execute("edit_file", {
                    "path": path,
                    "old_text": file_action.get("old_text", ""),
                    "new_text": file_action.get("new_text", ""),
                })
                return {"success": True, "path": path, "message": result}
            else:
                return {"success": False, "path": path, "error": "tool_registry not available"}

        except Exception as e:
            logger.error(f"Failed to modify file {path}: {e}")
            return {"success": False, "path": path, "error": str(e)}

    def _run_tests(self) -> dict[str, Any]:
        """运行测试

        Returns:
            测试结果字典
        """
        try:
            if self.tool_registry:
                result = self.tool_registry.execute("run_command", {
                    "command": "python -m pytest tests/ -v --tb=short",
                    "timeout": 60,
                })

                passed = "passed" in result.lower() or "PASSED" in result
                failed = "failed" in result.lower() or "FAILED" in result

                return {
                    "passed": passed and not failed,
                    "output": result[:500],
                    "command": "python -m pytest tests/ -v --tb=short",
                }
            else:
                return {
                    "passed": False,
                    "output": "tool_registry not available",
                    "command": "python -m pytest tests/ -v --tb=short",
                }

        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return {
                "passed": False,
                "error": str(e),
                "command": "python -m pytest tests/ -v --tb=short",
            }

    def _generate_diff_summary(self, files_created: list[str], files_changed: list[str]) -> str:
        """生成差异摘要

        Args:
            files_created: 创建的文件列表
            files_changed: 修改的文件列表

        Returns:
            差异摘要字符串
        """
        parts = []
        if files_created:
            parts.append(f"Created {len(files_created)} file(s): {', '.join(files_created)}")
        if files_changed:
            parts.append(f"Modified {len(files_changed)} file(s): {', '.join(files_changed)}")

        return "\n".join(parts) if parts else "No files changed"

    def _create_empty_result(self) -> CodeResult:
        """创建空的代码结果

        Returns:
            空的 CodeResult
        """
        return CodeResult(
            files_changed=[],
            files_created=[],
            diff_summary="No code generated",
            test_results={"passed": False, "error": "No spec available"},
            metadata={"error": "No spec available"},
        )


__all__ = ["CodingAgent"]
