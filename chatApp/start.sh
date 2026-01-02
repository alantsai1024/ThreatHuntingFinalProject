#!/bin/bash
# Linux/Mac 啟動腳本

echo "========================================"
echo "  Wazuh Security Analyst"
echo "  LangChain AgenticRAG Application"
echo "========================================"
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python 3.9+"
    exit 1
fi

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虛擬環境
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# 安裝依賴
echo "[INFO] Checking dependencies..."
pip install -q -r requirements.txt

# 創建日誌目錄
mkdir -p logs

# 運行應用
echo ""
echo "[INFO] Starting application..."
echo ""
python main.py
