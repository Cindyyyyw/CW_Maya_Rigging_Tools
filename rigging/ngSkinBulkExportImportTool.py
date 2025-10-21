import maya.cmds as cmds
import os
import json
from functools import partial
from ngSkinTools2.api import import_json, export_json, Layers

window_id = "ngSkinBatchToolUI"

def get_skin_cluster(mesh):
    history = cmds.listHistory(mesh)
    skin_clusters = cmds.ls(history, type='skinCluster')
    return skin_clusters[0] if skin_clusters else None

def export_face_info(file_field):
    file_path = cmds.textField(file_field, q=True, text=True)
    selected = cmds.ls(selection=True, type='transform')
    if not selected:
        cmds.warning("Please select at least one mesh")
        return
    result = []
    for mesh in selected:
        face_count = cmds.polyEvaluate(mesh, face=True)
        result.append({"name": mesh, "face_count": face_count})
    with open(file_path, "w") as f:
        json.dump(result, f, indent=4)
    cmds.inViewMessage(amg="export successful", pos="midCenterTop", fade=True)

def import_weights(json_field, folder_field, mesh_field):
    json_path = cmds.textField(json_field, q=True, text=True)
    weight_dir = cmds.textField(folder_field, q=True, text=True)
    combined_mesh = cmds.textField(mesh_field, q=True, text=True)

    if not os.path.exists(json_path):
        cmds.error("no JSON document found")
        return
    with open(json_path, "r") as f:
        mesh_data = json.load(f)

    if not get_skin_cluster(combined_mesh):
        cmds.error(f"{combined_mesh} has no skinCluster, bind skin first")
        return

    offset = 0
    for entry in mesh_data:
        name = entry["name"]
        face_count = entry["face_count"]
        weight_file = os.path.join(weight_dir, f"{name}.json")
        if not os.path.exists(weight_file):
            print(f"Unable to find {weight_file}")
            offset += face_count
            continue

        face_range = f"{combined_mesh}.f[{offset}:{offset + face_count - 1}]"
        cmds.select(face_range, r=True)

        import_json(combined_mesh,json_path)

        target_layers = Layers(combined_mesh)
        layers = target_layers.list
        if layers:
            latest_layer = layers[-1]
            cmds.setAttr(f"{combined_mesh}.{latest_layer}.layerName", name, type="string")

        print(f"Importing {name} → {face_range}")
        offset += face_count

def export_ng_weights(folder_field):
    export_dir = cmds.textField(folder_field, q=True, text=True)
    selected = cmds.ls(selection=True, type='transform')
    if not selected:
        cmds.warning("Please select at least one mesh")
        return
    for mesh in selected:
        path = os.path.join(export_dir, f"{mesh}.json")
        exporter = LayerDataExporter()
        exporter.setSourceMesh(mesh)
        exporter.setDestinationFile(path)
        exporter.exportAll()
        print(f"Exported to {path}")
    cmds.inViewMessage(amg="All ngSkinTools weight exported", pos="midCenterTop", fade=True)

def show_ui():
    if cmds.window(window_id, exists=True):
        cmds.deleteUI(window_id)

    cmds.window(window_id, title="ngSkin bulk import/export tool", widthHeight=(400, 300))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)

    # 区域 1：导出面信息 JSON
    cmds.text(label="export selected mesh's face information")
    face_info_field = cmds.textField(placeholderText="path for expoerted JSON file")
    cmds.button(label="export mesh face JSON", command=lambda x: export_face_info(face_info_field))

    # 区域 2：导入权重到合并 mesh
    cmds.separator(h=10)
    cmds.text(label="2️⃣ 导入 ngSkin 权重到合并后的 mesh")
    json_field = cmds.textField(placeholderText="面信息 JSON 路径")
    weight_folder_field = cmds.textField(placeholderText="ngSkin 权重文件夹路径")
    combined_mesh_field = cmds.textField(placeholderText="合并后的 mesh 名称")
    cmds.button(label="导入权重", command=lambda x: import_weights(json_field, weight_folder_field, combined_mesh_field))

    # 区域 3：一键导出所有选中 mesh 的权重
    cmds.separator(h=10)
    cmds.text(label="3️⃣ 一键导出选中 mesh 的 ngSkin 权重")
    export_folder_field = cmds.textField(placeholderText="导出文件夹路径")
    cmds.button(label="导出选中 mesh 的权重", command=lambda x: export_ng_weights(export_folder_field))

    cmds.setParent("..")
    cmds.showWindow(window_id)