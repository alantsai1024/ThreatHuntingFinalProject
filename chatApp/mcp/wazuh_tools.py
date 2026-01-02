"""
Wazuh MCP 工具包
將 MCP 工具轉換為 LangChain 工具格式
"""
from typing import Dict, Any, Optional, List
from langchain.tools import StructuredTool
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
import asyncio
from loguru import logger

from .client import MCPClient


class WazToolConfig:
    """Wazuh 工具配置"""

    # Wazuh 工具定義（基於 MCP server 的工具列表）
    WAZUH_TOOLS = {
        "get_wazuh_alert_summary": {
            "description": "獲取 Wazuh 安全警報摘要。返回最近的安全警報信息，包括警報 ID、時間戳、描述等。",
            "parameters": {
                "limit": {"type": "integer", "description": "返回的最大警報數量（默認 100）"}
            }
        },
        "get_wazuh_agents": {
            "description": "獲取 Wazuh 代理列表。返回所有代理的詳細信息，包括 ID、名稱、IP、狀態、操作系統等。",
            "parameters": {
                "status": {"type": "string", "description": "過濾代理狀態（active, disconnected, pending, never_connected）"},
                "limit": {"type": "integer", "description": "返回的最大代理數量（默認 300）"}
            }
        },
        "get_wazuh_vulnerability_summary": {
            "description": "獲取指定代理的漏洞摘要。返回代理檢測到的漏洞信息，包括 CVE ID、嚴重性等。",
            "parameters": {
                "agent_id": {"type": "string", "description": "代理 ID（例如 '001', '002'）", "required": True},
                "severity": {"type": "string", "description": "過濾漏洞嚴重性（Low, Medium, High, Critical）"},
                "limit": {"type": "integer", "description": "返回的最大漏洞數量（默認 10000）"}
            }
        },
        "get_wazuh_critical_vulnerabilities": {
            "description": "獲取指定代理的關鍵漏洞。只返回 Critical 級別的漏洞。",
            "parameters": {
                "agent_id": {"type": "string", "description": "代理 ID（例如 '001', '002'）", "required": True},
                "limit": {"type": "integer", "description": "返回的最大漏洞數量（默認 300）"}
            }
        },
        "get_wazuh_agent_processes": {
            "description": "獲取指定代理上運行的進程列表。返回進程的 PID、名稱、狀態、用戶和命令行等信息。",
            "parameters": {
                "agent_id": {"type": "string", "description": "代理 ID（例如 '001', '002'）", "required": True},
                "search": {"type": "string", "description": "搜索過濾器，按進程名稱或命令過濾"},
                "limit": {"type": "integer", "description": "返回的最大進程數量（默認 300）"}
            }
        },
        "get_wazuh_agent_ports": {
            "description": "獲取指定代理的網絡端口信息。返回打開的端口、協議、狀態和關聯的進程等信息。",
            "parameters": {
                "agent_id": {"type": "string", "description": "代理 ID（例如 '001', '002'）", "required": True},
                "protocol": {"type": "string", "description": "協議過濾器（tcp, udp）", "required": True},
                "state": {"type": "string", "description": "狀態過濾器（LISTENING, ESTABLISHED 等）", "required": True},
                "limit": {"type": "integer", "description": "返回的最大端口數量（默認 300）"}
            }
        },
        "get_wazuh_rules_summary": {
            "description": "獲取 Wazuh 安全規則摘要。返回檢測規則的詳細信息，包括規則 ID、級別、描述和組別。",
            "parameters": {
                "level": {"type": "integer", "description": "過濾規則級別"},
                "group": {"type": "string", "description": "過濾規則組別"},
                "limit": {"type": "integer", "description": "返回的最大規則數量（默認 300）"}
            }
        },
        "search_wazuh_manager_logs": {
            "description": "搜索 Wazuh 管理器日誌。返回匹配搜索條件的日誌條目。",
            "parameters": {
                "level": {"type": "string", "description": "日誌級別（error, warning, info）", "required": True},
                "search_term": {"type": "string", "description": "搜索關鍵詞"},
                "tag": {"type": "string", "description": "日誌標籤過濾器"},
                "limit": {"type": "integer", "description": "返回的最大日誌條目數量（默認 300）"}
            }
        },
        "get_wazuh_manager_error_logs": {
            "description": "獲取 Wazuh 管理器錯誤日誌。返回所有錯誤級別的日誌條目。",
            "parameters": {
                "limit": {"type": "integer", "description": "返回的最大日誌條目數量（默認 300）"}
            }
        },
        "get_wazuh_cluster_health": {
            "description": "獲取 Wazuh 集群健康狀態。返回集群是否啟用、運行中以及節點連接狀態。",
            "parameters": {}
        },
        "get_wazuh_cluster_nodes": {
            "description": "獲取 Wazuh 集群節點列表。返回集群中所有節點的詳細信息，包括名稱、類型、版本、IP 和狀態。",
            "parameters": {
                "node_type": {"type": "string", "description": "過濾節點類型（master, worker）"},
                "limit": {"type": "integer", "description": "返回的最大節點數量（默認 500）"}
            }
        },
        "get_wazuh_weekly_stats": {
            "description": "獲取 Wazuh 管理器週統計數據。返回過去一週各種指標的匯總統計。",
            "parameters": {}
        },
        "get_wazuh_remoted_stats": {
            "description": "獲取 Wazuh remoted 守護進程統計數據。返回隊列大小、TCP 會話、事件計數和消息流量等信息。",
            "parameters": {}
        },
        "get_wazuh_log_collector_stats": {
            "description": "獲取指定代理的日誌收集器統計。返回已處理、丟棄的事件、字節數和目標日誌文件等信息。",
            "parameters": {
                "agent_id": {"type": "string", "description": "代理 ID（例如 '001', '002'）", "required": True}
            }
        }
    }


def create_wazuh_tools(mcp_client: MCPClient) -> List[Tool]:
    """
    創建 Wazuh LangChain 工具列表

    Args:
        mcp_client: MCP 客戶端實例

    Returns:
        LangChain 工具列表
    """
    tools = []

    for tool_name, tool_info in WazToolConfig.WAZUH_TOOLS.items():
        # 創建工具的包裝函數
        def make_tool_wrappers(name: str):
            async def tool_wrapper(*args, **kwargs) -> str:
                """異步工具調用包裝器"""
                try:
                    if args and not kwargs:
                        if len(args) == 1 and isinstance(args[0], dict):
                            kwargs = args[0]
                        else:
                            kwargs = {"input": args[0] if len(args) == 1 else args}

                    logger.info(f"🔧 調用 Wazuh 工具: {name} with args: {kwargs}")
                    result = await mcp_client.call_tool(name, kwargs)

                    # 提取文本內容
                    if result and "content" in result:
                        content_items = result["content"]
                        texts = []
                        for item in content_items:
                            if isinstance(item, dict) and item.get("type") == "text":
                                texts.append(item.get("text", ""))
                        return "\n\n".join(texts) if texts else "無返回結果"
                    else:
                        return "工具執行完成但無返回數據"

                except Exception as e:
                    error_msg = f"執行工具 {name} 時發生錯誤: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    return error_msg

            # 創建同步版本（LangChain 需要）
            def sync_wrapper(*args, **kwargs) -> str:
                """同步工具調用包裝器"""
                return asyncio.run(tool_wrapper(*args, **kwargs))

            return sync_wrapper, tool_wrapper

        # 創建工具描述
        description = tool_info["description"]
        parameters = tool_info.get("parameters", {})

        # 構建參數說明
        if parameters:
            param_desc = "\n參數:\n"
            for param_name, param_info in parameters.items():
                required = param_info.get("required", False)
                desc = param_info.get("description", "")
                param_desc += f"  - {param_name}: {desc} {'(必填)' if required else '(可選)'}\n"
            description += param_desc

        # 創建 LangChain 工具
        sync_wrapper, async_wrapper = make_tool_wrappers(tool_name)
        tool = Tool(
            name=tool_name,
            description=description,
            func=sync_wrapper,
            coroutine=async_wrapper
        )

        tools.append(tool)
        logger.debug(f"✅ 創建工具: {tool_name}")

    logger.info(f"✅ 成功創建 {len(tools)} 個 Wazuh 工具")
    return tools


class WazuhToolkit:
    """Wazuh 工具包，提供便捷的工具創建和管理"""

    def __init__(self, mcp_client: MCPClient):
        """
        初始化 Wazuh 工具包

        Args:
            mcp_client: MCP 客戶端實例
        """
        self.mcp_client = mcp_client
        self._tools: Optional[List[Tool]] = None

    def get_tools(self) -> List[Tool]:
        """
        獲取所有 Wazuh 工具

        Returns:
            LangChain 工具列表
        """
        if self._tools is None:
            self._tools = create_wazuh_tools(self.mcp_client)
        return self._tools

    def get_tool_by_name(self, tool_name: str) -> Optional[Tool]:
        """
        根據名稱獲取工具

        Args:
            tool_name: 工具名稱

        Returns:
            工具實例或 None
        """
        tools = self.get_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None

    def list_tool_names(self) -> List[str]:
        """
        列出所有工具名稱

        Returns:
            工具名稱列表
        """
        return list(WazToolConfig.WAZUH_TOOLS.keys())
