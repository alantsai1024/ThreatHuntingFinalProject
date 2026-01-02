# 🛡️ Wazuh Security Analyst - LangChain AgenticRAG 應用

一個智能的 Wazuh SIEM 安全分析助手，結合了 LangChain Agent、RAG 檢索增強生成和 MCP (Model Context Protocol) 技術。

## ✨ 核心功能

- 🔍 **智能警報分析**: 自動分析 Wazuh SIEM 警報並提供威脅評估
- 🤖 **AI 對話助手**: 自然語言交互，智能理解您的安全問題
- 🛠️ **工具調用**: 自動調用合適的 Wazuh MCP 工具獲取數據
- 📚 **知識庫檢索**: RAG 技術提供安全最佳實踐和文檔
- 🌐 **聯網搜索**: 獲取最新的 CVE、威脅情報和技術文檔
- 📊 **多源數據關聯**: 綜合分析警報、漏洞、進程、端口等多維數據

## 📁 項目結構

```
chatApp/
├── main.py                 # 應用入口
├── config.py              # 配置管理
├── requirements.txt       # Python 依賴
├── congif.env             # 環境變數配置
├── mcpconfig.json         # MCP 服務器配置
├── mcp/                   # MCP 客戶端模塊
│   ├── client.py          # MCP 通信客戶端
│   └── wazuh_tools.py     # Wazuh LangChain 工具包
├── rag/                   # RAG 檢索模塊
│   └── retriever.py       # 知識庫檢索器
├── agents/                # Agent 模塊
│   └── security_agent.py  # 安全分析代理
├── tools/                 # 工具模塊
│   ├── web_search.py      # 聯網搜索工具
│   └── system_tools.py    # 系統輔助工具
└── ui/                    # 用戶界面
    └── cli.py             # 命令行界面
```

## 🚀 快速開始

### 1. 前置要求

- Python 3.9+
- Wazuh SIEM (運行中)
- Wazuh MCP Server (已編譯)

### 2. 安裝依賴

```bash
cd chatApp
pip install -r requirements.txt
```

### 3. 配置環境變數

編輯 `congif.env` 文件，確保以下配置正確：

```bash
# Wazuh 配置
WAZUH_API_HOST=192.168.0.75
WAZUH_API_PORT=55000
WAZUH_API_USERNAME=wazuh
WAZUH_API_PASSWORD=your_password
WAZUH_INDEXER_HOST=192.168.0.75
WAZUH_INDEXER_PORT=9200
WAZUH_INDEXER_USERNAME=admin
WAZUH_INDEXER_PASSWORD=your_password

# LLM 配置（推薦）
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
gpt-4o-mini

# 兼容舊變數（仍可使用）
ChatGPTAPIKEY=your_api_key
BASEURL=https://api.openai.com/v1
MODEL=gpt-4o-mini

# OpenRouter 範例
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini

# 可選：聯網搜索
TAVILY_API_KEY=your_tavily_key
```

### 4. 啟動 Wazuh MCP Server

在另一個終端中：

```bash
cd ../mcp-server-wazuh
cargo run
```

### 5. 運行應用

```bash
python main.py
```

## 💬 使用示例

### 查看警報
```
❯ 顯示最近 10 個關鍵安全警報
```

### 分析漏洞
```
❯ 檢查代理 001 的關鍵漏洞
```

### 進程監控
```
❯ 查看 agent 002 上運行的進程
```

### 威脅調查
```
❯ 分析這些警報並建議應對措施
```

### 聯網搜索
```
❯ 搜索 CVE-2024-XXXX 漏洞的詳細信息
```

### 綜合分析
```
❯ 我的系統最近有什麼安全風險？請給出詳細報告
```

## 🛠️ 可用工具

### Wazuh MCP 工具
- `get_wazuh_alert_summary` - 獲取警報摘要
- `get_wazuh_agents` - 獲取代理列表
- `get_wazuh_vulnerability_summary` - 漏洞摘要
- `get_wazuh_critical_vulnerabilities` - 關鍵漏洞
- `get_wazuh_agent_processes` - 進程監控
- `get_wazuh_agent_ports` - 端口監控
- `get_wazuh_rules_summary` - 規則查詢
- `search_wazuh_manager_logs` - 日誌搜索
- `get_wazuh_cluster_health` - 集群健康
- `get_wazuh_weekly_stats` - 統計數據
- ... 還有更多

### 內置工具
- 聯網搜索 (Tavily / DuckDuckGo)
- 計算器
- 系統狀態
- RAG 知識庫檢索

## 🎯 特色功能

### 1. Agentic RAG
結合檢索增強生成和 Agent 推理，提供上下文感知的智能回答。

### 2. 自主工具選擇
Agent 根據問題自動選擇最合適的工具，無需手動指定。

### 3. 多步推理
支持複雜的多步驟安全分析和關聯推理。

### 4. 流式響應
實時顯示 Agent 的思考過程和工具調用。

## 📝 配置說明

### MCP 配置 (mcpconfig.json)

```json
{
  "mcpServers": {
    "wazuh": {
      "command": "cargo run --manifest-path /path/to/mcp-server-wazuh/Cargo.toml",
      "args": [],
      "env": {
        "WAZUH_API_HOST": "192.168.0.75",
        ...
      }
    }
  }
}
```

### 支持的 LLM

- OpenAI (GPT-4, GPT-3.5)
- Azure OpenAI
- 任何 OpenAI 兼容的 API

## 🔧 故障排除

### 快速診斷

首先運行測試腳本檢查環境：

```bash
python test_setup.py
```

### 1. 導入錯誤 (ModuleNotFoundError)

**問題**: `ModuleNotFoundError: No module named 'xxx'`

**解決方案**:
```bash
# 重新安裝所有依賴
pip install -r requirements.txt --upgrade

# 如果特定包失敗，單獨安裝
pip install langchain langchain-openai langchain-community
```

### 2. MCP 連接失敗

**問題**: `沒有成功連接任何 MCP 服務器`

**解決方案**:

#### 方法 A: 使用 HTTP 模式（推薦）

1. 啟動 Wazuh MCP Server（HTTP 模式）：
```bash
cd ../mcp-server-wazuh
cargo run --features http -- --transport http --host 127.0.0.1 --port 8080
```

2. 更新 `mcpconfig.json`：
```json
{
  "mcpServers": {
    "wazuh": {
      "command": "http://127.0.0.1:8080",
      "args": [],
      "env": {
        "WAZUH_API_HOST": "192.168.0.75",
        "WAZUH_API_PORT": "55000",
        ...
      }
    }
  }
}
```

#### 方法 B: 使用 stdio 模式

1. 編譯 Wazuh MCP Server：
```bash
cd ../mcp-server-wazuh
cargo build --release
```

2. 更新 `mcpconfig.json` 使用編譯後的可執行文件：
```json
{
  "mcpServers": {
    "wazuh": {
      "command": "C:\\path\\to\\mcp-server-wazuh\\target\\release\\mcp-server-wazuh.exe",
      "args": [],
      "env": { ... }
    }
  }
}
```

### 3. Wazuh API 連接失敗

**問題**: 工具調用返回連接錯誤

**檢查清單**:
- Wazuh 服務是否運行：`curl -k https://192.168.0.75:55000/`
- 用戶名密碼是否正確（檢查 `congif.env`）
- 網絡是否可達：`ping 192.168.0.75`
- 防火牆是否允許端口 55000 和 9200

### 4. LLM API 調用失敗

**問題**: API key 錯誤或連接失敗

**解決方案**:
- 檢查 `LLM_API_KEY` 或 `ChatGPTAPIKEY` 是否正確
- 確認 `LLM_BASE_URL` 或 `BASEURL` 可訪問
- 如果使用代理，設置：
```bash
HTTP_PROXY=http://your-proxy:port
HTTPS_PROXY=http://your-proxy:port
```

### 5. RAG 知識庫問題

**問題**: 向量數據庫初始化失敗

**解決方案**:
```bash
# 刪除舊的向量數據庫
rm -rf rag/chroma_db

# 重新運行應用（會自動創建）
python main.py
```

**首次運行注意**:
- 嵌入模型 (~100MB) 會自動下載
- 需要穩定的網絡連接
- 下載位置：`~/.cache/torch/sentence_transformers/`

### 6. 聯網搜索不可用

**問題**: Tavily 或 DuckDuckGo 搜索失敗

**解決方案**:

Tavily（需要 API key）:
```bash
# 在 congif.env 中添加
TAVILY_API_KEY=tvly-xxxxxxxxx
```

DuckDuckGo（免費，自動備選）:
- 檢查網絡連接
- 某些網絡環境可能受限

### 7. 日誌查看

所有日誌保存在 `logs/app.log`：

```bash
# 實時查看日誌
tail -f logs/app.log

# 查看錯誤日誌
grep ERROR logs/app.log

# 查看 MCP 相關日誌
grep MCP logs/app.log
```

### 8. 常見錯誤碼

| 錯誤 | 原因 | 解決方案 |
|------|------|----------|
| `Connection refused` | Wazuh API 不可達 | 檢查 IP、端口、防火牆 |
| `401 Unauthorized` | 認證失敗 | 檢查用戶名密碼 |
| `API key invalid` | LLM API key 錯誤 | 更新 ChatGPTAPIKEY |
| `Timeout` | 請求超時 | 檢查網絡，增加超時時間 |
| `Model not found` | LLM 模型名稱錯誤 | 檢查 congif.env 中的 LLM_MODEL 或 MODEL |

### 9. 獲取幫助

如果以上方法無法解決：

1. 查看完整日誌：`logs/app.log`
2. 運行診斷腳本：`python test_setup.py`
3. 提交 Issue 並附上錯誤日誌

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 許可證

MIT License

## 👨‍💻 作者

Threat Hunting Final Project

## 🙏 致謝

- [Wazuh](https://wazuh.com/) - 開源 SIEM 平台
- [LangChain](https://github.com/langchain-ai/langchain) - LLM 應用框架
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol
