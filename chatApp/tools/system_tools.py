"""
系統工具
提供基本的系統輔助功能
"""
from langchain.tools import tool
from typing import Union


@tool
def calculator_tool(expression: str) -> str:
    """
    計算數學表達式

    Args:
        expression: 數學表達式，例如 "2 + 2", "10 * 5", "100 / 4"

    Returns:
        計算結果

    Examples:
        >>> calculator_tool("2 + 2")
        '4'
        >>> calculator_tool("10 * 5")
        '50'
    """
    try:
        # 安全地評估表達式
        # 注意：在生產環境中應該使用更安全的方式
        result = eval(expression, {"__builtins__": {}}, {})

        return f"計算結果: {result}"

    except Exception as e:
        return f"計算錯誤: {str(e)}"


@tool
def get_current_time() -> str:
    """
    獲取當前日期和時間

    Returns:
        當前時間的字符串表示
    """
    from datetime import datetime
    now = datetime.now()
    return f"當前時間: {now.strftime('%Y-%m-%d %H:%M:%S')}"


@tool
def system_status() -> str:
    """
    獲取系統狀態信息

    Returns:
        系統狀態摘要
    """
    import platform
    import os

    status = f"""
系統狀態信息:
- 操作系統: {platform.system()} {platform.release()}
- Python 版本: {platform.python_version()}
- 當前工作目錄: {os.getcwd()}
- 響應正常
    """.strip()

    return status
