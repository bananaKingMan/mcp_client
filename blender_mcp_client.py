"""
Blender MCP Client - 修复异步+超时+协议适配问题
核心改进：
1. 改用同步 socket（适配 Blender MCP 插件的阻塞式通信）
2. 优化消息格式和结束标识
3. 增加超时重试和分段接收逻辑
4. 适配 Blender 主线程执行特性
"""

import socket
import json
import time
from typing import Optional, Dict, Any

class BlenderMCPClient:
    """Blender MCP Client - 同步版本（适配插件通信特性）"""
    
    def __init__(self, host: str = "localhost", port: int = 9876):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.connect_status = False
        # 超时配置（适配 Blender 主线程执行）
        self.connect_timeout = 15  # 连接超时（秒）
        self.recv_timeout = 20     # 接收响应超时（秒）
        self.retry_times = 2       # 超时重试次数

    def connect(self) -> bool:
        """
        同步连接（移除异步，适配 socket 阻塞特性）
        """
        if self.sock is not None:
            return True
            
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置 socket 级别超时（全局生效）
            self.sock.settimeout(self.connect_timeout)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # 禁用 Nagle 算法，减少消息延迟
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            self.sock.connect((self.host, self.port))
            print(f"✅ 成功连接到 Blender MCP Server: {self.host}:{self.port}")
            
            # 连接测试：执行极简命令（减少 Blender 执行耗时）
            test_result = self.execute_command("print('connect_ok')", retry=True)
            if test_result.get("status") == "success":
                self.connect_status = True
                return True
            else:
                print(f"❌ 连接测试失败：{test_result.get('message', 'Unknown error')}")
                return False
                
        except socket.gaierror:
            print(f"❌ DNS 解析失败：无法解析主机名 '{self.host}'")
        except socket.timeout:
            print(f"❌ 连接超时：超过 {self.connect_timeout} 秒未响应")
        except ConnectionRefusedError:
            print(f"❌ 连接被拒绝：端口 {self.port} 未监听")
            print(f"   提示：请检查 Blender MCP 插件是否已启动并开启服务")
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
            self.connect_status = False
            print("✅ 已断开连接")

    def _safe_recv(self) -> bytes:
        """
        安全接收响应（处理分段/超时/无响应）
        返回：完整的响应字节数据
        """
        response_data = b""
        start_time = time.time()
        
        while True:
            try:
                # 每次接收 1024 字节（减小单次阻塞时间）
                chunk = self.sock.recv(1024) # type: ignore
                if not chunk:
                    break
                response_data += chunk
                
                # 尝试提前解析（判断是否为完整 JSON）
                try:
                    json.loads(response_data.decode('utf-8').strip())
                    break  # 解析成功，说明响应完整
                except json.JSONDecodeError:
                    # 未接收完整，继续
                    pass
                
                # 超时保护（总时长不超过 recv_timeout）
                if time.time() - start_time > self.recv_timeout:
                    raise socket.timeout(f"接收响应超时（{self.recv_timeout}秒）")
                    
            except socket.timeout:
                # 超时但有部分数据，尝试返回
                if response_data:
                    break
                raise
        
        return response_data

    def execute_command(self, command: str, retry: bool = False) -> Dict[str, Any]:
        """
        执行 Blender Python 命令（支持重试）
        :param command: 要执行的代码
        :param retry: 是否启用超时重试
        :return: 响应字典
        """
        if self.sock is None:
            return {"status": "error", "message": "Not connected"}
        
        # 构造标准请求（移除多余转义，确保 JSON 简洁）
        request_data = {
            "type": "execute_code",
            "params": {"code": command.strip()}
        }
        
        # 序列化（禁用 ASCII 转义，减少数据量）
        try:
            request_str = json.dumps(request_data, ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            return {"status": "error", "message": f"JSON 序列化失败: {e}"}
        
        # 重试逻辑
        attempts = 0
        max_attempts = self.retry_times + 1 if retry else 1
        
        while attempts < max_attempts:
            try:
                # 发送消息（移除 \n，插件可能不需要额外分隔符）
                self.sock.sendall(request_str.encode('utf-8'))
                time.sleep(0.5)  # 给 Blender 主线程留执行时间
                
                # 接收响应
                response_data = self._safe_recv()
                if not response_data:
                    raise Exception("服务器返回空响应")
                
                # 解析响应
                response_str = response_data.decode('utf-8').strip()
                result = json.loads(response_str)
                return result
                
            except socket.timeout:
                attempts += 1
                if attempts < max_attempts:
                    print(f"⚠️ 执行超时，第 {attempts} 次重试...")
                    time.sleep(1)  # 重试前等待 1 秒
                else:
                    return {"status": "error", "message": f"超时（{self.recv_timeout}秒），已重试 {self.retry_times} 次"}
            except json.JSONDecodeError:
                return {"status": "error", "message": f"响应解析失败: {response_data[:200] if response_data else '空数据'}"} # type: ignore
            except Exception as e:
                return {"status": "error", "message": f"执行失败: {type(e).__name__}: {e}"}
        
        return {"status": "error", "message": "重试次数耗尽"}

    def get_scene_info(self) -> Dict[str, Any]:
        """获取场景信息（适配插件无参数要求）"""
        if self.sock is None:
            return {"status": "error", "message": "Not connected"}
        
        request_data = {
            "type": "get_scene_info",
            "params": {}
        }
        
        request_str = json.dumps(request_data, ensure_ascii=False, separators=(',', ':'))
        
        try:
            self.sock.sendall(request_str.encode('utf-8'))
            time.sleep(0.5)
            
            response_data = self._safe_recv()
            response_str = response_data.decode('utf-8').strip()
            result = json.loads(response_str)
            
            # 美化输出
            if result.get("status") == "success":
                scene_info = result.get("result", {})
                print("\n📋 Blender 场景信息:")
                print(f"   场景名称: {scene_info.get('name', 'Unknown')}")
                print(f"   对象数量: {scene_info.get('object_count', 0)}")
                
                objects = scene_info.get("objects", [])
                if objects:
                    print("   场景对象列表:")
                    for idx, obj in enumerate(objects, 1):
                        print(f"     {idx}. {obj.get('name')} ({obj.get('type')}) - 位置: {obj.get('location')}")
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": f"获取场景信息失败: {e}"}

def main():
    """主函数（同步版本）"""
    print("=" * 60)
    print("Blender MCP Client - 修复版（同步+重试+超时优化）")
    print("=" * 60)
    
    client = BlenderMCPClient(host="localhost", port=9876)
    
    # 测试1: 连接
    print("\n📡 测试 1: 连接到 Blender MCP Server")
    print("-" * 40)
    connected = client.connect()
    
    if not connected:
        print("\n❌ 连接失败，程序退出")
        client.disconnect()
        return
    
    # 测试2: 执行选择命令
    print("\n📡 测试 2: 执行选择所有物体命令")
    print("-" * 40)
    select_result = client.execute_command("bpy.ops.object.select_all(action='SELECT')")
    if select_result.get("status") == "success":
        print("✅ 选择命令执行成功！")
    else:
        print(f"❌ 选择命令失败: {select_result.get('message')}")
    
    # 测试3: 获取场景信息
    print("\n📡 测试 3: 获取场景信息")
    print("-" * 40)
    scene_info = client.get_scene_info()
    
    # 测试4: 创建立方体
    print("\n📡 测试 4: 创建立方体")
    print("-" * 40)
    create_result = client.execute_command(
        "import bpy; bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))"
    )
    if create_result.get("status") == "success":
        print("✅ 立方体创建成功！")
    else:
        print(f"❌ 立方体创建失败: {create_result.get('message')}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    
    client.disconnect()

if __name__ == "__main__":
    main()
