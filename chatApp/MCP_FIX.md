# MCP 連接問題修復

## ✅ 已修復的問題

### 1. HTTP Headers 缺失
- 添加了 `Content-Type: application/json`
- 添加了 `Accept: application/json`

### 2. MCP 協議不完整
- 添加了 `notifications/initialized` 通知（MCP 協議要求）

### 3. 錯誤日誌增強
- 添加了更詳細的錯誤信息輸出

## 🧪 測試步驟

### 步驟 1: 確保 MCP Server 正在運行

在終端 1 中：
```bash
cd ../mcp-server-wazuh
cargo run --features http -- --transport http --host 127.0.0.1 --port 8080
```

您應該看到：
```
✅ Starting HTTP server on 127.0.0.1:8080
✅ Listening on http://127.0.0.1:8080/mcp
```

### 步驟 2: 運行 MCP 連接測試

在終端 2 中（chatApp 目錄）：
```bash
python test_mcp.py
```

這會測試：
- ✅ 基本連接
- ✅ MCP 初始化
- ✅ initialized 通知
- ✅ 工具列表獲取

**成功輸出應該類似：**
```
🎉 MCP 連接測試成功!
✅ 成功獲取 14 個工具!
```

### 步驟 3: 如果測試通過，運行主程序

```bash
python main.py
```

## 🔍 如果仍有問題

### 檢查清單

1. **確認 MCP Server 正在運行**
   ```bash
   # 在 Windows 上
   netstat -an | findstr 8080

   # 應該看到類似：
   # TCP    127.0.0.1:8080    0.0.0.0:0    LISTENING
   ```

2. **測試基本 HTTP 連接**
   ```bash
   curl http://127.0.0.1:8080/mcp
   ```

3. **查看 MCP Server 日誌**
   - 檢查 Server 終端的輸出
   - 看是否有錯誤信息

4. **查看客戶端日誌**
   ```bash
   type logs\app.log
   ```

## 🐛 常見錯誤及解決方案

### 錯誤 1: Connection refused

**原因**: MCP Server 未啟動

**解決**:
```bash
cd ../mcp-server-wazuh
cargo run --features http -- --transport http --host 127.0.0.1 --port 8080
```

### 錯誤 2: HTTP 406

**原因**: 請求格式錯誤

**解決**:
- ✅ 已修復：添加了正確的 headers
- ✅ 已修復：添加了 initialized 通知

### 錯誤 3: 超時

**原因**: 網絡延遲或防火牆

**解決**:
```bash
# 檢查防火牆設置
# 確保允許本地端口 8080
```

## 📝 調試技巧

### 啟用詳細日誌

在 `congif.env` 中設置：
```bash
RUST_LOG=debug
```

### 使用測試腳本

```bash
python test_mcp.py
```

這會顯示每一步的詳細信息，幫助診斷問題。

## ✅ 成功標誌

當一切正常時，您會看到：

```
21:39:48 | INFO | 🔌 初始化 MCP 客戶端...
21:39:48 | INFO | 📡 連接 MCP 服務器: wazuh
21:39:48 | INFO | 🌐 使用 HTTP 模式連接 MCP 服務器: http://127.0.0.1:8080/mcp
21:39:48 | INFO | ✅ 成功連接到 MCP 服務器
21:39:48 | INFO | 🛠️  Agent 已加載 14 個工具
```

## 🎯 下一步

如果 MCP 連接成功，您就可以：

1. ✅ 運行 `python main.py`
2. ✅ 開始與安全分析助手對話
3. ✅ 使用 Wazuh 工具分析警報、漏洞等

---

**需要幫助？** 查看完整的日誌文件 `logs/app.log`
