"""
配置管理模塊
從環境變數和配置文件中讀取應用配置
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class WazuhConfig(BaseModel):
    """Wazuh SIEM 配置"""
    api_host: str = Field(default="localhost")
    api_port: int = Field(default=55000)
    api_username: str = Field(default="wazuh")
    api_password: str = Field(default="wazuh")
    indexer_host: str = Field(default="localhost")
    indexer_port: int = Field(default=9200)
    indexer_username: str = Field(default="admin")
    indexer_password: str = Field(default="admin")
    verify_ssl: bool = Field(default=False)
    test_protocol: str = Field(default="https")


class LLMConfig(BaseModel):
    """LLM 配置"""
    api_key: str
    base_url: str
    model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.7)


class AppConfig(BaseModel):
    """應用配置"""
    wazuh: WazuhConfig
    llm: LLMConfig
    mcp_config_path: str = Field(default="mcpconfig.json")
    knowledge_base_path: str = Field(default="rag/knowledge_base")
    chroma_db_path: str = Field(default="rag/chroma_db")
    log_level: str = Field(default="INFO")


class ConfigManager:
    """配置管理器"""

    def __init__(self, env_file: str = "congif.env"):
        """初始化配置管理器"""
        self.env_file = env_file
        self.project_root = Path(__file__).parent
        self._load_env()

    def _load_env(self):
        """加載環境變數"""
        env_path = self.project_root / self.env_file
        if env_path.exists():
            load_dotenv(env_path)
        else:
            print(f"⚠️  警告: 環境變數文件 {env_file} 不存在")

    def load_config(self) -> AppConfig:
        """加載完整配置"""
        def first_env(*keys: str) -> Optional[str]:
            for key in keys:
                value = os.getenv(key)
                if value:
                    return value
            return None

        # 加載 Wazuh 配置
        wazuh_config = WazuhConfig(
            api_host=os.getenv("WAZUH_API_HOST", "localhost"),
            api_port=int(os.getenv("WAZUH_API_PORT", "55000")),
            api_username=os.getenv("WAZUH_API_USERNAME", "wazuh"),
            api_password=os.getenv("WAZUH_API_PASSWORD", "wazuh"),
            indexer_host=os.getenv("WAZUH_INDEXER_HOST", "localhost"),
            indexer_port=int(os.getenv("WAZUH_INDEXER_PORT", "9200")),
            indexer_username=os.getenv("WAZUH_INDEXER_USERNAME", "admin"),
            indexer_password=os.getenv("WAZUH_INDEXER_PASSWORD", "admin"),
            verify_ssl=os.getenv("WAZUH_VERIFY_SSL", "false").lower() == "true",
            test_protocol=os.getenv("WAZUH_TEST_PROTOCOL", "https")
        )

        api_key = first_env(
            "LLM_API_KEY",
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
            "ChatGPTAPIKEY"
        ) or ""
        base_url = first_env(
            "LLM_BASE_URL",
            "OPENROUTER_BASE_URL",
            "OPENAI_BASE_URL",
            "BASEURL"
        ) or "https://api.openai.com/v1"
        model = first_env(
            "LLM_MODEL",
            "OPENROUTER_MODEL",
            "MODEL"
        )
        if not model:
            if "openrouter.ai" in base_url:
                model = "openai/gpt-4o-mini"
            else:
                model = "gpt-4o-mini"

        # 加載 LLM 配置
        llm_config = LLMConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7"))
        )

        # 創建應用配置
        config = AppConfig(
            wazuh=wazuh_config,
            llm=llm_config,
            mcp_config_path=str(self.project_root / "mcpconfig.json"),
            knowledge_base_path=str(self.project_root / "rag" / "knowledge_base"),
            chroma_db_path=str(self.project_root / "rag" / "chroma_db"),
            log_level=os.getenv("RUST_LOG", "INFO")
        )

        return config

    def load_mcp_config(self) -> Dict[str, Any]:
        """加載 MCP 服務器配置"""
        mcp_config_path = self.project_root / "mcpconfig.json"

        if mcp_config_path.exists():
            with open(mcp_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"⚠️  警告: MCP 配置文件 {mcp_config_path} 不存在")
            return {"mcpServers": {}}


# 全局配置實例
_config_manager: Optional[ConfigManager] = None
_app_config: Optional[AppConfig] = None


def get_config_manager() -> ConfigManager:
    """獲取配置管理器單例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """獲取應用配置單例"""
    global _app_config
    if _app_config is None:
        _app_config = get_config_manager().load_config()
    return _app_config


def reload_config() -> AppConfig:
    """重新加載配置"""
    global _app_config
    _app_config = get_config_manager().load_config()
    return _app_config
