from client.base_client import BaseBlenderMCPClient
from operations.object_ops import ObjectOperations
from operations.transform_ops import TransformOperations
from operations.material_ops import MaterialOperations
from animation.keyframe_ops import KeyframeOperations
from physics.rigid_body_ops import RigidBodyOperations
from rendering.engine_ops import RenderEngineOperations
from assets.import_ops import ImportOperations

def main():
    print("=" * 60)
    print("Blender MCP Client - 全功能版")
    print("=" * 60)

    # 初始化客户端
    client = BaseBlenderMCPClient(host="localhost", port=9876)
    
    # 建立连接
    if not client.connect():
        print("❌ 连接失败，程序退出")
        return

    # 初始化所有操作类
    obj_ops = ObjectOperations(client)
    transform_ops = TransformOperations(client)
    material_ops = MaterialOperations(client)
    keyframe_ops = KeyframeOperations(client)
    rigid_body_ops = RigidBodyOperations(client)
    render_ops = RenderEngineOperations(client)
    import_ops = ImportOperations(client)

    # 示例：执行基础操作
    print("\n📝 执行示例操作...")
    
    # 1. 创建并配置立方体
    obj_ops.create_cube = lambda: obj_ops.copy_object("Cube", "MyCube")  # 兼容旧方法
    obj_ops.copy_object("Cube", "MyCube")
    transform_ops.move_object("MyCube", (2, 0, 0))
    
    # 2. 创建并分配材质
    material_ops.create_material("RedMat", (1,0,0,1), 0.0, 0.5)
    material_ops.assign_material("MyCube", "RedMat")
    
    # 3. 添加关键帧动画
    keyframe_ops.insert_location_keyframe("MyCube", 1, (2,0,0))
    keyframe_ops.insert_location_keyframe("MyCube", 50, (5,0,0))
    
    # 4. 设置渲染参数
    render_ops.set_render_engine("CYCLES")
    render_ops.set_render_resolution(1920, 1080)

    print("\n✅ 示例操作执行完成！")
    
    # 保持连接，等待用户输入
    input("\n按回车键断开连接并退出...")
    client.disconnect()

if __name__ == "__main__":
    main()