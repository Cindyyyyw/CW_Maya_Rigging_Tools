import maya.cmds as cmds

def build_twist_joints(selected_joint, num_twist_joints, solvingMethod):
    # Ensure the selected joint has exactly one child
    children = cmds.listRelatives(selected_joint, type="joint", children=True)
    if not children or len(children) != 1:
        cmds.warning("Selected joint must have exactly one child joint.")
        return
    
    child_joint = children[0]
    
    # Create a group to contain all twist joints
    twist_group = cmds.group(empty=True, name="%s_rev_jnt_grp" % selected_joint)
    
    # Match the group's transforms to the selected joint
    cmds.matchTransform(twist_group, selected_joint)
    
    # Parent the group under the selected joint, but leave the original child joint alone
    cmds.parent(twist_group, selected_joint)
    print("method %s chosen" % solvingMethod)
    if solvingMethod ==1:
        
        
        # # Create plusMinusAverage node for the selected joint and its child
        # twist_tot_node = cmds.createNode("plusMinusAverage", name = "%s_plusMinusAverage" % selected_joint) 
        # cmds.connectAttr("%s.rotate" % selected_joint, "%s.input3D[0]" % twist_tot_node)
        # cmds.connectAttr("%s.rotate" % child_joint, "%s.input3D[1]" % twist_tot_node)
        # cmds.setAttr("%s.operation" % twist_tot_node, 1)

        # Create eulerToQuat node for the selected joint
        euler_to_quat_node = cmds.createNode("eulerToQuat", name="%s_eulerToQuat1" % selected_joint)
        cmds.connectAttr("%s.rotate" % selected_joint, "%s.inputRotate" % euler_to_quat_node)
        euler_to_quat_node2 = cmds.createNode("eulerToQuat", name="%s_eulerToQuat2" % selected_joint)
        cmds.connectAttr("%s.rotate" % child_joint, "%s.inputRotate" % euler_to_quat_node2)
        quat_to_euler_node2 = cmds.createNode("quatToEuler", name="%s_quatToEuler2" % selected_joint)
        cmds.connectAttr("%s.outputQuat" % euler_to_quat_node2, "%s.inputQuat" % quat_to_euler_node2)
        
    else:
        # Create eulerToQuat node for the selected joint
        euler_to_quat_node = cmds.createNode("eulerToQuat", name="%s_eulerToQuat1" % selected_joint)
        cmds.connectAttr("%s.rotate" % child_joint, "%s.inputRotate" % euler_to_quat_node)
        
    # Create quatToEuler node for the selected joint
    quat_to_euler_node = cmds.createNode("quatToEuler", name="%s_quatToEuler1" % selected_joint)
    cmds.connectAttr("%s.outputQuat" % euler_to_quat_node, "%s.inputQuat" % quat_to_euler_node)
    
    # Create a list to hold the twist joints
    twist_joints = []
    
    for i in range(num_twist_joints):
        # Create a twist joint
        twist_joint_name = "%s_rev_jnt_%d" % (selected_joint, i)
        twist_joint = cmds.joint(name=twist_joint_name)
        
        
        # Parent the twist joint under the twist group
        cmds.parent(twist_joint, twist_group)
        cmds.matchTransform(twist_joint, selected_joint)
        cmds.setAttr("%s.jointOrientX" % twist_joint, 0)
        cmds.setAttr("%s.jointOrientY" % twist_joint, 0)
        cmds.setAttr("%s.jointOrientZ" % twist_joint, 0)
        cmds.setAttr("%s.rotateY" % twist_joint, 0)
        cmds.setAttr("%s.rotateZ" % twist_joint, 0)
        
        
        twist_joints.append(twist_joint)
        
        # Create multiplyDivide node for each twist joint
        mult_div_node = cmds.createNode("multiplyDivide", name="%s_multiplyDivide" % twist_joint_name)
        
        # Set input1X from the child joint's translateX
        cmds.connectAttr("%s.translateX" % child_joint, "%s.input1X" % mult_div_node)
        
        # Set input1Y from quatToEuler node's outputRotateX
        cmds.connectAttr("%s.outputRotateX" % quat_to_euler_node, "%s.input1Y" % mult_div_node)
        
        if(solvingMethod==1):
            # Set input1Z from quatToEuler2 node's outputRotateX
            cmds.connectAttr("%s.outputRotateX" % quat_to_euler_node2, "%s.input1Z" % mult_div_node)
            
            # Calculate input2X and input2Y
            portion = 1.0 / num_twist_joints  # percentage of each portion
            input2X = portion * i
            input2Y = portion * (num_twist_joints - i) * -1
            input2Z = portion * i
            cmds.setAttr("%s.input2X" % mult_div_node, input2X)
            cmds.setAttr("%s.input2Y" % mult_div_node, input2Y)
            cmds.setAttr("%s.input2Z" % mult_div_node, input2Z)
            
            # create another node to add input YZ together
            twist_tot_node = cmds.createNode("plusMinusAverage", name="%s_plusMinusAverage" % selected_joint)
            cmds.connectAttr("%s.outputY" % mult_div_node, "%s.input1D[0]" % twist_tot_node)
            cmds.connectAttr("%s.outputZ" % mult_div_node, "%s.input1D[1]" % twist_tot_node)
            
            # Connect the outputX to the twist joint's translateX
            cmds.connectAttr("%s.outputX" % mult_div_node, "%s.translateX" % twist_joint)
            
            # Connect the outputY to the twist joint's rotateX
            cmds.connectAttr("%s.output1D" % twist_tot_node, "%s.rotateX" % twist_joint)
            
            
            
        else:
            # Calculate input2X and input2Y
            input2X = (1.0 / num_twist_joints) * i
            input2Y = (1.0 / num_twist_joints) * i
            cmds.setAttr("%s.input2X" % mult_div_node, input2X)
            cmds.setAttr("%s.input2Y" % mult_div_node, input2Y)
            
            # Connect the outputX to the twist joint's translateX
            cmds.connectAttr("%s.outputX" % mult_div_node, "%s.translateX" % twist_joint)
            
            # Connect the outputY to the twist joint's rotateX
            cmds.connectAttr("%s.outputY" % mult_div_node, "%s.rotateX" % twist_joint)
        
    # # Ensure the original child joint remains parented to the selected joint
    # cmds.parent(child_joint, selected_joint)

def twist_joint_builder_UI():
    if cmds.window("twistJointBuilderUI", exists=True):
        cmds.deleteUI("twistJointBuilderUI")
    
    window = cmds.window("twistJointBuilderUI", title="Twist Joint Builder", widthHeight=(500, 150))
    cmds.columnLayout(adjustableColumn=True)
    
    cmds.text(label="Select a Joint with One Child")
    cmds.separator(height=10, style='in')
    
    cmds.intSliderGrp('twistJointsSlider', label='Number of Twist Joints ', field=True, minValue=1, maxValue=10, value=5)
    cmds.radioButtonGrp('solvingMethod', label="Method ", labelArray2=["Rev root", "Root"], numberOfRadioButtons=2, select=1)  # Set the default selected radio button (1 for Option A))
    
    
    cmds.separator(height=10, style='in')
    cmds.button(label="Build Twist Joints", command=build_twist_joints_from_UI)
    
    cmds.showWindow(window)

def build_twist_joints_from_UI(*args):
    selected_joint = cmds.ls(selection=True)
    
    if not selected_joint:
        cmds.warning("Please select a joint.")
        return
    
    selected_joint = selected_joint[0]
    num_twist_joints = cmds.intSliderGrp('twistJointsSlider', query=True, value=True)
    method = cmds.radioButtonGrp("solvingMethod", query = True, select=True)
    build_twist_joints(selected_joint, num_twist_joints, method)

# Launch the UI
twist_joint_builder_UI()
