"""
聯網搜索工具
使用 Tavily API 進行網絡搜索
"""
from typing import Optional
from langchain.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from loguru import logger
import os


def create_tavily_tool(max_results: int = 5, search_depth: str = "advanced") -> Optional[Tool]:
    """
    創建 Tavily 搜索工具

    Args:
        max_results: 最大返回結果數量
        search_depth: 搜索深度（"basic" 或 "advanced"）

    Returns:
        Tavily 搜索工具實例，如果 API key 未配置則返回 None
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        logger.warning("⚠️  TAVILY_API_KEY 未設置，Tavily 搜索工具將不可用")
        logger.info("💡 提示: 在 .env 文件中設置 TAVILY_API_KEY 以啟用聯網搜索功能")
        return None

    try:
        # 創建 Tavily 搜索工具
        tavily_tool = TavilySearchResults(
            max_results=max_results,
            search_depth=search_depth,
            include_answer=True,
            include_raw_content=False,
            include_images=False,
        )

        logger.info("✅ Tavily 搜索工具創建成功")
        return tavily_tool

    except Exception as e:
        logger.error(f"❌ 創建 Tavily 搜索工具失敗: {e}")
        return None


def create_web_search_tool() -> Tool:
    """
    創建通用的網絡搜索工具
    如果 Tavily 不可用，使用 DuckDuckGo 作為備選

    Returns:
        網絡搜索工具
    """
    # 優先使用 Tavily
    tavily_tool = create_tavily_tool()
    if tavily_tool:
        return tavily_tool

    # 備選方案：使用 DuckDuckGo
    try:
        from langchain_community.tools import DuckDuckGoSearchRun

        ddg_tool = DuckDuckGoSearchRun(
            name="web_search",
            description="搜索互聯網以獲取最新信息。適用於查找新聞、技術文檔、CVE 信息等。輸入應該是一個搜索查詢。"
        )

        logger.info("✅ 使用 DuckDuckGo 搜索工具")
        return ddg_tool

    except Exception as e:
        logger.error(f"❌ 創建網絡搜索工具失敗: {e}")
        # 返回一個虛擬工具
        return Tool(
            name="web_search",
            func=lambda x: "網絡搜索功能不可用。請檢查 TAVILY_API_KEY 或網絡連接。",
            description="網絡搜索工具（當前不可用）"
        )
