"""
MCP 客戶端實現
支持通過 stdio 和 HTTP 與 MCP 服務器通信
"""
import asyncio
import json
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
import httpx
from loguru import logger
import sys


class MCPClient:
    """MCP 客戶端，用於與 MCP 服務器通信"""

    def __init__(self, server_config: Dict[str, Any]):
        """
        初始化 MCP 客戶端

        Args:
            server_config: MCP 服務器配置，包含 command, args, env 等信息
        """
        self.server_config = server_config
        self.server_url = None
        self.session_id = None
        self.process = None  # stdio 模式的子進程
        self.request_id = 0  # JSON-RPC 請求 ID
        self._initialize_connection()

    def _initialize_connection(self):
        """初始化連接配置"""
        command = self.server_config.get('command', '')

        # 檢查是否是 HTTP 服務器
        if 'http' in command.lower() or command.startswith('http'):
            # HTTP 模式
            self.transport_mode = 'http'
            self.server_url = command
            logger.info(f"🌐 使用 HTTP 模式連接 MCP 服務器: {self.server_url}")
        else:
            # stdio 模式（需要通過子進程通信）
            self.transport_mode = 'stdio'
            logger.info(f"📡 使用 stdio 模式連接 MCP 服務器: {command}")

    async def connect(self) -> bool:
        """
        建立與 MCP 服務器的連接

        Returns:
            連接是否成功
        """
        try:
            if self.transport_mode == 'http':
                return await self._connect_http()
            else:
                return await self._connect_stdio()
        except Exception as e:
            logger.error(f"❌ 連接 MCP 服務器失敗: {e}")
            return False

    async def _connect_http(self) -> bool:
        """建立 HTTP 連接"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 初始化請求
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
                            "name": "chatapp-wazuh-client",
                            "version": "1.0.0"
                        }
                    }
                }

                # 設置正確的 headers
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                logger.debug(f"發送初始化請求到 {self.server_url}/mcp")
                response = await client.post(
                    f"{self.server_url}/mcp",
                    json=init_payload,
                    headers=headers
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ 成功連接到 MCP 服務器")
                    logger.debug(f"服務器信息: {result.get('result', {}).get('serverInfo', {})}")

                    # 獲取 session ID（如果使用 SSE）
                    if 'mcp-session-id' in response.headers:
                        self.session_id = response.headers['mcp-session-id']
                        headers['MCP-Session-Id'] = self.session_id

                    # 發送 initialized 通知（MCP 協議要求）
                    notification = {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized"
                    }

                    logger.debug("發送 initialized 通知")
                    await client.post(
                        f"{self.server_url}/mcp",
                        json=notification,
                        headers=headers
                    )

                    return True
                else:
                    logger.error(f"❌ HTTP 連接失敗: {response.status_code}")
                    logger.error(f"響應內容: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"❌ HTTP 連接異常: {e}")
            return False

    async def _connect_stdio(self) -> bool:
        """
        建立 stdio 連接
        通過子進程與 MCP 服務器通信
        """
        try:
            command = self.server_config.get('command', '')
            args = self.server_config.get('args', [])
            env = self.server_config.get('env', {})

            # 構建環境變數
            process_env = os.environ.copy()
            process_env.update(env)

            logger.info(f"啟動 MCP 服務器進程: {command}")

            # 啟動子進程
            self.process = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=process_env
            )

            # 等待進程啟動
            await asyncio.sleep(1)

            if self.process.returncode is not None:
                logger.error(f"❌ MCP 進程啟動失敗，退出碼: {self.process.returncode}")
                return False

            # 初始化 MCP 連接
            init_request = {
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
                        "name": "chatapp-wazuh-client",
                        "version": "1.0.0"
                    }
                }
            }

            response = await self._send_request_stdio(init_request)

            if response and 'result' in response:
                logger.info(f"✅ 成功連接到 MCP 服務器 (stdio)")
                logger.debug(f"服務器信息: {response.get('result', {}).get('serverInfo', {})}")

                # 發送 initialized 通知
                notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                await self._send_notification_stdio(notification)

                return True
            else:
                logger.error(f"❌ stdio 初始化失敗: {response}")
                return False

        except Exception as e:
            logger.error(f"❌ stdio 連接異常: {e}")
            await self._close_stdio()
            return False

    async def _send_request_stdio(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        通過 stdio 發送請求並獲取響應

        Args:
            request: JSON-RPC 請求對象

        Returns:
            JSON-RPC 響應對象
        """
        try:
            if not self.process or self.process.stdin is None:
                logger.error("❌ MCP 進程未運行")
                return None

            # 發送請求
            request_json = json.dumps(request) + "\n"
            logger.debug(f"發送 stdio 請求: {request_json.strip()}")
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()

            # 讀取響應
            if self.process.stdout is None:
                logger.error("❌ 無法讀取進程輸出")
                return None

            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=30.0
            )

            if not response_line:
                logger.error("❌ 未收到響應")
                return None

            response = json.loads(response_line.decode())
            logger.debug(f"收到 stdio 響應: {json.dumps(response)[:200]}")
            return response

        except asyncio.TimeoutError:
            logger.error("❌ stdio 請求超時")
            return None
        except Exception as e:
            logger.error(f"❌ stdio 請求失敗: {e}")
            return None

    async def _send_notification_stdio(self, notification: Dict[str, Any]) -> bool:
        """
        通過 stdio 發送通知（不需要響應）

        Args:
            notification: JSON-RPC 通知對象

        Returns:
            是否發送成功
        """
        try:
            if not self.process or self.process.stdin is None:
                logger.error("❌ MCP 進程未運行")
                return False

            # 發送通知
            notification_json = json.dumps(notification) + "\n"
            logger.debug(f"發送 stdio 通知: {notification_json.strip()}")
            self.process.stdin.write(notification_json.encode())
            await self.process.stdin.drain()

            return True

        except Exception as e:
            logger.error(f"❌ stdio 通知發送失敗: {e}")
            return False

    async def _close_stdio(self):
        """關閉 stdio 連接"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except:
                self.process.kill()
            finally:
                self.process = None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        獲取可用的工具列表

        Returns:
            工具列表
        """
        try:
            if self.transport_mode == 'http':
                return await self._list_tools_http()
            else:
                return await self._list_tools_stdio()
        except Exception as e:
            logger.error(f"❌ 獲取工具列表失敗: {e}")
            return []

    async def _list_tools_http(self) -> List[Dict[str, Any]]:
        """通過 HTTP 獲取工具列表"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }

                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                if self.session_id:
                    headers['MCP-Session-Id'] = self.session_id

                response = await client.post(
                    f"{self.server_url}/mcp",
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    result = response.json()
                    tools = result.get('result', {}).get('tools', [])
                    logger.info(f"✅ 獲取到 {len(tools)} 個工具")
                    return tools
                else:
                    logger.error(f"❌ 獲取工具列表失敗: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"❌ HTTP 獲取工具列表異常: {e}")
            return []

    async def _list_tools_stdio(self) -> List[Dict[str, Any]]:
        """通過 stdio 獲取工具列表"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            response = await self._send_request_stdio(request)

            if response and 'result' in response:
                tools = response.get('result', {}).get('tools', [])
                logger.info(f"✅ 獲取到 {len(tools)} 個工具 (stdio)")
                return tools
            else:
                logger.error(f"❌ stdio 獲取工具列表失敗: {response}")
                return []

        except Exception as e:
            logger.error(f"❌ stdio 獲取工具列表異常: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        調用工具

        Args:
            tool_name: 工具名稱
            arguments: 工具參數

        Returns:
            工具執行結果
        """
        try:
            if self.transport_mode == 'http':
                return await self._call_tool_http(tool_name, arguments)
            else:
                return await self._call_tool_stdio(tool_name, arguments)
        except Exception as e:
            logger.error(f"❌ 調用工具 {tool_name} 失敗: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }

    async def _call_tool_http(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """通過 HTTP 調用工具"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }

                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                if self.session_id:
                    headers['MCP-Session-Id'] = self.session_id

                logger.debug(f"🔧 調用工具: {tool_name} with args: {arguments}")
                response = await client.post(
                    f"{self.server_url}/mcp",
                    json=payload,
                    headers=headers,
                    timeout=120.0  # 工具執行可能需要更長時間
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.debug(f"✅ 工具執行成功")
                    return result.get('result', {})
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ 工具調用失敗: {error_msg}")
                    return {
                        "content": [{"type": "text", "text": error_msg}],
                        "isError": True
                    }

        except Exception as e:
            error_msg = f"HTTP 異常: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }

    async def _call_tool_stdio(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """通過 stdio 調用工具"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            logger.debug(f"🔧 stdio 調用工具: {tool_name} with args: {arguments}")
            response = await self._send_request_stdio(request)

            if response and 'result' in response:
                logger.debug(f"✅ stdio 工具執行成功")
                return response.get('result', {})
            else:
                error_msg = f"stdio 工具調用失敗: {response}"
                logger.error(f"❌ {error_msg}")
                return {
                    "content": [{"type": "text", "text": error_msg}],
                    "isError": True
                }

        except Exception as e:
            error_msg = f"stdio 異常: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }


class MCPClientManager:
    """MCP 客戶端管理器，管理多個 MCP 服務器連接"""

    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}

    async def add_server(self, name: str, server_config: Dict[str, Any]) -> bool:
        """
        添加 MCP 服務器

        Args:
            name: 服務器名稱
            server_config: 服務器配置

        Returns:
            是否添加成功
        """
        try:
            client = MCPClient(server_config)
            success = await client.connect()

            if success:
                self.clients[name] = client
                logger.info(f"✅ MCP 服務器 '{name}' 連接成功")
                return True
            else:
                logger.warning(f"⚠️  MCP 服務器 '{name}' 連接失敗")
                return False

        except Exception as e:
            logger.error(f"❌ 添加 MCP 服務器 '{name}' 失敗: {e}")
            return False

    def get_client(self, name: str) -> Optional[MCPClient]:
        """獲取指定的 MCP 客戶端"""
        return self.clients.get(name)

    def get_all_clients(self) -> Dict[str, MCPClient]:
        """獲取所有 MCP 客戶端"""
        return self.clients

    async def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        獲取所有服務器的工具列表

        Returns:
            {server_name: [tools]}
        """
        all_tools = {}
        for name, client in self.clients.items():
            tools = await client.list_tools()
            all_tools[name] = tools
        return all_tools
