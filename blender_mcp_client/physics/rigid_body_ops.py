from typing import Dict, Any
from client.base_client import BaseBlenderMCPClient

class RigidBodyOperations:
    def __init__(self, client: BaseBlenderMCPClient):
        self.client = client

    def add_rigid_body(self, object_name: str, body_type: str = "ACTIVE", mass: float = 1.0) -> Dict[str, Any]:
        """添加刚体物理"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = "{body_type}"
    obj.rigid_body.mass = {mass}
    print(f"已为'{object_name}'添加刚体物理（类型：{body_type}，质量：{mass}）")
else:
    print(f"Error: 对象'{object_name}'不存在")
        """
        return self.client.execute_command(cmd)