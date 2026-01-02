"""
快速測試腳本
驗證所有依賴是否正確安裝
"""
import sys

def test_imports():
    """測試所有關鍵導入"""
    print("🔍 測試 Python 導入...\n")

    tests = [
        ("LangChain", "langchain"),
        ("LangChain OpenAI", "langchain_openai"),
        ("LangChain Community", "langchain_community"),
        ("LangChain Core", "langchain_core"),
        ("ChromaDB", "chromadb"),
        ("HTTPX", "httpx"),
        ("Rich", "rich"),
        ("Loguru", "loguru"),
        ("Pydantic", "pydantic"),
        ("Python Dotenv", "dotenv"),
    ]

    failed = []

    for name, module in tests:
        try:
            __import__(module)
            print(f"✅ {name:20s} - OK")
        except ImportError as e:
            print(f"❌ {name:20s} - FAILED: {e}")
            failed.append(name)

    print(f"\n{'='*50}")

    if failed:
        print(f"\n❌ {len(failed)} 個包導入失敗")
        print("請運行: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ 所有依賴安裝成功！")
        return True

def test_optional_imports():
    """測試可選導入"""
    print("\n🔍 測試可選依賴...\n")

    # Tavily（可選）
    try:
        import tavily
        print("✅ Tavily            - OK (聯網搜索功能可用)")
    except ImportError:
        print("⚠️  Tavily            - 未安裝 (聯網搜索將使用 DuckDuckGo)")

    # Sentence Transformers（可選，首次使用會自動下載）
    try:
        import sentence_transformers
        print("✅ Sentence Transformers - OK (RAG 功能可用)")
    except ImportError:
        print("⚠️  Sentence Transformers - 未安裝 (RAG 功能受限)")

    print(f"\n{'='*50}\n")

def main():
    """主函數"""
    print("="*50)
    print("  Wazuh Security Analyst - 依賴檢查")
    print("="*50)
    print()

    # 檢查 Python 版本
    if sys.version_info < (3, 9):
        print(f"❌ Python 版本過低: {sys.version}")
        print("   需要 Python 3.9 或更高版本")
        sys.exit(1)

    print(f"✅ Python 版本: {sys.version.split()[0]}")
    print()

    # 測試導入
    if not test_imports():
        sys.exit(1)

    # 測試可選導入
    test_optional_imports()

    # 檢查配置文件
    print("🔍 檢查配置文件...\n")

    import os
    from pathlib import Path

    config_files = [
        ("congif.env", "環境變數配置"),
        ("mcpconfig.json", "MCP 服務器配置"),
    ]

    for filename, description in config_files:
        if Path(filename).exists():
            print(f"✅ {filename:20s} - 找到 ({description})")
        else:
            print(f"⚠️  {filename:20s} - 未找到 ({description})")

    print(f"\n{'='*50}\n")
    print("🎉 檢查完成！您可以運行 'python main.py' 啟動應用了\n")

if __name__ == "__main__":
    main()
