import maya.cmds as cmds
import maya.mel as mel

class BlendShapeMirrorTool:
    """
    BlendShape权重镜像工具
    支持基于顶点位置的自动对称检测和权重镜像
    """
    
    def __init__(self):
        self.window_name = "blendShapeMirrorWindow"
        self.width = 400
        self.height = 500
        
        # 数据存储
        self.current_mesh = None
        self.blendshape_node = None
        self.mirror_table = {}
        
        self.build_ui()
    
    def build_ui(self):
        """构建UI界面"""
        # 删除已存在的窗口
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        # 创建窗口
        self.window = cmds.window(
            self.window_name,
            title="BlendShape Mirror Tool",
            widthHeight=(self.width, self.height),
            sizeable=True
        )
        
        # 主布局
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnOffset=("both", 10))
        
        # ========== Mesh选择区域 ==========
        cmds.frameLayout(label="1. Select Mesh", collapsable=True, collapse=False, marginHeight=10)
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 280), (2, 100)])
        
        self.mesh_field = cmds.textField(
            placeholderText="Select mesh and click 'Load'",
            editable=False
        )
        cmds.button(label="Load Mesh", command=self.load_mesh)
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== BlendShape选择区域 ==========
        cmds.frameLayout(label="2. Select BlendShape Node", collapsable=True, collapse=False, marginHeight=10)
        
        self.blendshape_menu = cmds.optionMenu(
            label="BlendShape:",
            changeCommand=self.on_blendshape_changed
        )
        cmds.menuItem(label="<No BlendShape Found>")
        
        cmds.setParent('..')
        
        # ========== Target选择区域 ==========
        cmds.frameLayout(label="3. Select Target to Mirror", collapsable=True, collapse=False, marginHeight=10)
        
        cmds.rowColumnLayout(numberOfColumns=1)
        
        # Target列表
        self.target_list = cmds.textScrollList(
            numberOfRows=8,
            allowMultiSelection=False,
            selectCommand=self.on_target_selected
        )
        
        # 显示当前target信息
        self.target_info = cmds.text(
            label="Select a target to see info",
            align='left',
            font='smallPlainLabelFont'
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== 镜像设置区域 ==========
        cmds.frameLayout(label="4. Mirror Settings", collapsable=True, collapse=False, marginHeight=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        # 镜像轴向
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 280)])
        cmds.text(label="Mirror Axis:")
        self.axis_radio = cmds.radioButtonGrp(
            numberOfRadioButtons=3,
            labelArray3=['X', 'Y', 'Z'],
            select=1,  # 默认X轴
            columnWidth3=[60, 60, 60]
        )
        cmds.setParent('..')
        
        # 镜像方向
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 280)])
        cmds.text(label="Mirror Direction:")
        self.direction_radio = cmds.radioButtonGrp(
            numberOfRadioButtons=2,
            labelArray2=['Positive to Negative', 'Negative to Positive'],
            select=1,  # 默认 +X 到 -X
            columnWidth2=[180, 180]
        )
        cmds.setParent('..')
        
        # 容差设置
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 280)])
        cmds.text(label="Tolerance:")
        self.tolerance_field = cmds.floatField(
            value=0.001,
            minValue=0.0001,
            maxValue=1.0,
            precision=4
        )
        cmds.setParent('..')
        
        cmds.separator(height=10, style='none')
        
        # 构建镜像表按钮
        cmds.button(
            label="Build Mirror Table (Required)",
            height=30,
            backgroundColor=[0.3, 0.5, 0.3],
            command=self.build_mirror_table
        )
        
        self.mirror_table_info = cmds.text(
            label="Mirror table not built yet",
            align='center',
            font='smallPlainLabelFont'
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== 执行区域 ==========
        cmds.frameLayout(label="5. Execute", collapsable=True, collapse=False, marginHeight=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        cmds.button(
            label="Mirror Selected Target",
            height=40,
            backgroundColor=[0.4, 0.6, 0.4],
            command=self.execute_mirror
        )
        
        cmds.separator(height=5, style='none')
        
        cmds.button(
            label="Mirror All Targets",
            height=30,
            backgroundColor=[0.5, 0.5, 0.6],
            command=self.mirror_all_targets
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== 工具按钮 ==========
        cmds.frameLayout(label="Tools", collapsable=True, collapse=True, marginHeight=10)
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 190), (2, 190)])
        
        cmds.button(label="Flip Target", command=self.flip_target)
        cmds.button(label="Reset Weights", command=self.reset_weights)
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # 显示窗口
        cmds.showWindow(self.window)
    
    def load_mesh(self, *args):
        """加载选中的mesh"""
        sel = cmds.ls(sl=True, transforms=True)
        
        if not sel:
            cmds.warning("Please select a mesh")
            return
        
        self.current_mesh = sel[0]
        cmds.textField(self.mesh_field, edit=True, text=self.current_mesh)
        
        # 查找blendShape节点
        self.find_blendshapes()
        
        print(f"✓ Loaded mesh: {self.current_mesh}")
    
    def find_blendshapes(self):
        """查找mesh上的所有blendShape节点"""
        if not self.current_mesh:
            return
        
        # 获取mesh的shape节点
        shapes = cmds.listRelatives(self.current_mesh, shapes=True, noIntermediate=False)
        if not shapes:
            cmds.warning("No shape node found")
            return
        
        # 查找blendShape节点
        history = cmds.listConnections(shapes[0], type='blendShape', s=1)
        i = 1
        while not history and i < len(shapes):
            history = cmds.listConnections(shapes[i], type='blendShape', s=1)
            i+=1
        # 清空并重新填充菜单
        menu_items = cmds.optionMenu(self.blendshape_menu, query=True, itemListLong=True)
        if menu_items:
            cmds.deleteUI(menu_items)
        
        if not history:
            cmds.menuItem(parent=self.blendshape_menu, label="<No BlendShape Found>")
            cmds.warning("No blendShape found on this mesh")
            return
        
        # 添加找到的blendShape节点
        for bs_node in history:
            cmds.menuItem(parent=self.blendshape_menu, label=bs_node)
        
        # 自动选择第一个
        if history:
            cmds.optionMenu(self.blendshape_menu, edit=True, value=history[0])
            self.on_blendshape_changed(history[0])
    
    def on_blendshape_changed(self, selected_bs):
        """当blendShape节点改变时"""
        if selected_bs == "<No BlendShape Found>":
            return
        
        self.blendshape_node = selected_bs
        self.load_targets()
    
    def load_targets(self):
        """加载blendShape的所有target"""
        if not self.blendshape_node:
            return
        
        # 清空列表
        cmds.textScrollList(self.target_list, edit=True, removeAll=True)
        
        # 获取所有target别名
        aliases = cmds.aliasAttr(self.blendshape_node, query=True)
        
        if not aliases:
            cmds.textScrollList(self.target_list, edit=True, append="<No Targets>")
            return
        
        # aliases是 [alias, attr, alias, attr, ...] 格式
        targets = [aliases[i] for i in range(0, len(aliases), 2)]
        
        # 添加到列表
        for target in targets:
            cmds.textScrollList(self.target_list, edit=True, append=target)
        
        print(f"✓ Loaded {len(targets)} targets from {self.blendshape_node}")
    
    def on_target_selected(self):
        """当选择target时显示信息"""
        selected = cmds.textScrollList(self.target_list, query=True, selectItem=True)
        
        if not selected:
            return
        
        target_name = selected[0]
        
        # 获取target的索引
        aliases = cmds.aliasAttr(self.blendshape_node, query=True)
        target_index = aliases.index(target_name) // 2
        
        # 获取当前权重值
        weight_attr = f"{self.blendshape_node}.{target_name}"
        current_weight = cmds.getAttr(weight_attr)
        
        # 统计painted权重的顶点数
        painted_count = self.count_painted_vertices(target_index)
        
        info_text = f"Target: {target_name} | Index: {target_index} | Weight: {current_weight:.2f} | Painted Verts: {painted_count}"
        cmds.text(self.target_info, edit=True, label=info_text)
    
    def count_painted_vertices(self, target_index):
        """统计有painted权重的顶点数"""
        count = 0
        vert_count = cmds.polyEvaluate(self.current_mesh, vertex=True)
        
        for i in range(vert_count):
            weight_attr = f"{self.blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].targetWeights[{i}]"
            
            if cmds.objExists(weight_attr):
                weight = cmds.getAttr(weight_attr)
                if abs(weight - 1.0) > 0.001:  # 如果不是默认值1.0
                    count += 1
        
        return count
    
    def build_mirror_table(self, *args):
        """构建顶点镜像对应表"""
        if not self.current_mesh:
            cmds.warning("Please load a mesh first")
            return
        
        axis_index = cmds.radioButtonGrp(self.axis_radio, query=True, select=True) - 1
        tolerance = cmds.floatField(self.tolerance_field, query=True, value=True)
        
        axis_names = ['X', 'Y', 'Z']
        axis_name = axis_names[axis_index]
        
        print(f"Building mirror table for {self.current_mesh} on {axis_name} axis...")
        
        # 开始构建
        cmds.waitCursor(state=True)
        
        vert_count = cmds.polyEvaluate(self.current_mesh, vertex=True)
        self.mirror_table = {}
        matched_count = 0
        
        # 进度条
        cmds.progressWindow(
            title='Building Mirror Table',
            progress=0,
            status=f'Processing vertices...',
            isInterruptable=True
        )
        
        for i in range(vert_count):
            # 检查是否取消
            if cmds.progressWindow(query=True, isCancelled=True):
                break
            
            # 更新进度
            progress = int((i / float(vert_count)) * 100)
            cmds.progressWindow(edit=True, progress=progress, status=f'Processing vertex {i}/{vert_count}')
            
            # 获取顶点位置
            pos = cmds.xform(
                f"{self.current_mesh}.vtx[{i}]",
                query=True,
                translation=True,
                objectSpace=True
            )
            
            # 创建镜像位置
            mirror_pos = list(pos)
            mirror_pos[axis_index] *= -1
            
            # 查找对应的镜像顶点
            mirror_vert = self.find_closest_vertex(mirror_pos, tolerance)
            
            if mirror_vert is not None:
                self.mirror_table[i] = mirror_vert
                matched_count += 1
        
        cmds.progressWindow(endProgress=True)
        cmds.waitCursor(state=False)
        
        # 更新信息
        info_text = f"✓ Mirror table built: {matched_count}/{vert_count} vertices matched"
        cmds.text(self.mirror_table_info, edit=True, label=info_text)
        
        print(f"✓ Mirror table built: {matched_count} vertices matched")
        
        if matched_count < vert_count * 0.9:  # 如果匹配率低于90%
            cmds.warning(f"Only {matched_count}/{vert_count} vertices matched. Consider increasing tolerance.")
    
    def find_closest_vertex(self, target_pos, tolerance):
        """找到最接近目标位置的顶点"""
        vert_count = cmds.polyEvaluate(self.current_mesh, vertex=True)
        min_dist = float('inf')
        closest_vert = None
        
        for j in range(vert_count):
            vert_pos = cmds.xform(
                f"{self.current_mesh}.vtx[{j}]",
                query=True,
                translation=True,
                objectSpace=True
            )
            
            # 计算距离
            dist = sum((a - b) ** 2 for a, b in zip(target_pos, vert_pos)) ** 0.5
            
            if dist < min_dist:
                min_dist = dist
                closest_vert = j
        
        # 如果距离在容差范围内，返回顶点ID
        if min_dist <= tolerance:
            return closest_vert
        
        return None
    
    def execute_mirror(self, *args):
        """执行镜像操作"""
        # 验证
        if not self.current_mesh:
            cmds.warning("Please load a mesh first")
            return
        
        if not self.blendshape_node:
            cmds.warning("Please select a blendShape node")
            return
        
        if not self.mirror_table:
            cmds.warning("Please build mirror table first")
            return
        
        # 获取选中的target
        selected = cmds.textScrollList(self.target_list, query=True, selectItem=True)
        if not selected:
            cmds.warning("Please select a target to mirror")
            return
        
        target_name = selected[0]
        
        # 执行镜像
        self.mirror_target(target_name)
    
    def mirror_target(self, target_name):
        """镜像单个target的权重"""
        # 获取target索引
        aliases = cmds.aliasAttr(self.blendshape_node, query=True)
        target_index = aliases.index(target_name) // 2
        
        # 获取方向设置
        direction = cmds.radioButtonGrp(self.direction_radio, query=True, select=True)
        pos_to_neg = (direction == 1)  # True = Positive to Negative
        
        print(f"Mirroring target: {target_name} ({'+ to -' if pos_to_neg else '- to +'})")
        
        # 开始镜像
        cmds.waitCursor(state=True)
        mirrored_count = 0
        
        # 遍历镜像表
        for src_vert, dst_vert in self.mirror_table.items():
            # 根据方向决定源和目标
            if not pos_to_neg:
                src_vert, dst_vert = dst_vert, src_vert
            
            # 获取源顶点的权重
            src_weight_attr = f"{self.blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].targetWeights[{src_vert}]"
            
            # 检查源权重是否存在
            if cmds.objExists(src_weight_attr):
                src_weight = cmds.getAttr(src_weight_attr)
            else:
                src_weight = 1.0  # 默认权重
            
            # 设置到目标顶点
            dst_weight_attr = f"{self.blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].targetWeights[{dst_vert}]"
            
            try:
                cmds.setAttr(dst_weight_attr, src_weight)
                mirrored_count += 1
            except:
                pass
        
        cmds.waitCursor(state=False)
        
        print(f"✓ Mirrored {mirrored_count} vertex weights for {target_name}")
        cmds.inViewMessage(
            amg=f'✓ Mirrored <hl>{target_name}</hl>: {mirrored_count} vertices',
            pos='midCenter',
            fade=True,
            fadeStayTime=2000
        )
    
    def mirror_all_targets(self, *args):
        """镜像所有targets"""
        if not self.blendshape_node:
            cmds.warning("Please select a blendShape node")
            return
        
        if not self.mirror_table:
            cmds.warning("Please build mirror table first")
            return
        
        # 获取所有targets
        aliases = cmds.aliasAttr(self.blendshape_node, query=True)
        if not aliases:
            cmds.warning("No targets found")
            return
        
        targets = [aliases[i] for i in range(0, len(aliases), 2)]
        
        # 确认对话框
        result = cmds.confirmDialog(
            title='Confirm',
            message=f'Mirror all {len(targets)} targets?',
            button=['Yes', 'No'],
            defaultButton='Yes',
            cancelButton='No',
            dismissString='No'
        )
        
        if result != 'Yes':
            return
        
        # 进度条
        cmds.progressWindow(
            title='Mirroring All Targets',
            progress=0,
            status='Starting...',
            isInterruptable=True
        )
        
        # 镜像每个target
        for i, target in enumerate(targets):
            if cmds.progressWindow(query=True, isCancelled=True):
                break
            
            progress = int((i / float(len(targets))) * 100)
            cmds.progressWindow(
                edit=True,
                progress=progress,
                status=f'Mirroring {target} ({i+1}/{len(targets)})'
            )
            
            self.mirror_target(target)
        
        cmds.progressWindow(endProgress=True)
        
        print(f"✓ Mirrored all {len(targets)} targets")
        cmds.inViewMessage(
            amg=f'✓ Mirrored <hl>all {len(targets)} targets</hl>',
            pos='midCenter',
            fade=True,
            fadeStayTime=2000
        )
    
    def flip_target(self, *args):
        """翻转target（先镜像到临时，再镜像回来）"""
        selected = cmds.textScrollList(self.target_list, query=True, selectItem=True)
        if not selected:
            cmds.warning("Please select a target")
            return
        
        target_name = selected[0]
        
        # 实现翻转逻辑
        cmds.warning("Flip功能待实现")
    
    def reset_weights(self, *args):
        """重置所有权重为1.0"""
        selected = cmds.textScrollList(self.target_list, query=True, selectItem=True)
        if not selected:
            cmds.warning("Please select a target")
            return
        
        result = cmds.confirmDialog(
            title='Confirm',
            message='Reset all vertex weights to 1.0?',
            button=['Yes', 'No'],
            defaultButton='No',
            cancelButton='No'
        )
        
        if result != 'Yes':
            return
        
        target_name = selected[0]
        aliases = cmds.aliasAttr(self.blendshape_node, query=True)
        target_index = aliases.index(target_name) // 2
        
        vert_count = cmds.polyEvaluate(self.current_mesh, vertex=True)
        
        for i in range(vert_count):
            weight_attr = f"{self.blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].targetWeights[{i}]"
            if cmds.objExists(weight_attr):
                cmds.setAttr(weight_attr, 1.0)
        
        print(f"✓ Reset weights for {target_name}")


# ========== 启动工具 ==========
def show_blendshape_mirror_tool():
    """显示BlendShape镜像工具"""
    BlendShapeMirrorTool()


# 运行工具
if __name__ == "__main__":
    show_blendshape_mirror_tool()