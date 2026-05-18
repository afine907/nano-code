"""任务执行器 - 任务执行逻辑"""

import asyncio
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass

from jojo_code.task.types import (
    Task,
    TaskInput,
    TaskResult,
    TaskStatus,
    TaskType,
)


@dataclass
class TaskExecutorConfig:
    """任务执行器配置"""

    max_concurrent: int = 5  # 最大并发任务数
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟 (秒)
    timeout: float | None = None  # 任务超时 (秒)
    output_dir: str = ".jojo-code/output"  # 输出目录


# 任务执行函数类型
TaskFunc = Callable[[TaskInput], TaskResult]


class TaskExecutor:
    """任务执行器

    负责执行任务，支持:
    - 同步/异步执行
    - 并发控制
    - 重试机制
    - 超时控制
    - 进度追踪
    """

    def __init__(self, config: TaskExecutorConfig | None = None):
        self.config = config or TaskExecutorConfig()
        self._executors: dict[TaskType, TaskFunc] = {}
        self._running_tasks: dict[str, Future] = {}
        self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_concurrent)
        self._locks: dict[str, asyncio.Lock] = {}

    def register(self, task_type: TaskType, func: TaskFunc) -> None:
        """注册任务执行函数

        Args:
            task_type: 任务类型
            func: 执行函数
        """
        self._executors[task_type] = func

    def unregister(self, task_type: TaskType) -> bool:
        """注销任务执行函数

        Args:
            task_type: 任务类型

        Returns:
            是否成功注销
        """
        return self._executors.pop(task_type, None) is not None

    def execute(self, task: Task) -> TaskResult:
        """同步执行任务

        Args:
            task: 任务

        Returns:
            任务结果
        """
        if task.input is None:
            return TaskResult(success=False, error="任务没有输入")

        # 获取执行函数
        executor = self._executors.get(task.type)
        if executor is None:
            return TaskResult(
                success=False,
                error=f"未注册的任务类型: {task.type}",
            )

        # 标记开始
        task.start()

        try:
            # 执行任务
            result = executor(task.input)

            # 标记完成
            task.complete(result)
            return result

        except Exception as e:
            # 标记失败
            task.fail(str(e))
            return TaskResult(success=False, error=str(e))

    def submit(self, task: Task, callback: Callable[[Task], None] | None = None) -> str:
        """提交任务异步执行

        Args:
            task: 任务
            callback: 完成回调

        Returns:
            任务 ID
        """
        # 提交到线程池
        future = self._thread_pool.submit(self.execute, task)
        self._running_tasks[task.id] = future

        # 设置回调
        if callback:
            future.add_done_callback(lambda f: callback(task))

        return task.id

    def submit_with_retry(
        self,
        task: Task,
        max_retries: int | None = None,
        callback: Callable[[Task], None] | None = None,
    ) -> str:
        """提交任务带重试

        Args:
            task: 任务
            max_retries: 最大重试次数
            callback: 完成回调

        Returns:
            任务 ID
        """
        max_retries = max_retries or self.config.max_retries

        def run_with_retry():
            attempts = 0
            while attempts < max_retries:
                try:
                    result = self.execute(task)
                    if result.success:
                        return result
                except Exception:
                    pass

                attempts += 1
                if attempts < max_retries:
                    import time

                    time.sleep(self.config.retry_delay * attempts)

            return TaskResult(success=False, error="重试次数耗尽")

        task.input = TaskInput(
            tool_name="retry_wrapper",
            args={"task_id": task.id},
            description=f"带重试的任务: {task.id}",
        )

        future = self._thread_pool.submit(run_with_retry)
        self._running_tasks[task.id] = future

        if callback:
            future.add_done_callback(lambda f: callback(task))

        return task.id

    def cancel(self, task_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务 ID

        Returns:
            是否成功取消
        """
        if task_id in self._running_tasks:
            future = self._running_tasks[task_id]
            cancelled = future.cancel()
            if cancelled:
                del self._running_tasks[task_id]
            return cancelled
        return False

    def get_status(self, task_id: str) -> TaskStatus | None:
        """获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态，如果任务不存在则返回 None
        """
        if task_id in self._running_tasks:
            future = self._running_tasks[task_id]
            if future.done():
                return TaskStatus.COMPLETED
            return TaskStatus.RUNNING
        return None

    def wait(self, task_id: str, timeout: float | None = None) -> TaskResult | None:
        """等待任务完成

        Args:
            task_id: 任务 ID
            timeout: 超时时间 (秒)

        Returns:
            任务结果，如果超时则返回 None
        """
        if task_id not in self._running_tasks:
            return None

        future = self._running_tasks[task_id]
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            return None

    def shutdown(self, wait: bool = True) -> None:
        """关闭执行器

        Args:
            wait: 是否等待正在执行的任务
        """
        self._thread_pool.shutdown(wait=wait)
        self._running_tasks.clear()


# 预置执行器工厂
class ExecutorFactory:
    """执行器工厂"""

    @staticmethod
    def create_bash_executor() -> TaskFunc:
        """创建 Bash 执行器"""

        def executor(input: TaskInput) -> TaskResult:
            import subprocess

            cmd = input.args.get("command", "")
            timeout = input.args.get("timeout", 300)

            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                return TaskResult(
                    success=result.returncode == 0,
                    output={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                    },
                    error=None if result.returncode == 0 else result.stderr,
                )
            except subprocess.TimeoutExpired:
                return TaskResult(success=False, error="命令执行超时")
            except Exception as e:
                return TaskResult(success=False, error=str(e))

        return executor

    @staticmethod
    def create_agent_executor() -> TaskFunc:
        """创建 Agent 执行器"""

        def executor(input: TaskInput) -> TaskResult:
            # TODO: 实现 Agent 执行器
            return TaskResult(success=False, error="Agent 执行器未实现")

        return executor


__all__ = [
    "TaskExecutor",
    "TaskExecutorConfig",
    "TaskFunc",
    "ExecutorFactory",
]
