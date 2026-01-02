# 🚀 快速開始指南

## ✅ 問題已修復

已修復的導入錯誤：
- ❌ 移除了 `langchain_core.utilities.TavilySearchAPIWrapper`（不存在）
- ✅ 直接使用 `langchain_community.tools.tavily_search.TavilySearchResults`
- ✅ 更新了 `requirements.txt`，移除了不必要的依賴

## 📝 立即開始的 3 個步驟

### 步驟 1: 安裝依賴

```bash
cd chatApp
pip install -r requirements.txt
```

**提示**:
- 如果遇到下載速度慢，使用國內鏡像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步驟 2: 測試環境

```bash
python test_setup.py
```

這會檢查：
- ✅ Python 版本
- ✅ 所有依賴包
- ✅ 配置文件

如果看到 `🎉 檢查完成！`，說明環境正常。

### 步驟 3A: 啟動 Wazuh MCP Server（新終端）

**使用 HTTP 模式（推薦）**:

```bash
cd ../mcp-server-wazuh
cargo run --features http -- --transport http --host 127.0.0.1 --port 8080
```

保持這個終端運行，不要關閉。

### 步驟 3B: 更新 MCP 配置（如果是第一次）

編輯 `chatApp/mcpconfig.json`：

```json
{
  "mcpServers": {
    "wazuh": {
      "command": "http://127.0.0.1:8080",
      "args": [],
      "env": {
        "WAZUH_API_HOST": "192.168.0.75",
        "WAZUH_API_PORT": "55000",
        "WAZUH_API_USERNAME": "wazuh",
        "WAZUH_API_PASSWORD": "5Z89Q9fqo*?+NZ9h*wawb2*5jz3FRqFA",
        "WAZUH_INDEXER_HOST": "192.168.0.75",
        "WAZUH_INDEXER_PORT": "9200",
        "WAZUH_INDEXER_USERNAME": "admin",
        "WAZUH_INDEXER_PASSWORD": "r?buu7iYlZGP*xH6ml*EUoHfLmTZhgl6",
        "WAZUH_TEST_PROTOCOL": "https",
        "WAZUH_VERIFY_SSL": "false",
        "RUST_LOG": "debug"
      }
    }
  }
}
```

**重要**: 確保 `command` 改為 `http://127.0.0.1:8080`

### 步驟 4: 運行應用

回到 `chatApp` 目錄：

```bash
python main.py
```

## 🎉 成功啟動的標誌

看到以下輸出說明啟動成功：

```
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║        🛡️  Wazuh Security Analyst Agent 🛡️           ║
    ║                                                       ║
    ║        LangChain AgenticRAG 應用 v1.0.0              ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝

⚙️  加載配置...
✅ 配置加載成功
🔌 初始化 MCP 客戶端...
📡 連接 MCP 服務器: wazuh
✅ wazuh 連接成功
...
🚀 啟動交互式界面...
```

然後會顯示歡迎界面：

```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│   🛡️  Wazuh Security Analyst                            │
│                                                          │
│   您好！我是您的專業安全分析助手...                      │
│                                                          │
╰──────────────────────────────────────────────────────────╯

❯
```

## 💬 開始對話

試試這些命令：

```
❯ /tools              # 查看所有可用工具
❯ 你好                # 測試對話
❯ 顯示最近 5 個警報   # 測試 Wazuh 工具
```

## ⚠️ 常見問題

### Q1: 提示 "沒有成功連接任何 MCP 服務器"

**原因**: Wazuh MCP server 未運行

**解決**:
1. 確認另一個終端正運行 `cargo run --features http ...`
2. 檢查端口 8080 是否被占用
3. 查看 mcpconfig.json 中的 command 是否為 `http://127.0.0.1:8080`

### Q2: 下載 sentence-transformers 很慢

**解決**: 手動下載模型

```bash
# 使用國內鏡像
export HF_ENDPOINT=https://hf-mirror.com
python main.py
```

### Q3: 出現 SSL 錯誤

**解決**: 在 congif.env 中設置：

```bash
WAZUH_VERIFY_SSL=false
```

## 📚 下一步

- 閱讀完整文檔: `README.md`
- 查看故障排除: `README.md` 的 "🔧 故障排除" 部分
- 查看日誌: `logs/app.log`

## 🆘 需要幫助？

1. 運行診斷: `python test_setup.py`
2. 查看日誌: `type logs\app.log` (Windows) 或 `cat logs/app.log` (Linux/Mac)
3. 檢查配置: 確認 `congif.env` 和 `mcpconfig.json` 正確

---

**祝您使用愉快！🎊**
