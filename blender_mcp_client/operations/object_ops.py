# 

# 待实现功能

import json
from typing import List, Dict, Any, Optional, Tuple
from client.base_client import BaseBlenderMCPClient

class ObjectOperations:
    def __init__(self, client: BaseBlenderMCPClient):
        self.client = client

    def list_all_objects(self) -> Dict[str, Any]:
        """列出所有对象（含类型、可见性、父对象）"""
        cmd = """
import bpy, json
objects_info = []
for obj in bpy.context.scene.objects:
    obj_info = {
        "name": obj.name,
        "type": obj.type,
        "visible": not obj.hide_viewport,
        "render_visible": not obj.hide_render,
        "parent": obj.parent.name if obj.parent else None,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale)
    }
    objects_info.append(obj_info)
print(json.dumps(objects_info))
        """
        result = self.client.execute_command(cmd)
        if result["status"] == "success" and result["data"]:
            try:
                result["data"] = json.loads(result["data"])
            except:
                result["message"] = "解析对象列表失败"
        return result

    def select_object(self, name: str, select: bool = True) -> Dict[str, Any]:
        """选择/取消选择对象"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj:
    obj.select_set({str(select).lower()})
    print(f"对象'{name}'已{'选中' if select else '取消选中'}")
else:
    print(f"Error: 对象'{name}'不存在")
        """
        return self.client.execute_command(cmd)

    def select_all(self) -> Dict[str, Any]:
        """选择所有对象"""
        cmd = "import bpy; bpy.ops.object.select_all(action='SELECT'); print('已选中所有对象')"
        return self.client.execute_command(cmd)

    def select_none(self) -> Dict[str, Any]:
        """取消所有选择"""
        cmd = "import bpy; bpy.ops.object.select_all(action='DESELECT'); print('已取消所有对象选择')"
        return self.client.execute_command(cmd)

    def get_active_object(self) -> Dict[str, Any]:
        """获取当前活动对象"""
        cmd = """
import bpy, json
active_obj = bpy.context.active_object
if active_obj:
    print(json.dumps({"name": active_obj.name, "type": active_obj.type}))
else:
    print("Error: 无活动对象")
        """
        result = self.client.execute_command(cmd)
        if result["status"] == "success" and result["data"]:
            try:
                result["data"] = json.loads(result["data"])
            except:
                result["message"] = "解析活动对象失败"
        return result

    def set_active_object(self, name: str) -> Dict[str, Any]:
        """设置活动对象"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    print(f"已将'{name}'设为活动对象")
else:
    print(f"Error: 对象'{name}'不存在")
        """
        return self.client.execute_command(cmd)

    def hide_object(self, name: str, hide: bool = True) -> Dict[str, Any]:
        """隐藏/显示对象（视口+渲染）"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj:
    obj.hide_viewport = {str(hide).lower()}
    obj.hide_render = {str(hide).lower()}
    print(f"对象'{name}'已{'隐藏' if hide else '显示'}")
else:
    print(f"Error: 对象'{name}'不存在")
        """
        return self.client.execute_command(cmd)

    def show_object(self, name: str) -> Dict[str, Any]:
        """显示对象（hide_object的别名）"""
        return self.hide_object(name, hide=False)

    def lock_object(self, name: str, lock: bool = True) -> Dict[str, Any]:
        """锁定/解锁对象变换"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj:
    obj.lock_location = ({str(lock).lower()},) * 3
    obj.lock_rotation = ({str(lock).lower()},) * 3
    obj.lock_scale = ({str(lock).lower()},) * 3
    print(f"对象'{name}'变换已{'锁定' if lock else '解锁'}")
else:
    print(f"Error: 对象'{name}'不存在")
        """
        return self.client.execute_command(cmd)

    def copy_object(self, name: str, new_name: Optional[str] = None, linked: bool = False) -> Dict[str, Any]:
        """复制对象（普通复制/链接复制）"""
        new_name = new_name or f"{name}_copy"
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj:
    if {str(linked).lower()}:
        new_obj = obj.copy()
        new_obj.data = obj.data
    else:
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
    new_obj.name = "{new_name}"
    bpy.context.collection.objects.link(new_obj)
    print(f"已{'链接复制' if linked else '复制'}对象'{name}'为'{new_name}'")
else:
    print(f"Error: 对象'{name}'不存在")
        """
        return self.client.execute_command(cmd)

    def instance_object(self, name: str, new_name: Optional[str] = None) -> Dict[str, Any]:
        """链接复制对象"""
        return self.copy_object(name, new_name, linked=True)

    def join_objects(self, object_names: List[str]) -> Dict[str, Any]:
        """连接多个对象"""
        names_str = ", ".join([f"'{name}'" for name in object_names])
        cmd = f"""
import bpy
bpy.ops.object.select_all(action='DESELECT')
objects = []
for name in [{names_str}]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.select_set(True)
        objects.append(obj)
    else:
        print(f"Error: 对象'{name}'不存在")
        exit()
if len(objects) < 2:
    print("Error: 至少需要2个对象才能连接")
else:
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    print(f"已连接对象: {object_names}")
        """
        return self.client.execute_command(cmd)

    def separate_object(self, name: str, separation_type: str = 'SELECTED') -> Dict[str, Any]:
        """分离几何"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.mesh.separate(type='{separation_type}')
    print(f"已分离对象'{name}'（类型：{separation_type}）")
else:
    print(f"Error: 对象'{name}'不存在")
        """
        return self.client.execute_command(cmd)

    def parent_objects(self, parent: str, children: List[str], keep_transform: bool = True) -> Dict[str, Any]:
        """父对象设置"""
        children_str = ", ".join([f"'{child}'" for child in children])
        cmd = f"""
import bpy
parent_obj = bpy.data.objects.get("{parent}")
if not parent_obj:
    print(f"Error: 父对象'{parent}'不存在")
    exit()
for child_name in [{children_str}]:
    child_obj = bpy.data.objects.get(child_name)
    if child_obj:
        child_obj.parent = parent_obj
        child_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()
        if not {str(keep_transform).lower()}:
            child_obj.location = (0,0,0)
            child_obj.rotation_euler = (0,0,0)
            child_obj.scale = (1,1,1)
        print(f"已将'{child_name}'设为'{parent}'的子对象")
    else:
        print(f"Error: 子对象'{child_name}'不存在")
        """
        return self.client.execute_command(cmd)

    def clear_parent(self, child_name: str, keep_transform: bool = True) -> Dict[str, Any]:
        """移除父本"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{child_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.parent_clear(type={'CLEAR_KEEP_TRANSFORM' if keep_transform else 'CLEAR'})
    print(f"已移除'{child_name}'的父对象（保留变换：{keep_transform}）")
else:
    print(f"Error: 对象'{child_name}'不存在")
        """
        return self.client.execute_command(cmd)

    def get_object_hierarchy(self, root_name: str, max_depth: int = 10) -> Dict[str, Any]:
        """获取层级树"""
        cmd = f"""
import bpy, json
def get_hierarchy(obj, depth=0):
    if depth > {max_depth}:
        return {"name": obj.name, "children": []}
    children = []
    for child in bpy.context.scene.objects:
        if child.parent == obj:
            children.append(get_hierarchy(child, depth+1))
    return {{
        "name": obj.name,
        "type": obj.type,
        "depth": depth,
        "children": children
    }}
root_obj = bpy.data.objects.get("{root_name}")
if root_obj:
    hierarchy = get_hierarchy(root_obj)
    print(json.dumps(hierarchy))
else:
    print(f"Error: 根对象'{root_name}'不存在")
        """
        result = self.client.execute_command(cmd)
        if result["status"] == "success" and result["data"]:
            try:
                result["data"] = json.loads(result["data"])
            except:
                result["message"] = "解析层级树失败"
        return result

    def apply_transform(self, name: str) -> Dict[str, Any]:
        """应用位置/旋转/缩放"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print(f"已应用变换到对象'{name}'")
else:
    print(f"Error: 对象'{name}'不存在")
        """
        return self.client.execute_command(cmd)

    def reset_transform(self, name: str) -> Dict[str, Any]:
        """重置变换"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj:
    obj.location = (0,0,0)
    obj.rotation_euler = (0,0,0)
    obj.scale = (1,1,1)
    print(f"已重置'{name}'的变换")
else:
    print(f"Error: 对象'{name}'不存在")
        """
        return self.client.execute_command(cmd)

    def snap_to_grid(self, name: str, increment: float = 1.0) -> Dict[str, Any]:
        """吸附到网格"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.context.scene.unit_settings.grid_scale = {increment}
    bpy.ops.object.snap_selected_to_grid()
    print(f"已将'{name}'吸附到网格（增量：{increment}）")
else:
    print(f"Error: 对象'{name}'不存在")
        """
        return self.client.execute_command(cmd)

    def snap_to_cursor(self, name: str) -> Dict[str, Any]:
        """吸附到3D光标"""
        cmd = f"""
import bpy
obj = bpy.data.objects.get("{name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.snap_selected_to_cursor(use_offset=False)
    print(f"已将'{name}'吸附到3D光标")
else:
    print(f"Error: 对象'{name}'不存在")
        """
        return self.client.execute_command(cmd)

    def align_objects_to_axis(self, object_names: List[str], axis: str = 'X', reference_object: Optional[str] = None) -> Dict[str, Any]:
        """沿轴线对齐"""
        names_str = ", ".join([f"'{name}'" for name in object_names])
        cmd = f"""
import bpy
axis_index = {{'X':0, 'Y':1, 'Z':2}}.get("{axis.upper()}", 0)
# 选中对象
bpy.ops.object.select_all(action='DESELECT')
objects = []
for name in [{names_str}]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.select_set(True)
        objects.append(obj)
    else:
        print(f"Error: 对象'{name}'不存在")
if not objects:
    exit()
# 获取参考位置
if "{reference_object}":
    ref_obj = bpy.data.objects.get("{reference_object}")
    ref_pos = ref_obj.location[axis_index] if ref_obj else objects[0].location[axis_index]
else:
    ref_pos = objects[0].location[axis_index]
# 对齐
for obj in objects:
    obj.location[axis_index] = ref_pos
print(f"已将对象沿{axis}轴对齐到位置{ref_pos}")
        """
        return self.client.execute_command(cmd)

    def distribute_objects(self, object_names: List[str], axis: str = 'X', spacing: float = 1.0, start_position: Optional[Tuple[float, float, float]] = None) -> Dict[str, Any]:
        """均匀分配对象"""
        names_str = ", ".join([f"'{name}'" for name in object_names])
        start_pos = start_position or (0,0,0)
        cmd = f"""
import bpy
axis_index = {{'X':0, 'Y':1, 'Z':2}}.get("{axis.upper()}", 0)
# 选中对象
bpy.ops.object.select_all(action='DESELECT')
objects = []
for name in [{names_str}]:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.select_set(True)
        objects.append(obj)
    else:
        print(f"Error: 对象'{name}'不存在")
if len(objects) < 2:
    print("Error: 至少需要2个对象才能分配")
    exit()
# 排序并分配
objects.sort(key=lambda x: x.location[axis_index])
start = {start_pos[axis_index]}
for i, obj in enumerate(objects):
    pos = list(obj.location)
    pos[axis_index] = start + i * {spacing}
    obj.location = pos
print(f"已沿{axis}轴均匀分配对象（间距：{spacing}）")
        """
        return self.client.execute_command(cmd)

    def copy_transform(self, source: str, dest: str) -> Dict[str, Any]:
        """复制变换"""
        cmd = f"""
import bpy
src_obj = bpy.data.objects.get("{source}")
dest_obj = bpy.data.objects.get("{dest}")
if src_obj and dest_obj:
    dest_obj.location = src_obj.location.copy()
    dest_obj.rotation_euler = src_obj.rotation_euler.copy()
    dest_obj.scale = src_obj.scale.copy()
    print(f"已将'{source}'的变换复制到'{dest}'")
else:
    missing = []
    if not src_obj: missing.append(source)
    if not dest_obj: missing.append(dest)
    print(f"Error: 对象不存在 - {', '.join(missing)}")
        """
        return self.client.execute_command(cmd)

    def match_transform(self, target: str, source: str) -> Dict[str, Any]:
        """copy_transform的别名"""
        return self.copy_transform(source, target)

    def get_object_center(self, name: str, world_space: bool = True) -> Dict[str, Any]:
        """获取物体中心点"""
        cmd = f"""
import bpy, json
obj = bpy.data.objects.get("{name}")
if obj:
    center = obj.location if {str(world_space).lower()} else obj.data.center
    print(json.dumps(list(center)))
else:
    print(f"Error: 对象'{name}'不存在")
        """
        result = self.client.execute_command(cmd)
        if result["status"] == "success" and result["data"]:
            try:
                result["data"] = json.loads(result["data"])
            except:
                result["message"] = "解析中心点失败"
        return result

    def get_object_bounding_box(self, name: str) -> Dict[str, Any]:
        """获取世界空间AABB"""
        cmd = f"""
import bpy, json
obj = bpy.data.objects.get("{name}")
if obj:
    bbox = obj.bound_box
    min_co = [min([v[i] for v in bbox]) for i in range(3)]
    max_co = [max([v[i] for v in bbox]) for i in range(3)]
    # 转换到世界空间
    if obj.matrix_world is not None:
        min_co = list(obj.matrix_world @ bpy.Vector(min_co))
        max_co = list(obj.matrix_world @ bpy.Vector(max_co))
    print(json.dumps({{"min": min_co, "max": max_co}}))
else:
    print(f"Error: 对象'{name}'不存在")
        """
        result = self.client.execute_command(cmd)
        if result["status"] == "success" and result["data"]:
            try:
                result["data"] = json.loads(result["data"])
            except:
                result["message"] = "解析包围盒失败"
        return result