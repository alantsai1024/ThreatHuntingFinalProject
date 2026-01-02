"""
安全分析代理程序
使用 LangChain 創建智能安全分析助手
"""
from typing import List, Optional, Dict, Any
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger

from config import get_config


class SecurityAgent:
    """安全分析代理程序"""

    # 系統提示詞
    SYSTEM_PROMPT = """你是一個專業的安全分析助手，專精於 Wazuh SIEM 系統和威脅檢測。你可以幫助用戶：

🔍 **安全監控與分析**
- 分析 Wazuh 警報並識別潛在威脅
- 檢查代理狀態和系統健康度
- 監控進程和網絡連接
- 評估漏洞並提供建議

📊 **事件響應**
- 調查安全事件並提供詳細分析
- 建議應對措施和修復步驟
- 關聯多個來源的信息
- 提供符合安全最佳實踐的建議

🛠️ **工具能力**
你有權訪問以下工具：
- **Wazuh 工具**: 獲取警報、代理信息、漏洞、進程、端口、規則、日誌等
- **知識庫檢索**: 搜索安全最佳實踐和故障排除指南
- **網絡搜索**: 查找最新的 CVE、威脅情報和技術文檔
- **系統工具**: 計算、時間查詢等輔助功能

🎯 **工作流程**
1. 理解用戶的問題或請求
2. 選擇最合適的工具來獲取信息
3. 分析數據並從知識庫中檢索相關背景
4. 綜合信息並提供清晰、可操作的建議
5. 如需更多上下文，使用網絡搜索查找最新信息

💡 **回答風格**
- 使用繁體中文回答
- 結構化地呈現信息（使用列表、標題等）
- 提供具體的數據和建議
- 在不確定時說明並建議後續步驟
- 優先考慮安全性和風險緩解

🚨 **安全第一**
- 始終優先考慮安全性
- 對關鍵警報立即標註風險等級
- 提供符合行業標準的最佳實踐
- 在發現嚴重問題時強調需要立即採取行動
"""

    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        tools: Optional[List[BaseTool]] = None,
        verbose: bool = True
    ):
        """
        初始化安全代理

        Args:
            llm: 語言模型實例
            tools: 工具列表
            verbose: 是否顯示詳細輸出
        """
        config = get_config()

        # 初始化 LLM
        self.llm = llm or self._create_llm(config)

        # 初始化工具
        self.tools = tools or []

        # 創建 Agent
        self.agent_executor = self._create_agent(verbose)

        logger.info("✅ 安全代理初始化完成")

    def _create_llm(self, config) -> ChatOpenAI:
        """創建 LLM 實例"""
        llm = ChatOpenAI(
            model=config.llm.model,
            temperature=config.llm.temperature,
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            streaming=True
        )
        logger.info(f"🤖 初始化 LLM: {config.llm.model}")
        return llm

    def _create_agent(self, verbose: bool) -> AgentExecutor:
        """創建 Agent Executor"""
        # 創建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 創建 agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        # 創建 executor
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=10,
            early_stopping_method="generate"
        )

        logger.info(f"🛠️  Agent 已加載 {len(self.tools)} 個工具")
        return executor

    def chat(self, message: str, chat_history: Optional[List] = None) -> Dict[str, Any]:
        """
        與 Agent 對話

        Args:
            message: 用戶消息
            chat_history: 對話歷史

        Returns:
            Agent 響應結果
        """
        try:
            logger.info(f"👤 用戶: {message}")

            # 構建輸入
            inputs = {
                "input": message
            }

            if chat_history:
                inputs["chat_history"] = chat_history

            # 執行 Agent
            response = self.agent_executor.invoke(inputs)

            logger.info(f"🤖 Agent: {response.get('output', '')[:100]}...")
            return response

        except Exception as e:
            error_msg = f"Agent 執行錯誤: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "output": f"抱歉，發生錯誤：{error_msg}",
                "error": True
            }

    async def achat(self, message: str, chat_history: Optional[List] = None) -> Dict[str, Any]:
        """
        異步與 Agent 對話

        Args:
            message: 用戶消息
            chat_history: 對話歷史

        Returns:
            Agent 響應結果
        """
        try:
            logger.info(f"👤 用戶: {message}")

            # 構建輸入
            inputs = {
                "input": message
            }

            if chat_history:
                inputs["chat_history"] = chat_history

            # 執行 Agent（異步）
            response = await self.agent_executor.ainvoke(inputs)

            logger.info(f"🤖 Agent: {response.get('output', '')[:100]}...")
            return response

        except Exception as e:
            error_msg = f"Agent 異步執行錯誤: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "output": f"抱歉，發生錯誤：{error_msg}",
                "error": True
            }

    def stream_chat(self, message: str, chat_history: Optional[List] = None):
        """
        流式與 Agent 對話

        Args:
            message: 用戶消息
            chat_history: 對話歷史

        Yields:
            流式響應片段
        """
        try:
            logger.info(f"👤 用戶: {message}")

            # 構建輸入
            inputs = {
                "input": message
            }

            if chat_history:
                inputs["chat_history"] = chat_history

            # 流式執行 Agent
            for chunk in self.agent_executor.stream(inputs):
                yield chunk

        except Exception as e:
            error_msg = f"流式執行錯誤: {str(e)}"
            logger.error(f"❌ {error_msg}")
            yield {"output": f"抱歉，發生錯誤：{error_msg}", "error": True}

    def get_tools_info(self) -> List[Dict[str, str]]:
        """
        獲取所有工具的信息

        Returns:
            工具信息列表
        """
        tools_info = []
        for tool in self.tools:
            info = {
                "name": tool.name,
                "description": tool.description,
            }
            tools_info.append(info)
        return tools_info

    def add_tool(self, tool: BaseTool):
        """
        添加新工具

        Args:
            tool: 要添加的工具
        """
        self.tools.append(tool)
        # 重新創建 agent
        self.agent_executor = self._create_agent(verbose=True)
        logger.info(f"➕ 添加新工具: {tool.name}")

    def remove_tool(self, tool_name: str):
        """
        移除工具

        Args:
            tool_name: 工具名稱
        """
        self.tools = [t for t in self.tools if t.name != tool_name]
        # 重新創建 agent
        self.agent_executor = self._create_agent(verbose=True)
        logger.info(f"➖ 移除工具: {tool_name}")


def create_security_agent(
    tools: List[BaseTool],
    verbose: bool = True
) -> SecurityAgent:
    """
    創建安全代理的便捷函數

    Args:
        tools: 工具列表
        verbose: 是否顯示詳細輸出

    Returns:
        SecurityAgent 實例
    """
    return SecurityAgent(tools=tools, verbose=verbose)
