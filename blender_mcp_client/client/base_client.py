# 

# 待实现功能

import socket
import json
import time
from typing import Optional, Dict, Any

class BaseBlenderMCPClient:
    """基础通信客户端：处理Socket长连接、指令收发、统一返回格式"""
    def __init__(self, host: str = "localhost", port: int = 9876):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.is_connected = False
        # 配置项
        self.connect_timeout = 15
        self.recv_timeout = 20
        self.retry_times = 2

    def connect(self) -> bool:
        """建立长连接"""
        if self.is_connected and self.sock:
            print("⚠️ 已存在活跃连接")
            return True
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.connect_timeout)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.connect((self.host, self.port))
            
            # 连接测试
            test_result = self.execute_command("print('connection_ok')", retry=True)
            if test_result["status"] == "success":
                self.is_connected = True
                print(f"✅ 连接成功: {self.host}:{self.port}")
                return True
            else:
                self.disconnect()
                print(f"❌ 连接测试失败: {test_result['message']}")
                return False
        except Exception as e:
            print(f"❌ 连接错误: {type(e).__name__}: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except:
                pass
            self.sock = None
            self.is_connected = False
            print("✅ 已断开连接")

    def _safe_recv(self) -> bytes:
        """安全接收响应（处理分段、超时）"""
        if not self.sock:
            return b""
        response_data = b""
        start_time = time.time()
        while True:
            try:
                chunk = self.sock.recv(1024)
                if not chunk:
                    break
                response_data += chunk
                # 提前判断JSON完整性
                try:
                    json.loads(response_data.decode('utf-8').strip())
                    break
                except json.JSONDecodeError:
                    pass
                if time.time() - start_time > self.recv_timeout:
                    raise socket.timeout(f"接收超时（{self.recv_timeout}s）")
            except socket.timeout:
                if response_data:
                    break
                raise
        return response_data

    def execute_command(self, command: str, retry: bool = False, expect_binary: bool = False) -> Dict[str, Any]:
        """
        执行Blender指令，统一返回格式
        :param command: Blender Python指令
        :param retry: 是否重试
        :param expect_binary: 是否期望二进制返回（如渲染字节）
        :return: 统一格式字典
        """
        if not self.is_connected:
            return {
                "status": "error",
                "message": "未建立有效连接，请先调用connect()",
                "data": None
            }

        # 构造MCP请求
        request_data = {
            "type": "execute_code",
            "params": {"code": command.strip()}
        }
        try:
            request_str = json.dumps(request_data, ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            return {
                "status": "error",
                "message": f"JSON序列化失败: {e}",
                "data": None
            }

        # 重试逻辑
        attempts = 0
        max_attempts = self.retry_times + 1 if retry else 1
        while attempts < max_attempts:
            try:
                self.sock.sendall(request_str.encode('utf-8'))
                time.sleep(0.3)

                # 接收响应
                response_data = self._safe_recv()
                if not response_data:
                    raise Exception("服务器返回空响应")

                # 处理二进制返回
                if expect_binary:
                    return {
                        "status": "success",
                        "message": "二进制数据返回成功",
                        "data": response_data
                    }

                # 处理JSON返回
                response_str = response_data.decode('utf-8').strip()
                result = json.loads(response_str)
                
                return {
                    "status": result.get("status", "error"),
                    "message": result.get("message", "执行成功"),
                    "data": result.get("result", None)
                }
            except socket.timeout:
                attempts += 1
                if attempts < max_attempts:
                    print(f"⚠️ 执行超时，第{attempts}次重试...")
                    time.sleep(1)
                else:
                    return {
                        "status": "error",
                        "message": f"超时（{self.recv_timeout}s），已重试{self.retry_times}次",
                        "data": None
                    }
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": f"响应解析失败: {response_data[:200] if response_data else '空数据'}",
                    "data": None
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"执行失败: {type(e).__name__}: {e}",
                    "data": None
                }
        return {
            "status": "error",
            "message": "重试次数耗尽",
            "data": None
        }