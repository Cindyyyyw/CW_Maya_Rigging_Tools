import maya.cmds as cmds

class CurveLayerBuilderUI(object):
    def __init__(self):
        self.window = "curveLayerBuilderWindow"
        self.title = "Curve Layer Builder"
        self.size = (300, 200)

        self.build_ui()

    def build_ui(self):
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window, window=True)

        self.window = cmds.window(self.window, title=self.title, widthHeight=self.size, sizeable=False)
        self.layout = cmds.formLayout(numberOfDivisions=100)

        # Number of layers input
        self.layers_field = cmds.intFieldGrp(numberOfFields=1, label = "Number of Layers\t\t",value1=3 )
        # cmds.text(label="Number of Layers:")
        # self.layers_field = cmds.intField(value=3, minValue=1, maxValue=10, height=20)

        # Axis selection
        # cmds.text(label="Stretch Axis:")
        self.axis_menu = cmds.optionMenuGrp(label = "Stretch Axis\t\t")
        cmds.menuItem(label="X")
        cmds.menuItem(label="Y")
        cmds.menuItem(label="Z")

        # Direction selection
        # cmds.text(label="Direction:")
        self.direction_menu = cmds.optionMenuGrp(label = "Direction\t\t")
        cmds.menuItem(label="Positive")
        cmds.menuItem(label="Negative")

        # Build button
        # cmds.rowLayout(numberOfColumns=3, columnWidth3=[100, 100, 100], adjustableColumn=2)
        # cmds.text(label="")  # Left spacer
        # cmds.button(label="Build Curve Layers", command=self.on_build_button_clicked)
        # cmds.text(label="")  # Right spacer
        # cmds.setParent('..')  # Exit the row layout
        self.submit_btn = cmds.button(label="Build Curve Layers", command=self.on_build_button_clicked, height=30)
        
        cmds.formLayout( self.layout, edit=True, 
        attachForm=[(self.layers_field, 'top', 5),      (self.layers_field, 'left', 5),     (self.layers_field, 'right', 5), 
                    (self.axis_menu, 'left', 5),        (self.axis_menu, 'right', 5), 
                    (self.direction_menu, 'left', 5),   (self.direction_menu, 'right', 5), 
                    (self.submit_btn, 'left', 5),       (self.submit_btn, 'right', 5)], 
        attachControl=[ (self.axis_menu, 'top', 5, self.layers_field),
                        (self.direction_menu, 'top', 5, self.axis_menu),
                        (self.submit_btn, 'top', 5, self.direction_menu)] )

        cmds.showWindow(self.window)

    def on_build_button_clicked(self, *args):
        layers = cmds.intFieldGrp(self.layers_field, query=True, value1=True)
        axis = cmds.optionMenuGrp(self.axis_menu, query=True, value=True)
        direction = 1 if cmds.optionMenuGrp(self.direction_menu, query=True, value=True) == "Positive" else -1
        build_curve_layers(layers=layers, axis=axis, direction=direction)


def create_controller(name, size):
    ctrl = cmds.circle(name="%s_ctrl" % name, radius=size, normal=[1, 0, 0])[0]
    npo = cmds.group(ctrl, name="%s_npo" % name)
    return npo, ctrl


def build_curve_layers(layers=3, axis='X', direction=1):
    """
    Builds layers of cubic curves with specified number of layers.
    :param layers: Number of curve layers to build.
    :param axis: The axis along which the curves stretch ('X', 'Y', or 'Z').
    :param direction: Direction of curve stretching (1 for positive, -1 for negative).
    """
    # Validate input
    axis = axis.upper()
    if axis not in ['X', 'Y', 'Z']:
        cmds.error("Axis must be 'X', 'Y', or 'Z'.")
        return

    if direction not in [1, -1]:
        cmds.error("Direction must be 1 (positive) or -1 (negative).")
        return

    # Define length of all curves
    curve_length = 10.0  # Set a uniform length for all curves

    # Initialize previous layer joints
    previous_layer_joints = []

    # Collect all NPO groups for organizing later
    all_npo_groups = []
    final_crv_layer = ""
    final_crv_layer_no = 0
    
    # Create one extra curve layer (layers + 1) but keep joint creation the same
    for layer in range(1, layers + 1): 
        spans = 2 ** layer
        start_point = [0, 0, 0]
        end_point = [0, 0, 0]

        if axis == 'X':
            start_point[0] = 0
            end_point[0] = direction * curve_length
        elif axis == 'Y':
            start_point[1] = 0
            end_point[1] = direction * curve_length
        elif axis == 'Z':
            start_point[2] = 0
            end_point[2] = direction * curve_length

        # Create an initial linear curve with two points
        initial_curve = cmds.curve(d=1, p=[start_point, end_point], name="initial_curve_layer_%s" % layer)

        # Rebuild the curve with the required parameters
        rebuilt_curve = cmds.rebuildCurve(
            initial_curve,
            ch=1,  # History enabled
            rpo=1,  # Replace original
            rt=0,  # Keep parameterization
            end=1,  # Keep end knots
            kr=0,  # Keep range
            kcp=0,  # Don't keep control points
            kep=1,  # Keep endpoints
            kt=0,  # Uniform parameterization
            s=spans,  # Number of spans
            d=3  # Degree of the curve
        )[0]

        curve_name = "curve_layer_%s" % layer
        cmds.rename(rebuilt_curve, curve_name)
        rebuilt_curve = curve_name  # Update the rebuilt_curve variable with the new name

        # Rename the shape node to match the curve
        curve_shape = cmds.listRelatives(rebuilt_curve, shapes=True)[0]
        cmds.rename(curve_shape, "%sShape" % curve_name)

        # Create a group for NPOs of this layer
        npo_group_name = "layer_%s_NPOs" % layer
        npo_group = cmds.group(empty=True, name=npo_group_name)
        all_npo_groups.append(npo_group)

        # Add joints along the curve
        joints = []
        parameter_count = (2 * spans + 1)
        for i in range(parameter_count):
            param = float(i) / (parameter_count - 1)
            joint_name = "joint_layer_%s_%s" % (layer, i)

            # Create PointOnCurveInfo node
            poc = cmds.createNode('pointOnCurveInfo', name="%s_poc" % joint_name)
            cmds.connectAttr("%sShape.worldSpace[0]" % rebuilt_curve, "%s.inputCurve" % poc)
            cmds.setAttr("%s.parameter" % poc, param)

            # Normalize tangent vector
            tangent_vector_node = cmds.createNode('vectorProduct', name="%s_tangentVector" % joint_name)
            cmds.connectAttr("%s.tangent" % poc, "%s.input1" % tangent_vector_node)
            cmds.setAttr("%s.operation" % tangent_vector_node, 0)  # No operation, use as-is
            cmds.setAttr("%s.normalizeOutput" % tangent_vector_node, 1)  # Normalize the tangent

            # Calculate cross product with world up vector
            cross_product_node = cmds.createNode('vectorProduct', name="%s_crossProduct" % joint_name)
            cmds.setAttr("%s.operation" % cross_product_node, 2)  # Cross product
            cmds.setAttr("%s.input2" % cross_product_node, 0, 1, 0)  # World up vector
            cmds.connectAttr("%s.outputX" % tangent_vector_node, "%s.input1X" % cross_product_node)
            cmds.connectAttr("%s.outputY" % tangent_vector_node, "%s.input1Y" % cross_product_node)
            cmds.connectAttr("%s.outputZ" % tangent_vector_node, "%s.input1Z" % cross_product_node)

            # Build a four-by-four matrix
            four_by_four_matrix = cmds.createNode('fourByFourMatrix', name="%s_matrix" % joint_name)
            cmds.connectAttr("%s.outputX" % tangent_vector_node, "%s.in00" % four_by_four_matrix)
            cmds.connectAttr("%s.outputY" % tangent_vector_node, "%s.in01" % four_by_four_matrix)
            cmds.connectAttr("%s.outputZ" % tangent_vector_node, "%s.in02" % four_by_four_matrix)
            cmds.connectAttr("%s.outputX" % cross_product_node, "%s.in10" % four_by_four_matrix)
            cmds.connectAttr("%s.outputY" % cross_product_node, "%s.in11" % four_by_four_matrix)
            cmds.connectAttr("%s.outputZ" % cross_product_node, "%s.in12" % four_by_four_matrix)
            cmds.setAttr("%s.in20" % four_by_four_matrix, 0)
            cmds.setAttr("%s.in21" % four_by_four_matrix, 1)
            cmds.setAttr("%s.in22" % four_by_four_matrix, 0)  # Set world up vector as the Z-axis
            cmds.setAttr("%s.in30" % four_by_four_matrix, 0)  # Translation offset row is zero

            # Decompose the matrix to extract rotation
            decompose_matrix = cmds.createNode('decomposeMatrix', name="%s_decompose" % joint_name)
            cmds.connectAttr("%s.output" % four_by_four_matrix, "%s.inputMatrix" % decompose_matrix)

            # Create joint and connect its position and rotation
            joint = cmds.joint(name=joint_name)
            cmds.connectAttr("%s.position" % poc, "%s.translate" % joint)
            cmds.connectAttr("%s.outputRotate" % decompose_matrix, "%s.rotate" % joint)

            # Create child joint
            child_joint = cmds.joint(name="%s_child" % joint_name)
            cmds.setAttr("%s.translate" % child_joint, 0, 0, 0)
            cmds.setAttr("%s.rotate" % child_joint, 0, 0, 0)

            # Create controller and NPO group for the child joint
            size = 2.0 / (layer + 1)  # Example size scaling based on hierarchy depth
            npo, ctrl = create_controller(joint_name, size)
            cmds.parent(npo, npo_group)  # Group the NPO under the layer's NPO group
            cmds.parentConstraint(joint, npo, maintainOffset=False)  # Parent constrain NPO to parent joint without offset
            cmds.parentConstraint(ctrl, child_joint, maintainOffset=False)  # Parent constrain child joint to controller

            # Store joint for later skinning
            joints.append(child_joint)

        # Skin the next layer of curve to the child joints of the current layer
        if previous_layer_joints:
            skin_cluster = cmds.skinCluster(previous_layer_joints, rebuilt_curve, name="skinCluster_layer_%s" % layer, tsb=1,bm=0)[0]

        # Update the previous layer joints
        previous_layer_joints = joints
        
        if layer==layers: # for the last layer
            # Create an initial linear curve with two points
            initial_curve = cmds.curve(d=1, p=[start_point, end_point], name="initial_curve_layer_%s" % layer)

            # Rebuild the curve with the required parameters
            rebuilt_curve = cmds.rebuildCurve(
                initial_curve,
                ch=1,  # History enabled
                rpo=1,  # Replace original
                rt=0,  # Keep parameterization
                end=1,  # Keep end knots
                kr=0,  # Keep range
                kcp=0,  # Don't keep control points
                kep=1,  # Keep endpoints
                kt=0,  # Uniform parameterization
                s=spans+1,  # Number of spans
                d=3  # Degree of the curve
            )[0]
            curve_name = "curve_layer_%s" % (layer+1)
            cmds.rename(rebuilt_curve, curve_name)
            rebuilt_curve = curve_name  # Update the rebuilt_curve variable with the new name

            # Rename the shape node to match the curve
            curve_shape = cmds.listRelatives(rebuilt_curve, shapes=True)[0]
            cmds.rename(curve_shape, "%sShape" % curve_name)
            final_crv_layer = curve_name
            final_crv_layer_no = int(layer+1)
            skin_cluster = cmds.skinCluster(previous_layer_joints, rebuilt_curve, name="skinCluster_layer_%s" % (layer+1), tsb=1, bm=0)[0]
            

    # Group all NPO groups together
    master_group = cmds.group(all_npo_groups, name="All_NPOs")
    
    # Create a master controller for curve_layer_1
    master_ctrl, _ = create_controller("master", size=3)
    cmds.parent( "All_NPOs", "master_npo")
    cmds.parentConstraint( "master_ctrl", "curve_layer_1")
    cmds.scaleConstraint( "master_ctrl", "curve_layer_1")
    
    # Constrain all NPO's scale
    for npo in all_npo_groups:
        cmds.connectAttr("master_ctrl.scale", "%s.scale"%npo)
    
    # Tidy up
    joints = cmds.select(cmds.ls("joint_layer_*", et="joint"))
    cmds.select("joint_layer_*child", d=1)
    joint_layer_grp = cmds.group(n="joint_layer_grp")

    crvs = cmds.select(cmds.ls("curve_layer_*", et="nurbsCurve"))
    crv_layer_grp = cmds.group(n="curve_layer_grp")
    
    hidden_grp = cmds.group([joint_layer_grp,crv_layer_grp], n="hidden_grp")
    cmds.hide(hidden_grp)
    
    color_lis = [13, 4, 12, 24, 21]
    i = 0
    for npo_group in all_npo_groups:
        cmds.select(npo_group, hi=1)
        crvs = cmds.ls(sl=1, et="nurbsCurve")
        for crv in crvs:
            # Enable color override
            cmds.setAttr("%s.overrideEnabled" % crv, 1)
            
            # Set the override color (e.g., 6 = yellow)
            cmds.setAttr("%s.overrideColor" % crv, color_lis[i])
        i+=1
    
    # Create a cylinder that is going to be wire deformed by the last curve
    if axis =="X":
        ax = [1,0,0]
    elif axis =="Y":
        ax = [0,1,0]
    else:
        ax = [0,0,1]
    
    for i in range(3):
        ax[i] = ax[i]*direction
    
    move = list(ax)
    for i in range(3):
        move[i] = move[i]*5
        
    deformedCylinder = cmds.polyCylinder(n = "deformedCylinder", r=0.2, h=10, ax=tuple(ax), sx=8, sy=100, sz=1)[0]
    cmds.xform("deformedCylinder",t = move )
    cmds.makeIdentity(a=1,t=1)
    cmds.delete(deformedCylinder,ch=1)
    wireDeformerNode = cmds.wire(deformedCylinder, w=final_crv_layer, gw=0, en = 1.0, ce=0, li=0,n="crv_wire_deformer")[0]
    cmds.setAttr("%s.dropoffDistance[0]"%wireDeformerNode, 100)
    cmds.connectAttr("master_ctrl.scaleY","%s.scale[0]"%wireDeformerNode)
    cmds.connectAttr("master_ctrl.scaleY","master_ctrl.scaleZ")

    
    # CTRL visibility control
    cmds.addAttr( "master_ctrl", longName='ctrlVisibility', attributeType='long', h=0, dv=1, hxv=1, hnv=1, min = 0, max =final_crv_layer_no-1)
    cmds.setAttr( "master_ctrl.ctrlVisibility", keyable=False, channelBox = True, lock=False  )
    for i in range(final_crv_layer_no-1):
        layerVisCondNode = cmds.createNode("condition", n="layer_%s_visibility_condition"%(i+1))
        cmds.setAttr("%s.firstTerm"%layerVisCondNode, i+1)
        cmds.connectAttr("master_ctrl.ctrlVisibility", "%s.secondTerm"%layerVisCondNode)
        cmds.setAttr("%s.operation"%layerVisCondNode, 2)
        cmds.connectAttr("%s.outColorR"%layerVisCondNode, "layer_%s_NPOs.visibility"%(i+1))
        
        
    
# Launch the UI
if __name__ == '__main__':
    try:
        CurveLayerBuilderUI()
    except Exception as e:
        cmds.error("An error occurred: %s" % e)
