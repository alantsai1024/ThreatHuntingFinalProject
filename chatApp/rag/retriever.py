"""
安全知識庫檢索器
使用向量數據庫進行語義搜索和檢索
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.retrievers import BaseRetriever
from loguru import logger

# 創建安全的知識庫文檔
SECURITY_KNOWLEDGE_BASE = [
    """
    # Wazuh SIEM 安全監控最佳實踐

    ## 1. 警報分級和響應
    Wazuh 使用警報級別（1-16）來指示事件嚴重程度：
    - 級別 1-3: 低風險，信息性事件
    - 級別 4-7: 中等風險，需要關注
    - 級別 8-12: 高風險，需要調查
    - 級別 13-16: 關鍵風險，立即響應

    ## 2. 代理管理
    Wazuh 代理（Agent）是被監控端點上運行的程序：
    - 代理狀態：active（活躍）、disconnected（斷開）、pending（待確認）、never_connected（從未連接）
    - 定期檢查代理狀態以確保監控覆蓋
    - 使用 get_wazuh_agents 工具查看所有代理

    ## 3. 漏洞管理
    Wazuh 可以檢測系統漏洞並進行分級：
    - Critical（關鍵）：立即修復
    - High（高）：優先修復
    - Medium（中）：計劃修復
    - Low（低）：監控即可
    - 使用 get_wazuh_vulnerability_summary 查看漏洞詳情

    ## 4. 進程監控
    監控運行進程可以發現異常行為：
    - 使用 get_wazuh_agent_processes 查看特定代理的進程
    - 關注可疑進程名稱和命令行參數
    - 對比進程列表的變化

    ## 5. 網絡端口監控
    開放端口分析是安全評估的重要部分：
    - 使用 get_wazuh_agent_ports 查看代理的網絡連接
    - 關注未授權的監聽端口（LISTENING 狀態）
    - 檢查可疑的已建立連接（ESTABLISHED 狀態）

    ## 6. 日誌分析
    Wazuh 管理器日誌包含系統運行和事件信息：
    - 使用 search_wazuh_manager_logs 搜索特定日誌
    - 使用 get_wazuh_manager_error_logs 查看錯誤日誌
    - 日誌分析有助於故障排除和事件調查
    """,

    """
    # 威脅檢測和事件響應流程

    ## 威脅檢測
    1. 監控警報摘要（get_wazuh_alert_summary）
    2. 分析高級別警報（級別 >= 8）
    3. 識別攻擊模式和趨勢
    4. 關聯不同代理的事件

    ## 事件調查步驟
    1. 確定受影響的代理
    2. 檢查代理進程（get_wazuh_agent_processes）
    3. 查看網絡連接（get_wazuh_agent_ports）
    4. 搜索相關日誌（search_wazuh_manager_logs）
    5. 檢查漏洞狀態（get_wazuh_vulnerability_summary）

    ## 事件響應
    - 關鍵警報（級別 13-16）需要立即響應
    - 高級別警報（級別 8-12）需要快速調查
    - 記錄所有響應動作
    - 更新安全規則以防止再次發生
    """,

    """
    # Wazuh 集群管理

    ## 集群架構
    Wazuh 支持多節點集群部署：
    - Master 節點：協調集群操作
    - Worker 節點：處理數據和請求

    ## 集群健康監控
    使用以下工具監控集群：
    - get_wazuh_cluster_health：檢查集群整體健康狀態
    - get_wazuh_cluster_nodes：查看所有節點狀態
    - get_wazuh_weekly_stats：查看統計數據

    ## 性能優化
    - 監控 remoted 守護進程統計（get_wazuh_remoted_stats）
    - 檢查日誌收集器統計（get_wazuh_log_collector_stats）
    - 確保負載均衡在節點間合理分配
    """,

    """
    # 常見安全場景和應對策略

    ## 場景 1：可疑 USB 存儲設備連接
    **檢測**：警報描述中包含 "Attached USB Storage"
    **應對**：
    1. 使用 get_wazuh_agent_processes 查看代理進程
    2. 使用 get_wazuh_agent_ports 查看網絡連接
    3. 檢查是否有惡意文件傳輸
    4. 隔離受影響的系統（如需要）

    ## 場景 2：未授權的軟件安裝
    **檢測**：警報包含 "installed" 或軟件包管理器相關信息
    **應對**：
    1. 確認軟件是否經過授權
    2. 檢查代理進程列表
    3. 評估潛在風險
    4. 如未授權，卸載軟件並記錄事件

    ## 場景 3：異常網絡連接
    **檢測**：新的 ESTABLISHED 連接到未知 IP
    **應對**：
    1. 查看網絡端口信息（get_wazuh_agent_ports）
    2. 識別遠程 IP 和端口
    3. 關聯進程信息
    4. 評估是否為數據外洩

    ## 場景 4：漏洞利用嘗試
    **檢測**：警報級別高，包含攻擊特徵碼
    **應對**：
    1. 立即檢查漏洞狀態（get_wazuh_vulnerability_summary）
    2. 查看關鍵漏洞（get_wazuh_critical_vulnerabilities）
    3. 應用補丁或緩解措施
    4. 監控後續活動
    """,

    """
    # 安全規則和檢測機制

    ## Wazuh 規則系統
    Wazuh 使用規則來檢測和分類安全事件：
    - 每個規則有唯一的 ID
    - 規則級別（1-16）指示嚴重程度
    - 規則可以組織成組（groups）

    ## 常見規則組
    - authentication, authentication_failed：認證相關
    - web, web-attack：Web 攻擊
    - malware, ransomware：惡意軟件
    - policy_monitoring：策略違規
    - syslog, system：系統事件

    ## 使用規則信息
    通過 get_wazuh_rules_summary 可以：
    - 查看可用的檢測規則
    - 了解特定級別的規則
    - 檢查特定類型的規則
    - 優化檢測策略
    """,

    """
    # PCI-DSS 合規性監控

    ## PCI-DSS 要求和 Wazuh
    Wazuh 可以幫助滿足 PCI-DSS 的多項要求：

    ### 要求 10：追蹤和監控對網絡資源和持卡人數據的所有訪問
    - 使用警報監控（get_wazuh_alert_summary）
    - 日誌收集和分析（search_wazuh_manager_logs）
    - 代理監控覆蓋（get_wazuh_agents）

    ### 要求 11：定期測試安全系統和流程
    - 漏洞掃描（get_wazuh_vulnerability_summary）
    - 進程監控（get_wazuh_agent_processes）
    - 網絡端口監控（get_wazuh_agent_ports）

    ### 最佳實踐
    - 定期審計日誌
    - 監控所有代理狀態
    - 及時修復關鍵漏洞
    - 記錄所有安全事件
    """,

    """
    # 故障排除指南

    ## 問題：代理顯示 disconnected
    **原因**：
    - 網絡連接問題
    - 代理服務停止
    - 防火牆阻擋

    **解決步驟**：
    1. 檢查網絡連接
    2. 重啟代理服務
    3. 檢查防火牆規則
    4. 查看管理器日誌（get_wazuh_manager_error_logs）

    ## 問題：警報未生成
    **原因**：
    - 規則未啟用
    - 日誌收集問題
    - 配置錯誤

    **解決步驟**：
    1. 檢查規則配置（get_wazuh_rules_summary）
    2. 查看日誌收集器統計（get_wazuh_log_collector_stats）
    3. 搜索相關日誌（search_wazuh_manager_logs）

    ## 問題：集群節點不同步
    **原因**：
    - 網絡延遲
    - 節點過載
    - 配置不一致

    **解決步驟**：
    1. 檢查集群健康（get_wazuh_cluster_health）
    2. 查看節點狀態（get_wazuh_cluster_nodes）
    3. 檢查統計數據（get_wazuh_weekly_stats）
    """,
]


class SecurityKnowledgeRetriever(BaseRetriever):
    """安全知識庫檢索器"""

    def __init__(
        self,
        knowledge_base_path: str = "rag/chroma_db",
        embed_model: Optional[str] = None,
        k: int = 3
    ):
        """
        初始化檢索器

        Args:
            knowledge_base_path: 向量數據庫存儲路徑
            embed_model: 嵌入模型名稱（默認使用 all-MiniLM-L6-v2）
            k: 返回的文檔數量
        """
        super().__init__()
        self.knowledge_base_path = Path(knowledge_base_path)
        self.embed_model = embed_model or "sentence-transformers/all-MiniLM-L6-v2"
        self.k = k
        self._vectorstore: Optional[Chroma] = None
        self._initialized = False

    def _initialize_vectorstore(self):
        """初始化向量數據庫"""
        try:
            # 創建嵌入模型
            embeddings = HuggingFaceEmbeddings(
                model_name=self.embed_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

            # 嘗試加載現有的向量數據庫
            if self.knowledge_base_path.exists():
                logger.info(f"📂 加載現有的向量數據庫: {self.knowledge_base_path}")
                self._vectorstore = Chroma(
                    persist_directory=str(self.knowledge_base_path),
                    embedding_function=embeddings
                )
                logger.info("✅ 向量數據庫加載成功")
            else:
                # 創建新的向量數據庫
                logger.info("📝 創建新的向量數據庫")
                self._vectorstore = self._create_vectorstore(embeddings)
                logger.info("✅ 向量數據庫創建成功")

            self._initialized = True

        except Exception as e:
            logger.error(f"❌ 初始化向量數據庫失敗: {e}")
            raise

    def _create_vectorstore(self, embeddings) -> Chroma:
        """創建新的向量數據庫"""
        # 創建文檔
        documents = []
        for i, text in enumerate(SECURITY_KNOWLEDGE_BASE):
            doc = Document(
                page_content=text,
                metadata={"source": f"security_knowledge_{i+1}", "type": "best_practices"}
            )
            documents.append(doc)

        # 文本分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )

        splits = text_splitter.split_documents(documents)
        logger.info(f"📄 分割文檔為 {len(splits)} 個文本塊")

        # 創建向量數據庫
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)

        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=str(self.knowledge_base_path)
        )

        return vectorstore

    def _get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """
        檢索相關文檔

        Args:
            query: 查詢文本

        Returns:
            相關文檔列表
        """
        if not self._initialized:
            self._initialize_vectorstore()

        try:
            # 搜索相關文檔
            results = self._vectorstore.similarity_search(query, k=self.k)
            logger.debug(f"🔍 檢索到 {len(results)} 個相關文檔")
            return results

        except Exception as e:
            logger.error(f"❌ 檢索失敗: {e}")
            return []


def create_security_retriever(
    knowledge_base_path: str = "rag/chroma_db",
    embed_model: Optional[str] = None,
    k: int = 3
) -> SecurityKnowledgeRetriever:
    """
    創建安全知識檢索器的便捷函數

    Args:
        knowledge_base_path: 向量數據庫路徑
        embed_model: 嵌入模型名稱
        k: 返回的文檔數量

    Returns:
        SecurityKnowledgeRetriever 實例
    """
    return SecurityKnowledgeRetriever(
        knowledge_base_path=knowledge_base_path,
        embed_model=embed_model,
        k=k
    )
