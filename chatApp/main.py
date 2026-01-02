"""
Wazuh Security Analyst - LangChain AgenticRAG 應用

這是一個智能的安全分析助手，結合了：
- Wazuh MCP Server: 獲取 SIEM 數據
- LangChain Agent: 智能工具調用和對話
- RAG 知識庫: 安全最佳實踐和文檔
- 聯網搜索: 最新威脅情報

作者: Threat Hunting Final Project
版本: 1.0.0
"""
import asyncio
from pathlib import Path
from loguru import logger
import sys

from config import get_config, get_config_manager
from mcp.client import MCPClientManager
from mcp.wazuh_tools import WazuhToolkit
from rag.retriever import SecurityKnowledgeRetriever
from tools.web_search import create_web_search_tool
from tools.system_tools import calculator_tool, get_current_time, system_status
from agents.security_agent import create_security_agent
from ui.cli import run_interactive_cli


# 配置日誌
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="DEBUG"
)


async def initialize_mcp_client() -> MCPClientManager:
    """
    初始化 MCP 客戶端管理器

    Returns:
        MCPClientManager 實例
    """
    logger.info("🔌 初始化 MCP 客戶端...")

    config_manager = get_config_manager()
    mcp_config = config_manager.load_mcp_config()

    manager = MCPClientManager()

    # 遍歷配置的 MCP 服務器
    for server_name, server_config in mcp_config.get("mcpServers", {}).items():
        logger.info(f"📡 連接 MCP 服務器: {server_name}")
        success = await manager.add_server(server_name, server_config)

        if success:
            logger.info(f"✅ {server_name} 連接成功")
        else:
            logger.warning(f"⚠️  {server_name} 連接失敗")

    return manager


def create_tools(mcp_manager: MCPClientManager) -> list:
    """
    創建所有工具

    Args:
        mcp_manager: MCP 客戶端管理器

    Returns:
        工具列表
    """
    tools = []
    logger.info("🛠️  創建工具集...")

    # 1. Wazuh MCP 工具
    wazuh_client = mcp_manager.get_client("wazuh")
    if wazuh_client:
        logger.info("✅ 添加 Wazuh MCP 工具")
        wazuh_toolkit = WazuhToolkit(wazuh_client)
        wazuh_tools = wazuh_toolkit.get_tools()
        tools.extend(wazuh_tools)
        logger.info(f"   - 已添加 {len(wazuh_tools)} 個 Wazuh 工具")
    else:
        logger.warning("⚠️  Wazuh MCP 客戶端未連接，跳過 Wazuh 工具")

    # 2. 聯網搜索工具
    logger.info("✅ 添加聯網搜索工具")
    web_search_tool = create_web_search_tool()
    if web_search_tool:
        tools.append(web_search_tool)

    # 3. 系統工具
    logger.info("✅ 添加系統工具")
    tools.extend([
        calculator_tool,
        get_current_time,
        system_status
    ])

    logger.info(f"🎉 總共創建了 {len(tools)} 個工具")
    return tools


async def main():
    """主函數"""
    # 打印啟動信息
    console_print = """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║        🛡️  Wazuh Security Analyst Agent 🛡️           ║
    ║                                                       ║
    ║        LangChain AgenticRAG 應用 v1.0.0              ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    logger.info(console_print)

    try:
        # 1. 加載配置
        logger.info("⚙️  加載配置...")
        config = get_config()
        logger.info(f"✅ 配置加載成功")
        logger.info(f"   - LLM: {config.llm.model}")
        logger.info(f"   - Base URL: {config.llm.base_url}")

        # 2. 初始化 MCP 客戶端
        mcp_manager = await initialize_mcp_client()

        if not mcp_manager.get_all_clients():
            logger.error("❌ 沒有成功連接任何 MCP 服務器，無法繼續")
            logger.info("💡 請確保 Wazuh MCP server 正在運行")
            logger.info("   在 mcp-server-wazuh 目錄下執行: cargo run")
            return

        # 3. 創建工具集
        tools = create_tools(mcp_manager)

        # 4. 初始化 RAG 檢索器（可選）
        logger.info("📚 初始化知識庫檢索器...")
        try:
            retriever = SecurityKnowledgeRetriever()
            logger.info("✅ RAG 檢索器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️  RAG 檢索器初始化失敗: {e}")
            logger.info("   將繼續使用其他工具")

        # 5. 創建 Agent
        logger.info("🤖 創建安全分析 Agent...")
        agent = create_security_agent(tools=tools, verbose=True)
        logger.info("✅ Agent 創建成功")

        # 顯示可用工具
        tools_info = agent.get_tools_info()
        logger.info(f"🛠️  Agent 已加載 {len(tools_info)} 個工具:")
        for tool_info in tools_info[:5]:  # 只顯示前 5 個
            logger.info(f"   - {tool_info['name']}")
        if len(tools_info) > 5:
            logger.info(f"   - 還有 {len(tools_info) - 5} 個工具...")

        # 6. 啟動 CLI
        logger.info("🚀 啟動交互式界面...\n")
        await run_interactive_cli(agent)

    except KeyboardInterrupt:
        logger.info("\n\n👋 程序已用戶中斷")
    except Exception as e:
        logger.error(f"❌ 程序執行錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("🔚 程序結束")


if __name__ == "__main__":
    # 運行主程序
    asyncio.run(main())
