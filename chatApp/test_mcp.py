"""
MCP 連接測試腳本
用於診斷和測試與 Wazuh MCP Server 的連接
"""
import asyncio
import httpx
import json

async def test_mcp_connection():
    """測試 MCP 連接"""

    mcp_url = "http://127.0.0.1:8080/mcp"

    print("="*60)
    print("  MCP 連接測試")
    print("="*60)
    print()

    print(f"📍 測試 URL: {mcp_url}")
    print()

    # 1. 測試基本連接
    print("1️⃣  測試基本 HTTP 連接...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(mcp_url)
            print(f"   狀態碼: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            print(f"   Content: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ 連接失敗: {e}")
        print()
        print("💡 請確保 Wazuh MCP Server 正在運行:")
        print("   cd ../mcp-server-wazuh")
        print("   cargo run --features http -- --transport http --host 127.0.0.1 --port 8080")
        return

    print()

    # 2. 測試初始化請求
    print("2️⃣  測試 MCP 初始化...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "sampling": {},
                        "roots": {"listChanged": True}
                    },
                    "clientInfo": {
                        "name": "mcp-test-client",
                        "version": "1.0.0"
                    }
                }
            }

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            print(f"   發送初始化請求...")
            response = await client.post(
                mcp_url,
                json=init_payload,
                headers=headers
            )

            print(f"   狀態碼: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 初始化成功!")
                print(f"   Server: {result.get('result', {}).get('serverInfo', {})}")

                # 發送 initialized 通知
                print()
                print("3️⃣  發送 initialized 通知...")
                notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }

                response2 = await client.post(
                    mcp_url,
                    json=notification,
                    headers=headers
                )
                print(f"   狀態碼: {response2.status_code}")

                # 獲取工具列表
                print()
                print("4️⃣  獲取工具列表...")
                tools_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }

                response3 = await client.post(
                    mcp_url,
                    json=tools_payload,
                    headers=headers
                )

                print(f"   狀態碼: {response3.status_code}")

                if response3.status_code == 200:
                    result = response3.json()
                    tools = result.get('result', {}).get('tools', [])
                    print(f"   ✅ 成功獲取 {len(tools)} 個工具!")
                    print()
                    print("   可用工具:")
                    for i, tool in enumerate(tools[:10], 1):
                        print(f"   {i}. {tool.get('name')}")
                    if len(tools) > 10:
                        print(f"   ... 還有 {len(tools) - 10} 個工具")
                    print()
                    print("🎉 MCP 連接測試成功!")
                else:
                    print(f"   ❌ 獲取工具列表失敗")
                    print(f"   響應: {response3.text}")

            else:
                print(f"   ❌ 初始化失敗")
                print(f"   響應: {response.text}")

    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
