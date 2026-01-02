@echo off
REM Windows 啟動腳本
echo ========================================
echo   Wazuh Security Analyst
echo   LangChain AgenticRAG Application
echo ========================================
echo.

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM 檢查虛擬環境
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM 激活虛擬環境
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM 安裝依賴
echo [INFO] Checking dependencies...
pip install -q -r requirements.txt

REM 創建日誌目錄
if not exist "logs" mkdir logs

REM 運行應用
echo.
echo [INFO] Starting application...
echo.
python main.py

pause
