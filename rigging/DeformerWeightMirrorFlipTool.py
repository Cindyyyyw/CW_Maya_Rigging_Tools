import maya.cmds as cmds
import maya.mel as mel

class DeformerWeightMirrorTool:
    """
    通用Deformer权重镜像/翻转/复制工具
    支持: skinCluster, cluster, wire, sculpt, softMod, lattice, wrap等
    """
    
    def __init__(self):
        self.window_name = "deformerWeightMirrorWindow"
        self.width = 450
        self.height = 650  # 增加高度以容纳新功能
        
        # 数据存储
        self.current_mesh = None
        self.all_shapes = []
        self.source_deformer = None
        self.target_deformer = None
        self.mirror_table = {}
        
        # 支持的deformer类型
        self.supported_deformers = [
            'skinCluster',
            'cluster',
            'ffd',  # lattice
            'wire',
            'sculpt',
            'softMod',
            'wrap',
            'nonLinear',  # bend, twist, etc
            'blendShape',
            'deltaMush',
            'tension',
            'shrinkWrap'
        ]
        
        self.build_ui()
    
    def build_ui(self):
        """构建UI界面"""
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        self.window = cmds.window(
            self.window_name,
            title="Deformer Weight Mirror/Flip/Copy Tool",
            widthHeight=(self.width, self.height),
            sizeable=True
        )
        
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnOffset=("both", 10))
        
        # ========== Mesh选择区域 ==========
        cmds.frameLayout(label="1. Select Mesh", collapsable=True, collapse=False, marginHeight=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
        
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 320), (2, 100)])
        self.mesh_field = cmds.textField(
            placeholderText="Select mesh and click 'Load'",
            editable=False
        )
        cmds.button(label="Load Mesh", command=self.load_mesh, backgroundColor=[0.4, 0.5, 0.4])
        cmds.setParent('..')
        
        # Shape节点信息
        self.shape_info = cmds.text(
            label="Shapes: 0 (including intermediate)",
            align='left',
            font='smallPlainLabelFont'
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== Source Deformer选择 ==========
        cmds.frameLayout(label="2. Source Deformer (Copy From)", collapsable=True, collapse=False, marginHeight=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        cmds.text(label="Select the deformer to copy weights from:", align='left', font='smallBoldLabelFont')
        
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 320), (2, 100)])
        
        self.source_deformer_list = cmds.textScrollList(
            numberOfRows=6,
            allowMultiSelection=False,
            selectCommand=self.on_source_deformer_selected
        )
        
        cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
        cmds.button(label="Refresh", command=self.refresh_deformers, height=25)
        cmds.button(label="Select in Scene", command=self.select_source_deformer, height=25)
        cmds.setParent('..')
        
        cmds.setParent('..')
        
        self.source_deformer_info = cmds.text(
            label="No deformer selected",
            align='left',
            font='smallPlainLabelFont'
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== Target Deformer选择 ==========
        cmds.frameLayout(label="3. Target Deformer (Copy To)", collapsable=True, collapse=False, marginHeight=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        cmds.text(label="Select the deformer to apply weights to:", align='left', font='smallBoldLabelFont')
        
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 300), (2, 1), (3, 120)])
        
        self.target_mode_radio = cmds.radioButtonGrp(
            numberOfRadioButtons=2,
            labelArray2=['Same as Source', 'Different Deformer'],
            select=1,
            onCommand1=self.on_target_mode_changed,
            onCommand2=self.on_target_mode_changed,
            columnWidth2=[140, 160]
        )
        
        cmds.setParent('..')
        
        # Target deformer列表 (默认禁用)
        self.target_deformer_list = cmds.textScrollList(
            numberOfRows=4,
            allowMultiSelection=False,
            enable=False,
            selectCommand=self.on_target_deformer_selected
        )
        
        self.target_deformer_info = cmds.text(
            label="Using same deformer as source",
            align='left',
            font='smallPlainLabelFont'
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== Operation Mode选择 ==========
        cmds.frameLayout(label="4. Operation Mode", collapsable=True, collapse=False, marginHeight=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        # 操作模式选择
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 320)])
        cmds.text(label="Operation:")
        self.operation_radio = cmds.radioButtonGrp(
            numberOfRadioButtons=3,
            labelArray3=['Mirror', 'Flip', 'Copy'],
            select=1,
            columnWidth3=[80, 80, 80],
            onCommand1=self.on_operation_changed,
            onCommand2=self.on_operation_changed,
            onCommand3=self.on_operation_changed
        )
        cmds.setParent('..')
        
        cmds.separator(height=10, style='none')
        
        # 操作说明
        self.operation_description = cmds.text(
            label="Mirror: Copy weights from one side to the other (requires mirror table)",
            align='left',
            font='smallPlainLabelFont',
            wordWrap=True,
            height=30
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== Mirror/Flip设置 (仅Mirror/Flip模式) ==========
        self.mirror_flip_frame = cmds.frameLayout(
            label="5. Mirror/Flip Settings",
            collapsable=True,
            collapse=False,
            marginHeight=10
        )
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        # Mirror方向 (仅Mirror模式显示)
        self.mirror_direction_layout = cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 320)])
        cmds.text(label="Direction:")
        self.direction_radio = cmds.radioButtonGrp(
            numberOfRadioButtons=2,
            labelArray2=['Positive to Negative', 'Negative to Positive'],
            select=1,
            columnWidth2=[180, 180]
        )
        cmds.setParent('..')
        
        # 镜像轴
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 320)])
        cmds.text(label="Mirror Axis:")
        self.axis_radio = cmds.radioButtonGrp(
            numberOfRadioButtons=3,
            labelArray3=['X', 'Y', 'Z'],
            select=1,
            columnWidth3=[60, 60, 60]
        )
        cmds.setParent('..')
        
        # 容差
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 320)])
        cmds.text(label="Tolerance:")
        self.tolerance_field = cmds.floatField(
            value=0.001,
            minValue=0.0001,
            maxValue=1.0,
            precision=4
        )
        cmds.setParent('..')
        
        cmds.separator(height=10, style='none')
        
        # 构建镜像表
        cmds.button(
            label="Build Mirror Table (Required for Mirror/Flip)",
            height=35,
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
        
        # ========== Copy设置 (仅Copy模式) ==========
        self.copy_frame = cmds.frameLayout(
            label="5. Copy Settings",
            collapsable=True,
            collapse=False,
            marginHeight=10,
            visible=False  # 默认隐藏
        )
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        cmds.text(
            label="Copy mode will transfer all weights from source to target deformer",
            align='center',
            font='smallBoldLabelFont',
            wordWrap=True,
            height=30
        )
        
        cmds.separator(height=5, style='in')
        
        # Vertex范围选择
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 320)])
        cmds.text(label="Vertex Range:")
        self.vertex_range_radio = cmds.radioButtonGrp(
            numberOfRadioButtons=2,
            labelArray2=['All Vertices', 'Selected Vertices'],
            select=1,
            columnWidth2=[150, 150]
        )
        cmds.setParent('..')
        
        # 特殊选项：仅复制非零权重
        self.copy_nonzero_only = cmds.checkBox(
            label="Copy only non-zero weights (faster, recommended)",
            value=True
        )
        
        cmds.separator(height=10, style='none')
        
        # Copy信息
        self.copy_info = cmds.text(
            label="Note: Copy does not require mirror table",
            align='center',
            font='smallPlainLabelFont'
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== 高级选项 ==========
        cmds.frameLayout(label="6. Advanced Options", collapsable=True, collapse=True, marginHeight=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        # 权重混合模式
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 320)])
        cmds.text(label="Blend Mode:")
        self.blend_mode = cmds.optionMenu()
        cmds.menuItem(label="Replace (Overwrite)")
        cmds.menuItem(label="Add")
        cmds.menuItem(label="Subtract")
        cmds.menuItem(label="Average")
        cmds.setParent('..')
        
        # 权重影响强度
        cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 320)])
        cmds.text(label="Strength:")
        self.strength_slider = cmds.floatSlider(
            min=0.0,
            max=1.0,
            value=1.0,
            step=0.01
        )
        cmds.setParent('..')
        
        # 归一化权重
        self.normalize_weights = cmds.checkBox(
            label="Normalize weights after operation (for skinCluster)",
            value=True
        )
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== 执行区域 ==========
        cmds.frameLayout(label="7. Execute", collapsable=True, collapse=False, marginHeight=10)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        cmds.button(
            label="Execute Operation",
            height=45,
            backgroundColor=[0.4, 0.6, 0.4],
            command=self.execute_operation
        )
        
        cmds.separator(height=10, style='none')
        
        # 工具按钮
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 210), (2, 210)])
        cmds.button(label="Quick Mirror L→R", command=lambda x: self.quick_copy('LR'), height=30)
        cmds.button(label="Quick Mirror R→L", command=lambda x: self.quick_copy('RL'), height=30)
        cmds.setParent('..')
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        # ========== 信息显示 ==========
        cmds.frameLayout(label="Info", collapsable=True, collapse=True, marginHeight=10)
        cmds.scrollField(
            text=self.get_help_text(),
            editable=False,
            wordWrap=True,
            height=180,
            font='smallPlainLabelFont'
        )
        cmds.setParent('..')
        
        cmds.showWindow(self.window)
    
    def load_mesh(self, *args):
        """加载选中的mesh"""
        sel = cmds.ls(sl=True, transforms=True)
        
        if not sel:
            cmds.warning("Please select a mesh")
            return
        
        self.current_mesh = sel[0]
        cmds.textField(self.mesh_field, edit=True, text=self.current_mesh)
        
        # 获取所有shape节点（包括intermediate）
        self.find_all_shapes()
        
        # 查找deformer
        self.find_deformers()
        
        print(f"✓ Loaded mesh: {self.current_mesh}")
    
    def find_all_shapes(self):
        """查找所有shape节点，包括intermediate objects"""
        if not self.current_mesh:
            return
        
        # 获取所有shape，不过滤intermediate
        all_shapes = cmds.listRelatives(self.current_mesh, shapes=True, fullPath=True) or []
        
        self.all_shapes = all_shapes
        
        # 统计信息
        intermediate_count = len([s for s in all_shapes if cmds.getAttr(f"{s}.intermediateObject")])
        normal_count = len(all_shapes) - intermediate_count
        
        info_text = f"Shapes: {len(all_shapes)} total ({normal_count} normal, {intermediate_count} intermediate)"
        cmds.text(self.shape_info, edit=True, label=info_text)
        
        print(f"Found {len(all_shapes)} shape nodes:")
        for shape in all_shapes:
            is_intermediate = cmds.getAttr(f"{shape}.intermediateObject")
            print(f"  - {shape.split('|')[-1]} {'[intermediate]' if is_intermediate else ''}")
    
    def find_deformers(self):
        """使用findDeformers命令查找所有deformers"""
        if not self.all_shapes:
            return
        
        all_deformers = set()
        
        # 遍历每个shape节点
        for shape in self.all_shapes:
            try:
                # 使用findDeformers命令
                deformers = cmds.findDeformers(shape) or []
                all_deformers.update(deformers)
                
                if deformers:
                    print(f"Shape {shape.split('|')[-1]} has deformers: {deformers}")
                
            except Exception as e:
                # findDeformers可能在某些情况下失败，fallback到listConnections
                print(f"findDeformers failed for {shape}, using listConnections fallback: {e}")
                
                # Fallback方法：使用listConnections
                connections = cmds.listConnections(
                    shape,
                    source=True,
                    destination=False,
                    type='geometryFilter'
                ) or []
                
                # 也查找其他可能的deformer类型
                for deformer_type in self.supported_deformers:
                    type_connections = cmds.listConnections(
                        shape,
                        source=True,
                        destination=False,
                        type=deformer_type
                    ) or []
                    connections.extend(type_connections)
                
                all_deformers.update(connections)
        
        # 转换为列表并排序
        deformer_list = sorted(list(all_deformers))
        
        # 更新UI
        self.update_deformer_lists(deformer_list)
        
        print(f"✓ Found {len(deformer_list)} deformers using findDeformers")
    
    def refresh_deformers(self, *args):
        """刷新deformer列表"""
        if self.current_mesh:
            self.find_deformers()
    
    def update_deformer_lists(self, deformers):
        """更新source和target deformer列表"""
        # 清空列表
        cmds.textScrollList(self.source_deformer_list, edit=True, removeAll=True)
        cmds.textScrollList(self.target_deformer_list, edit=True, removeAll=True)
        
        if not deformers:
            cmds.textScrollList(self.source_deformer_list, edit=True, append="<No Deformers Found>")
            return
        
        # 添加deformer到列表，显示类型
        for deformer in deformers:
            node_type = cmds.nodeType(deformer)
            display_name = f"{deformer} [{node_type}]"
            
            cmds.textScrollList(self.source_deformer_list, edit=True, append=display_name)
            cmds.textScrollList(self.target_deformer_list, edit=True, append=display_name)
    
    def on_source_deformer_selected(self):
        """当选择source deformer时"""
        selected = cmds.textScrollList(self.source_deformer_list, query=True, selectItem=True)
        
        if not selected or selected[0] == "<No Deformers Found>":
            return
        
        # 提取deformer名称（去掉类型标签）
        deformer_display = selected[0]
        deformer_name = deformer_display.split(' [')[0]
        
        self.source_deformer = deformer_name
        
        # 获取deformer信息
        node_type = cmds.nodeType(deformer_name)
        
        # 获取受影响的geometry
        geometry = self.get_deformer_geometry(deformer_name, node_type)
        
        info_text = f"Source: {deformer_name} | Type: {node_type} | Affects: {len(geometry)} geo"
        cmds.text(self.source_deformer_info, edit=True, label=info_text)
        
        # 如果是same as source模式，自动同步
        if cmds.radioButtonGrp(self.target_mode_radio, query=True, select=True) == 1:
            self.target_deformer = self.source_deformer
            cmds.text(
                self.target_deformer_info,
                edit=True,
                label=f"Using same deformer: {deformer_name}"
            )
    
    def on_target_deformer_selected(self):
        """当选择target deformer时"""
        selected = cmds.textScrollList(self.target_deformer_list, query=True, selectItem=True)
        
        if not selected or selected[0] == "<No Deformers Found>":
            return
        
        deformer_display = selected[0]
        deformer_name = deformer_display.split(' [')[0]
        
        self.target_deformer = deformer_name
        
        node_type = cmds.nodeType(deformer_name)
        info_text = f"Target: {deformer_name} | Type: {node_type}"
        cmds.text(self.target_deformer_info, edit=True, label=info_text)
    
    def on_target_mode_changed(self, *args):
        """当target模式改变时"""
        mode = cmds.radioButtonGrp(self.target_mode_radio, query=True, select=True)
        
        if mode == 1:  # Same as source
            cmds.textScrollList(self.target_deformer_list, edit=True, enable=False)
            self.target_deformer = self.source_deformer
            
            if self.source_deformer:
                cmds.text(
                    self.target_deformer_info,
                    edit=True,
                    label=f"Using same deformer: {self.source_deformer}"
                )
        else:  # Different deformer
            cmds.textScrollList(self.target_deformer_list, edit=True, enable=True)
            cmds.text(
                self.target_deformer_info,
                edit=True,
                label="Select a target deformer from the list"
            )
    
    def on_operation_changed(self, *args):
        """当操作模式改变时"""
        operation = cmds.radioButtonGrp(self.operation_radio, query=True, select=True)
        
        # 更新操作说明
        descriptions = {
            1: "Mirror: Copy weights from one side to the other (requires mirror table)",
            2: "Flip: Swap weights between both sides (requires mirror table)",
            3: "Copy: Direct transfer of all weights from source to target (no mirror needed)"
        }
        cmds.text(self.operation_description, edit=True, label=descriptions[operation])
        
        # 根据操作模式显示/隐藏相应的设置frame
        if operation in [1, 2]:  # Mirror or Flip
            cmds.frameLayout(self.mirror_flip_frame, edit=True, visible=True)
            cmds.frameLayout(self.copy_frame, edit=True, visible=False)
            
            # Mirror模式显示direction，Flip模式隐藏
            if operation == 1:  # Mirror
                cmds.rowLayout(self.mirror_direction_layout, edit=True, enable=True)
            else:  # Flip
                cmds.rowLayout(self.mirror_direction_layout, edit=True, enable=False)
        else:  # Copy
            cmds.frameLayout(self.mirror_flip_frame, edit=True, visible=False)
            cmds.frameLayout(self.copy_frame, edit=True, visible=True)
    
    def select_source_deformer(self, *args):
        """在场景中选择source deformer"""
        if self.source_deformer:
            cmds.select(self.source_deformer)
    
    def get_deformer_geometry(self, deformer, node_type):
        """获取deformer影响的geometry"""
        geometry = []
        
        try:
            if node_type == 'skinCluster':
                geometry = cmds.skinCluster(deformer, query=True, geometry=True) or []
            elif node_type == 'blendShape':
                geometry = cmds.blendShape(deformer, query=True, geometry=True) or []
            elif node_type == 'cluster':
                geometry = cmds.cluster(deformer, query=True, geometry=True) or []
            elif node_type in ['ffd', 'wire', 'sculpt', 'softMod', 'wrap']:
                # 通过connections查找
                outputs = cmds.listConnections(
                    f"{deformer}.outputGeometry",
                    destination=True,
                    shapes=True
                ) or []
                geometry = list(set([cmds.listRelatives(o, parent=True)[0] for o in outputs if cmds.listRelatives(o, parent=True)]))
        except:
            pass
        
        return geometry
    
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
        
        cmds.waitCursor(state=True)
        
        vert_count = cmds.polyEvaluate(self.current_mesh, vertex=True)
        self.mirror_table = {}
        matched_count = 0
        
        cmds.progressWindow(
            title='Building Mirror Table',
            progress=0,
            status='Processing vertices...',
            isInterruptable=True
        )
        
        for i in range(vert_count):
            if cmds.progressWindow(query=True, isCancelled=True):
                break
            
            progress = int((i / float(vert_count)) * 100)
            cmds.progressWindow(edit=True, progress=progress, status=f'Processing vertex {i}/{vert_count}')
            
            pos = cmds.xform(
                f"{self.current_mesh}.vtx[{i}]",
                query=True,
                translation=True,
                objectSpace=True
            )
            
            mirror_pos = list(pos)
            mirror_pos[axis_index] *= -1
            
            mirror_vert = self.find_closest_vertex(mirror_pos, tolerance)
            
            if mirror_vert is not None:
                self.mirror_table[i] = mirror_vert
                matched_count += 1
        
        cmds.progressWindow(endProgress=True)
        cmds.waitCursor(state=False)
        
        info_text = f"✓ Mirror table built: {matched_count}/{vert_count} vertices matched ({matched_count*100//vert_count}%)"
        cmds.text(self.mirror_table_info, edit=True, label=info_text)
        
        print(f"✓ Mirror table built: {matched_count} vertices matched")
        
        if matched_count < vert_count * 0.5:
            cmds.warning(f"Low match rate: {matched_count}/{vert_count}. Check tolerance or mesh symmetry.")
    
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
            
            dist = sum((a - b) ** 2 for a, b in zip(target_pos, vert_pos)) ** 0.5
            
            if dist < min_dist:
                min_dist = dist
                closest_vert = j
        
        if min_dist <= tolerance:
            return closest_vert
        
        return None
    
    def execute_operation(self, *args):
        """执行操作（Mirror/Flip/Copy）"""
        # 验证
        if not self.current_mesh:
            cmds.warning("Please load a mesh first")
            return
        
        if not self.source_deformer:
            cmds.warning("Please select a source deformer")
            return
        
        if not self.target_deformer:
            cmds.warning("Please select a target deformer")
            return
        
        # 获取操作模式
        operation = cmds.radioButtonGrp(self.operation_radio, query=True, select=True)
        
        # Mirror/Flip需要镜像表
        if operation in [1, 2] and not self.mirror_table:
            cmds.warning("Please build mirror table first for Mirror/Flip operations")
            return
        
        # 获取方向
        direction = cmds.radioButtonGrp(self.direction_radio, query=True, select=True)
        pos_to_neg = (direction == 1)
        
        # 获取高级选项
        blend_mode = cmds.optionMenu(self.blend_mode, query=True, value=True)
        strength = cmds.floatSlider(self.strength_slider, query=True, value=True)
        normalize = cmds.checkBox(self.normalize_weights, query=True, value=True)
        
        # 执行对应操作
        if operation == 1:  # Mirror
            self.mirror_deformer_weights(pos_to_neg, blend_mode, strength, normalize)
        elif operation == 2:  # Flip
            self.flip_deformer_weights(blend_mode, strength, normalize)
        else:  # Copy
            self.copy_deformer_weights(blend_mode, strength, normalize)
    
    def copy_deformer_weights(self, blend_mode, strength, normalize):
        """✅ 新功能：直接复制deformer权重（不需要镜像）"""
        source_type = cmds.nodeType(self.source_deformer)
        target_type = cmds.nodeType(self.target_deformer)
        
        print(f"Copying weights: {self.source_deformer} [{source_type}] → {self.target_deformer} [{target_type}]")
        
        # 获取vertex范围
        vertex_range_mode = cmds.radioButtonGrp(self.vertex_range_radio, query=True, select=True)
        nonzero_only = cmds.checkBox(self.copy_nonzero_only, query=True, value=True)
        
        cmds.waitCursor(state=True)
        
        # 根据deformer类型调用对应的复制方法
        if source_type == 'skinCluster' and target_type == 'skinCluster':
            self.copy_skincluster_weights(vertex_range_mode, blend_mode, strength, normalize, nonzero_only)
        elif source_type == 'cluster' and target_type == 'cluster':
            self.copy_cluster_weights(vertex_range_mode, blend_mode, strength, nonzero_only)
        elif source_type == 'blendShape' and target_type == 'blendShape':
            self.copy_blendshape_weights(vertex_range_mode, blend_mode, strength, nonzero_only)
        else:
            # 通用复制方法
            self.copy_generic_weights(vertex_range_mode, blend_mode, strength, nonzero_only)
        
        cmds.waitCursor(state=False)
        
        cmds.inViewMessage(
            amg=f'✓ Copied weights: <hl>{self.source_deformer}</hl> → <hl>{self.target_deformer}</hl>',
            pos='midCenter',
            fade=True,
            fadeStayTime=2000
        )
    
    def copy_skincluster_weights(self, vertex_range_mode, blend_mode, strength, normalize, nonzero_only):
        """复制skinCluster权重"""
        # 获取source influences
        source_influences = cmds.skinCluster(self.source_deformer, query=True, influence=True)
        
        # 获取target influences
        target_influences = cmds.skinCluster(self.target_deformer, query=True, influence=True)
        
        # 建立influence映射（通过名称匹配）
        influence_map = {}
        for src_inf in source_influences:
            if src_inf in target_influences:
                influence_map[src_inf] = src_inf
            else:
                # 尝试通过短名称匹配
                src_short = src_inf.split('|')[-1].split(':')[-1]
                for tgt_inf in target_influences:
                    tgt_short = tgt_inf.split('|')[-1].split(':')[-1]
                    if src_short == tgt_short:
                        influence_map[src_inf] = tgt_inf
                        break
        
        print(f"Copying skinCluster: {len(influence_map)}/{len(source_influences)} influences matched")
        
        # 获取要处理的顶点列表
        if vertex_range_mode == 1:  # All vertices
            vert_count = cmds.polyEvaluate(self.current_mesh, vertex=True)
            vertices = range(vert_count)
        else:  # Selected vertices
            sel_verts = cmds.ls(sl=True, flatten=True)
            sel_verts = cmds.filterExpand(sel_verts, selectionMask=31)  # 31 = vertices
            if not sel_verts:
                cmds.warning("No vertices selected")
                return
            vertices = [int(v.split('[')[1].split(']')[0]) for v in sel_verts]
        
        print(f"Processing {len(vertices)} vertices...")
        
        copied_count = 0
        
        # 进度条
        cmds.progressWindow(
            title='Copying Weights',
            progress=0,
            status='Copying vertex weights...',
            isInterruptable=True
        )
        
        for idx, vert_id in enumerate(vertices):
            if cmds.progressWindow(query=True, isCancelled=True):
                break
            
            progress = int((idx / float(len(vertices))) * 100)
            cmds.progressWindow(edit=True, progress=progress)
            
            # 获取源顶点权重
            src_weights = cmds.skinPercent(
                self.source_deformer,
                f"{self.current_mesh}.vtx[{vert_id}]",
                query=True,
                value=True
            )
            
            # 构建transform-value对
            transform_values = []
            for i, src_inf in enumerate(source_influences):
                if src_inf in influence_map:
                    weight = src_weights[i]
                    
                    # 如果只复制非零权重
                    if nonzero_only and weight < 0.0001:
                        continue
                    
                    tgt_inf = influence_map[src_inf]
                    weight_value = weight * strength
                    
                    # 应用blend模式
                    if blend_mode != "Replace (Overwrite)":
                        current_weight = cmds.skinPercent(
                            self.target_deformer,
                            f"{self.current_mesh}.vtx[{vert_id}]",
                            transform=tgt_inf,
                            query=True
                        )
                        
                        if blend_mode == "Add":
                            weight_value = current_weight + weight_value
                        elif blend_mode == "Subtract":
                            weight_value = current_weight - weight_value
                        elif blend_mode == "Average":
                            weight_value = (current_weight + weight_value) / 2.0
                    
                    transform_values.append((tgt_inf, weight_value))
            
            # 设置权重
            if transform_values:
                cmds.skinPercent(
                    self.target_deformer,
                    f"{self.current_mesh}.vtx[{vert_id}]",
                    transformValue=transform_values,
                    normalize=normalize
                )
                copied_count += 1
        
        cmds.progressWindow(endProgress=True)
        
        print(f"✓ Copied weights for {copied_count} vertices")
    
    def copy_cluster_weights(self, vertex_range_mode, blend_mode, strength, nonzero_only):
        """复制cluster权重"""
        print("Copying cluster weights...")
        
        # 获取顶点列表
        if vertex_range_mode == 1:  # All vertices
            vert_count = cmds.polyEvaluate(self.current_mesh, vertex=True)
            vertices = range(vert_count)
        else:  # Selected vertices
            sel_verts = cmds.ls(sl=True, flatten=True)
            sel_verts = cmds.filterExpand(sel_verts, selectionMask=31)
            if not sel_verts:
                cmds.warning("No vertices selected")
                return
            vertices = [int(v.split('[')[1].split(']')[0]) for v in sel_verts]
        
        copied_count = 0
        
        for vert_id in vertices:
            # 获取源权重
            src_weight = cmds.percent(
                self.source_deformer,
                f"{self.current_mesh}.vtx[{vert_id}]",
                query=True,
                value=True
            )[0]
            
            if nonzero_only and src_weight < 0.0001:
                continue
            
            weight_value = src_weight * strength
            
            # 应用blend模式
            if blend_mode != "Replace (Overwrite)":
                current_weight = cmds.percent(
                    self.target_deformer,
                    f"{self.current_mesh}.vtx[{vert_id}]",
                    query=True,
                    value=True
                )[0]
                
                if blend_mode == "Add":
                    weight_value = current_weight + weight_value
                elif blend_mode == "Subtract":
                    weight_value = current_weight - weight_value
                elif blend_mode == "Average":
                    weight_value = (current_weight + weight_value) / 2.0
            
            # 设置权重
            cmds.percent(
                self.target_deformer,
                f"{self.current_mesh}.vtx[{vert_id}]",
                value=weight_value
            )
            copied_count += 1
        
        print(f"✓ Copied weights for {copied_count} vertices")
    
    def copy_blendshape_weights(self, vertex_range_mode, blend_mode, strength, nonzero_only):
        """复制blendShape权重"""
        print("Copying blendShape weights...")
        
        # 获取所有targets
        source_aliases = cmds.aliasAttr(self.source_deformer, query=True) or []
        target_aliases = cmds.aliasAttr(self.target_deformer, query=True) or []
        
        source_targets = [source_aliases[i] for i in range(0, len(source_aliases), 2)]
        target_targets = [target_aliases[i] for i in range(0, len(target_aliases), 2)]
        
        # 建立target映射
        target_map = {}
        for src_tgt in source_targets:
            if src_tgt in target_targets:
                src_idx = source_aliases.index(src_tgt) // 2
                tgt_idx = target_aliases.index(src_tgt) // 2
                target_map[src_idx] = tgt_idx
        
        print(f"Found {len(target_map)} matching targets")
        
        # 获取顶点列表
        if vertex_range_mode == 1:  # All vertices
            vert_count = cmds.polyEvaluate(self.current_mesh, vertex=True)
            vertices = range(vert_count)
        else:
            sel_verts = cmds.ls(sl=True, flatten=True)
            sel_verts = cmds.filterExpand(sel_verts, selectionMask=31)
            if not sel_verts:
                cmds.warning("No vertices selected")
                return
            vertices = [int(v.split('[')[1].split(']')[0]) for v in sel_verts]
        
        # 复制每个target的权重
        for src_idx, tgt_idx in target_map.items():
            for vert_id in vertices:
                # 获取源权重
                src_attr = f"{self.source_deformer}.inputTarget[0].inputTargetGroup[{src_idx}].targetWeights[{vert_id}]"
                
                if cmds.objExists(src_attr):
                    src_weight = cmds.getAttr(src_attr)
                else:
                    src_weight = 1.0
                
                if nonzero_only and abs(src_weight - 1.0) < 0.0001:
                    continue
                
                weight_value = src_weight * strength
                
                # 设置到target
                tgt_attr = f"{self.target_deformer}.inputTarget[0].inputTargetGroup[{tgt_idx}].targetWeights[{vert_id}]"
                cmds.setAttr(tgt_attr, weight_value)
        
        print(f"✓ Copied blendShape weights for {len(target_map)} targets")
    
    def copy_generic_weights(self, vertex_range_mode, blend_mode, strength, nonzero_only):
        """通用权重复制方法"""
        cmds.warning(f"Generic copying for {cmds.nodeType(self.source_deformer)} - may not work perfectly")
        
        # 获取顶点列表
        if vertex_range_mode == 1:
            vert_count = cmds.polyEvaluate(self.current_mesh, vertex=True)
            vertices = range(vert_count)
        else:
            sel_verts = cmds.ls(sl=True, flatten=True)
            sel_verts = cmds.filterExpand(sel_verts, selectionMask=31)
            if not sel_verts:
                cmds.warning("No vertices selected")
                return
            vertices = [int(v.split('[')[1].split(']')[0]) for v in sel_verts]
        
        try:
            for vert_id in vertices:
                src_weight = cmds.percent(
                    self.source_deformer,
                    f"{self.current_mesh}.vtx[{vert_id}]",
                    query=True,
                    value=True
                )[0]
                
                if nonzero_only and src_weight < 0.0001:
                    continue
                
                cmds.percent(
                    self.target_deformer,
                    f"{self.current_mesh}.vtx[{vert_id}]",
                    value=src_weight * strength
                )
        except:
            cmds.error("Unable to copy this deformer type")
    
    def mirror_deformer_weights(self, pos_to_neg, blend_mode, strength, normalize):
        """镜像deformer权重"""
        source_type = cmds.nodeType(self.source_deformer)
        target_type = cmds.nodeType(self.target_deformer)
        
        print(f"Mirroring weights: {self.source_deformer} [{source_type}] → {self.target_deformer} [{target_type}]")
        print(f"Direction: {'+ to -' if pos_to_neg else '- to +'}")
        
        cmds.waitCursor(state=True)
        
        # 根据deformer类型调用对应的镜像方法
        if source_type == 'skinCluster' and target_type == 'skinCluster':
            self.mirror_skincluster_weights(pos_to_neg, blend_mode, strength, normalize)
        elif source_type == 'cluster' and target_type == 'cluster':
            self.mirror_cluster_weights(pos_to_neg, blend_mode, strength)
        elif source_type == 'blendShape' and target_type == 'blendShape':
            self.mirror_blendshape_deformer_weights(pos_to_neg, blend_mode, strength)
        else:
            # 通用方法
            self.mirror_generic_weights(pos_to_neg, blend_mode, strength)
        
        cmds.waitCursor(state=False)
        
        cmds.inViewMessage(
            amg=f'✓ Mirrored weights: <hl>{self.source_deformer}</hl> → <hl>{self.target_deformer}</hl>',
            pos='midCenter',
            fade=True,
            fadeStayTime=2000
        )
    
    def mirror_skincluster_weights(self, pos_to_neg, blend_mode, strength, normalize):
        """镜像skinCluster权重"""
        # 获取所有影响的joints
        influences = cmds.skinCluster(self.source_deformer, query=True, influence=True)
        
        print(f"Mirroring skinCluster with {len(influences)} influences...")
        
        mirrored_count = 0
        
        # 遍历每个顶点
        for src_vert, dst_vert in self.mirror_table.items():
            if not pos_to_neg:
                src_vert, dst_vert = dst_vert, src_vert
            
            # 获取源顶点的权重
            weights = cmds.skinPercent(
                self.source_deformer,
                f"{self.current_mesh}.vtx[{src_vert}]",
                query=True,
                value=True
            )
            
            # 构建transform-value对
            transform_values = []
            for i, influence in enumerate(influences):
                if weights[i] > 0.0001:  # 忽略很小的权重
                    weight_value = weights[i] * strength
                    
                    # 应用blend模式
                    if blend_mode != "Replace (Overwrite)":
                        current_weight = cmds.skinPercent(
                            self.target_deformer,
                            f"{self.current_mesh}.vtx[{dst_vert}]",
                            transform=influence,
                            query=True
                        )
                        
                        if blend_mode == "Add":
                            weight_value = current_weight + weight_value
                        elif blend_mode == "Subtract":
                            weight_value = current_weight - weight_value
                        elif blend_mode == "Average":
                            weight_value = (current_weight + weight_value) / 2.0
                    
                    transform_values.append((influence, weight_value))
            
            # 设置权重
            if transform_values:
                cmds.skinPercent(
                    self.target_deformer,
                    f"{self.current_mesh}.vtx[{dst_vert}]",
                    transformValue=transform_values,
                    normalize=normalize
                )
                mirrored_count += 1
        
        print(f"✓ Mirrored {mirrored_count} vertices for skinCluster")
    
    def mirror_cluster_weights(self, pos_to_neg, blend_mode, strength):
        """镜像cluster权重"""
        print("Mirroring cluster weights...")
        
        mirrored_count = 0
        
        for src_vert, dst_vert in self.mirror_table.items():
            if not pos_to_neg:
                src_vert, dst_vert = dst_vert, src_vert
            
            # 获取源权重
            src_weight = cmds.percent(
                self.source_deformer,
                f"{self.current_mesh}.vtx[{src_vert}]",
                query=True,
                value=True
            )[0]
            
            weight_value = src_weight * strength
            
            # 应用blend模式
            if blend_mode != "Replace (Overwrite)":
                current_weight = cmds.percent(
                    self.target_deformer,
                    f"{self.current_mesh}.vtx[{dst_vert}]",
                    query=True,
                    value=True
                )[0]
                
                if blend_mode == "Add":
                    weight_value = current_weight + weight_value
                elif blend_mode == "Subtract":
                    weight_value = current_weight - weight_value
                elif blend_mode == "Average":
                    weight_value = (current_weight + weight_value) / 2.0
            
            # 设置权重
            cmds.percent(
                self.target_deformer,
                f"{self.current_mesh}.vtx[{dst_vert}]",
                value=weight_value
            )
            mirrored_count += 1
        
        print(f"✓ Mirrored {mirrored_count} vertices for cluster")
    
    def mirror_blendshape_deformer_weights(self, pos_to_neg, blend_mode, strength):
        """镜像blendShape的整体权重"""
        print("Mirroring blendShape weights...")
        
        # 获取所有targets
        aliases = cmds.aliasAttr(self.source_deformer, query=True) or []
        
        for idx in range(0, len(aliases), 2):
            target_name = aliases[idx]
            target_index = idx // 2
            
            mirrored_count = 0
            
            for src_vert, dst_vert in self.mirror_table.items():
                if not pos_to_neg:
                    src_vert, dst_vert = dst_vert, src_vert
                
                # 获取源权重
                src_attr = f"{self.source_deformer}.inputTarget[0].inputTargetGroup[{target_index}].targetWeights[{src_vert}]"
                
                if cmds.objExists(src_attr):
                    src_weight = cmds.getAttr(src_attr)
                else:
                    src_weight = 1.0
                
                weight_value = src_weight * strength
                
                # 设置到target
                dst_attr = f"{self.target_deformer}.inputTarget[0].inputTargetGroup[{target_index}].targetWeights[{dst_vert}]"
                cmds.setAttr(dst_attr, weight_value)
                mirrored_count += 1
            
            print(f"  - Mirrored target '{target_name}': {mirrored_count} vertices")
    
    def mirror_generic_weights(self, pos_to_neg, blend_mode, strength):
        """通用权重镜像方法（fallback）"""
        cmds.warning(f"Generic mirroring for {cmds.nodeType(self.source_deformer)} - may not work perfectly")
        
        # 尝试使用percent命令
        try:
            for src_vert, dst_vert in self.mirror_table.items():
                if not pos_to_neg:
                    src_vert, dst_vert = dst_vert, src_vert
                
                src_weight = cmds.percent(
                    self.source_deformer,
                    f"{self.current_mesh}.vtx[{src_vert}]",
                    query=True,
                    value=True
                )[0]
                
                cmds.percent(
                    self.target_deformer,
                    f"{self.current_mesh}.vtx[{dst_vert}]",
                    value=src_weight * strength
                )
        except:
            cmds.error("Unable to mirror this deformer type")
    
    def flip_deformer_weights(self, blend_mode, strength, normalize):
        """翻转deformer权重（两边互换）"""
        print(f"Flipping weights on {self.source_deformer}...")
        
        source_type = cmds.nodeType(self.source_deformer)
        
        # 先存储一边的权重
        temp_weights = {}
        
        for src_vert, dst_vert in self.mirror_table.items():
            if source_type == 'skinCluster':
                # 存储源顶点权重
                influences = cmds.skinCluster(self.source_deformer, query=True, influence=True)
                src_weights = cmds.skinPercent(
                    self.source_deformer,
                    f"{self.current_mesh}.vtx[{src_vert}]",
                    query=True,
                    value=True
                )
                temp_weights[src_vert] = list(zip(influences, src_weights))
            else:
                # 其他deformer类型
                src_weight = cmds.percent(
                    self.source_deformer,
                    f"{self.current_mesh}.vtx[{src_vert}]",
                    query=True,
                    value=True
                )[0]
                temp_weights[src_vert] = src_weight
        
        # 交换权重
        for src_vert, dst_vert in self.mirror_table.items():
            if source_type == 'skinCluster':
                # 获取dst权重
                influences = cmds.skinCluster(self.source_deformer, query=True, influence=True)
                dst_weights = cmds.skinPercent(
                    self.source_deformer,
                    f"{self.current_mesh}.vtx[{dst_vert}]",
                    query=True,
                    value=True
                )
                
                # 设置src = dst
                transform_values = [(inf, w) for inf, w in zip(influences, dst_weights) if w > 0.0001]
                if transform_values:
                    cmds.skinPercent(
                        self.target_deformer,
                        f"{self.current_mesh}.vtx[{src_vert}]",
                        transformValue=transform_values,
                        normalize=normalize
                    )
                
                # 设置dst = temp_src
                if src_vert in temp_weights:
                    cmds.skinPercent(
                        self.target_deformer,
                        f"{self.current_mesh}.vtx[{dst_vert}]",
                        transformValue=temp_weights[src_vert],
                        normalize=normalize
                    )
            else:
                # 其他类型
                dst_weight = cmds.percent(
                    self.source_deformer,
                    f"{self.current_mesh}.vtx[{dst_vert}]",
                    query=True,
                    value=True
                )[0]
                
                cmds.percent(self.target_deformer, f"{self.current_mesh}.vtx[{src_vert}]", value=dst_weight)
                
                if src_vert in temp_weights:
                    cmds.percent(self.target_deformer, f"{self.current_mesh}.vtx[{dst_vert}]", value=temp_weights[src_vert])
        
        print("✓ Flipped weights")
        cmds.inViewMessage(
            amg=f'✓ Flipped weights on <hl>{self.target_deformer}</hl>',
            pos='midCenter',
            fade=True,
            fadeStayTime=2000
        )
    
    def quick_copy(self, direction):
        """快速拷贝L→R或R→L"""
        if direction == 'LR':
            cmds.radioButtonGrp(self.direction_radio, edit=True, select=1)
        else:
            cmds.radioButtonGrp(self.direction_radio, edit=True, select=2)
        
        self.execute_operation()
    
    def get_help_text(self):
        """获取帮助文本"""
        return """DEFORMER WEIGHT MIRROR/FLIP/COPY TOOL

OPERATIONS:
- Mirror: Copy weights from one side to the other
  (requires mirror table)
- Flip: Swap weights between both sides
  (requires mirror table)
- Copy: Direct transfer of all weights from source to target
  (no mirror table needed)

COPY MODE:
Copy mode allows you to transfer weights from one deformer 
to another on the same mesh without any mirroring. Useful for:
- Transferring skinCluster weights to another skinCluster
- Copying cluster weights to a new cluster
- Duplicating deformer setups

USAGE:
1. Select mesh and click 'Load Mesh'
2. Select source deformer to copy weights from
3. Choose target deformer (or use same as source)
4. Select operation mode (Mirror/Flip/Copy)
5. For Mirror/Flip: Build mirror table
6. Execute

SUPPORTED DEFORMERS:
skinCluster, cluster, blendShape, wire, sculpt, 
softMod, wrap, lattice, deltaMush, and more

TIPS:
- Copy mode is fastest and doesn't require symmetry
- Use 'Selected Vertices' to copy only specific areas
- 'Copy only non-zero weights' improves performance
- Normalize is recommended for skinCluster"""


# ========== 启动工具 ==========
def show_deformer_weight_mirror_tool():
    """显示Deformer权重镜像工具"""
    DeformerWeightMirrorTool()


# 运行
if __name__ == "__main__":
    show_deformer_weight_mirror_tool()