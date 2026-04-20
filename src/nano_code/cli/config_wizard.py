"""交互式配置向导

首次运行时引导用户配置 API Key 和模型。
"""

import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()


# 支持的 API 提供商
PROVIDERS = {
    "1": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    },
    "2": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models": ["auto", "anthropic/claude-3.5-sonnet", "openai/gpt-4o"],
    },
    "3": {"name": "Azure OpenAI", "base_url": None, "models": ["gpt-4o", "gpt-4o-mini"]},
    "4": {
        "name": "LongCat",
        "base_url": "https://api.longcat.ai/v1",
        "models": ["gpt-4o", "gpt-4o-mini"],
    },
    "5": {"name": "自定义", "base_url": None, "models": []},
}


class ConfigWizard:
    """配置向导

    引导用户完成首次配置，包括 API 提供商、API Key、模型等。

    使用示例:
        >>> wizard = ConfigWizard()
        >>> if wizard.check_config():
        ...     wizard.run()
    """

    def __init__(self, config_path: Path | None = None):
        """初始化配置向导

        Args:
            config_path: 配置文件路径，默认为 ~/.nano-code/.env
        """
        self.config_path = config_path or (Path.home() / ".nano-code" / ".env")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.api_key: str | None = None
        self.base_url: str | None = None
        self.model: str = "gpt-4o-mini"
        self.provider: str = "OpenAI"

    def check_config(self) -> bool:
        """检查配置是否完整

        Returns:
            配置是否完整
        """
        # 检查环境变量
        if os.getenv("OPENAI_API_KEY"):
            return True

        # 检查配置文件
        if self.config_path.exists():
            content = self.config_path.read_text(encoding="utf-8")
            if "OPENAI_API_KEY" in content and "=" in content:
                return True

        return False

    def run(self) -> bool:
        """运行配置向导

        Returns:
            配置是否成功
        """
        console.print(
            Panel.fit(
                "🔧 [bold]欢迎使用 Nano Code！[/bold]\n\n检测到这是首次运行，需要进行配置。",
                title="配置向导",
                border_style="blue",
            )
        )

        # 选择提供商
        self._select_provider()

        # 输入 API Key
        self.api_key = self._prompt_api_key()
        if not self.api_key:
            console.print("[red]❌ API Key 不能为空[/red]")
            return False

        # 输入 Base URL（如果需要）
        if self._needs_base_url():
            self.base_url = self._prompt_base_url()

        # 选择模型
        self.model = self._prompt_model()

        # 保存配置
        if self.save_config():
            console.print(f"\n[green]✅ 配置已保存到 {self.config_path}[/green]")
            return True

        return False

    def _select_provider(self) -> None:
        """选择 API 提供商"""
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("序号", style="dim")
        table.add_column("提供商")
        table.add_column("默认 Base URL", style="dim")

        for key, provider in PROVIDERS.items():
            table.add_row(key, provider["name"], provider.get("base_url") or "需手动输入")

        console.print(table)

        choice = Prompt.ask(
            "\n请选择 API 提供商",
            choices=list(PROVIDERS.keys()),
            default="1",
        )

        self.provider = PROVIDERS[choice]["name"]
        if PROVIDERS[choice]["base_url"]:
            self.base_url = PROVIDERS[choice]["base_url"]

        console.print(f"[green]已选择: {self.provider}[/green]")

    def _prompt_api_key(self) -> str | None:
        """提示输入 API Key"""
        console.print(f"\n[bold]请输入 {self.provider} API Key[/bold]")
        console.print("[dim]提示: API Key 不会显示在屏幕上[/dim]")

        return Prompt.ask("API Key", password=True)

    def _needs_base_url(self) -> bool:
        """是否需要手动输入 Base URL"""
        return self.provider in ["Azure OpenAI", "自定义"]

    def _prompt_base_url(self) -> str | None:
        """提示输入 Base URL"""
        console.print(f"\n[bold]请输入 {self.provider} API Base URL[/bold]")
        console.print(
            "[dim]示例: https://your-resource.openai.azure.com/openai/deployments/your-deployment[/dim]"
        )

        return Prompt.ask("Base URL")

    def _prompt_model(self) -> str:
        """提示选择模型"""
        # 获取当前提供商的模型列表
        provider_info = next((p for p in PROVIDERS.values() if p["name"] == self.provider), None)
        models = provider_info["models"] if provider_info else []

        if models:
            console.print("\n[bold]请选择模型[/bold]")

            table = Table(show_header=False)
            for i, model in enumerate(models, 1):
                table.add_row(f"{i}. {model}")
            table.add_row(f"{len(models) + 1}. 其他（手动输入）")
            console.print(table)

            choice = Prompt.ask(
                "选择模型",
                choices=[str(i) for i in range(1, len(models) + 2)],
                default="2",  # 默认 gpt-4o-mini
            )

            idx = int(choice)
            if idx <= len(models):
                return models[idx - 1]

        # 手动输入模型
        return Prompt.ask("请输入模型名称", default="gpt-4o-mini")

    def save_config(self) -> bool:
        """保存配置到文件

        Returns:
            保存是否成功
        """
        try:
            lines = [
                "# Nano Code 配置文件",
                f"# 提供商: {self.provider}",
                "",
            ]

            if self.api_key:
                lines.append(f"OPENAI_API_KEY={self.api_key}")

            if self.base_url:
                lines.append(f"OPENAI_BASE_URL={self.base_url}")

            lines.append(f"MODEL={self.model}")

            self.config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True

        except Exception as e:
            console.print(f"[red]保存配置失败: {e}[/red]")
            return False

    def load_config(self) -> dict:
        """加载配置

        Returns:
            配置字典
        """
        config = {}

        if self.config_path.exists():
            content = self.config_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()

        return config


def run_wizard_if_needed() -> bool:
    """如果需要则运行配置向导

    Returns:
        配置是否完整
    """
    wizard = ConfigWizard()

    if wizard.check_config():
        return True

    return wizard.run()
