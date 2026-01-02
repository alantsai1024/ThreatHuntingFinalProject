"""
命令行界面
提供交互式對話界面
"""
import sys
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from loguru import logger

from agents.security_agent import SecurityAgent


class ChatCLI:
    """交互式命令行界面"""

    def __init__(
        self,
        agent: SecurityAgent,
        history_file: str = ".chat_history"
    ):
        """
        初始化 CLI

        Args:
            agent: SecurityAgent 實例
            history_file: 聊天歷史文件路徑
        """
        self.agent = agent
        self.console = Console()
        self.chat_history: List = []
        self.history_file = history_file

        # 創建提示會話
        self.session = PromptSession(
            history=FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory()
        )

        self._show_welcome()

    def _show_welcome(self):
        """顯示歡迎信息"""
        welcome_text = """
# 🛡️  Wazuh 安全分析助手

您好！我是您的專業安全分析助手，可以幫助您：

- 🔍 分析 Wazuh SIEM 警報和事件
- 📊 監控代理狀態和系統健康度
- 🐛 檢測漏洞並提供修復建議
- 🌐 搜索最新的安全情報和 CVE 信息
- 📚 提供安全最佳實踐指導

**使用方式**: 直接輸入您的問題，我會智能調用相應工具來幫助您。

**特殊命令**:
- `/tools` - 查看可用工具列表
- `/clear` - 清除對話歷史
- `/exit` 或 `/quit` - 退出程序

---
        """

        self.console.print(Panel(
            Markdown(welcome_text),
            title="[bold blue]歡迎使用[/bold blue]",
            border_style="blue"
        ))

    def _show_tools(self):
        """顯示可用工具"""
        tools_info = self.agent.get_tools_info()

        self.console.print("\n[bold cyan]🛠️  可用工具列表:[/bold cyan]\n")

        for i, tool_info in enumerate(tools_info, 1):
            self.console.print(
                f"  [yellow]{i}.[/yellow] [bold green]{tool_info['name']}[/bold green]"
            )
            self.console.print(f"     {tool_info['description']}\n")

    def _format_assistant_message(self, message: str) -> None:
        """格式化並顯示助手消息"""
        # 使用 Markdown 渲染
        markdown = Markdown(message)
        self.console.print(Panel(
            markdown,
            title="[bold green]🤖 助手[/bold green]",
            border_style="green"
        ))

    def _format_user_message(self, message: str) -> None:
        """格式化並顯示用戶消息"""
        self.console.print(Panel(
            message,
            title="[bold blue]👤 您[/bold blue]",
            border_style="blue"
        ))

    def _show_thinking(self):
        """顯示思考動畫"""
        return self.console.status("[bold yellow]🤔 思考中...[/bold yellow]")

    async def run(self):
        """運行交互式對話循環"""
        logger.info("🚀 啟動 CLI 界面")

        try:
            while True:
                try:
                    # 獲取用戶輸入
                    user_input = await self.session.prompt_async(
                        [("bold cyan", "❯ ")]
                    )

                    # 處理特殊命令
                    if user_input.strip().lower() in ['/exit', '/quit', 'exit', 'quit']:
                        self.console.print("\n[yellow]👋 再見！感謝使用！[/yellow]\n")
                        break

                    if user_input.strip().lower() == '/clear':
                        self.chat_history.clear()
                        self.console.print("[green]✓ 對話歷史已清除[/green]\n")
                        continue

                    if user_input.strip().lower() == '/tools':
                        self._show_tools()
                        continue

                    if not user_input.strip():
                        continue

                    # 顯示用戶消息
                    self._format_user_message(user_input)
                    self.console.print()

                    # 執行 Agent 並顯示響應
                    with self._show_thinking():
                        response = await self.agent.achat(user_input, self.chat_history)

                    # 顯示助手回應
                    self._format_assistant_message(response.get('output', ''))
                    self.console.print()

                    # 更新對話歷史
                    # (注意：這裡可以根據需要調整歷史記錄的格式)
                    # self.chat_history.extend([...])

                except KeyboardInterrupt:
                    self.console.print("\n\n[yellow]⚠️  按 Ctrl+C 再次退出[/yellow]\n")
                    continue

                except Exception as e:
                    logger.error(f"❌ 處理錯誤: {e}")
                    self.console.print(f"\n[red]❌ 發生錯誤: {e}[/red]\n")

        except Exception as e:
            logger.error(f"❌ CLI 運行錯誤: {e}")
            self.console.print(f"\n[red]❌ 严重錯誤: {e}[/red]\n")
            sys.exit(1)


async def run_interactive_cli(agent: SecurityAgent):
    """
    運行交互式 CLI 的便捷函數

    Args:
        agent: SecurityAgent 實例
    """
    cli = ChatCLI(agent)
    await cli.run()
