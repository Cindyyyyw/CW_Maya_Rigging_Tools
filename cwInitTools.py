import maya.cmds as cmds
import maya.api.OpenMaya as om
import sys
# on windows
# sys.path.append("E:/Rigging/scripts/tpTools")
# on mac
sys.path.append("/Volumes/CINDY/Rigging/scripts/tpTools")

import tpRig.tpControl.tpControl as tpControl

# setup control at the origin without constraints


def get_child_jnt(rootJntLis):
    """
    ### Description:
    Takes a list of joints and returns a list of child joints in hierarchy order\n
    ### Parameters:
    1. rootJntLis: list
        - a list containing all root joints 
    ### Output:
    1. fullJntLis: list(nested)
        - a list of root and child joints in hierarchy order
    ### Note:
    Function reads the max amount of child joints from the first joint and uses 
    that number as a reference for all joints in the list.
    ### Example:
        in  ->  [a_ik_jnt, a_fk_jnt, a_jnt]\n
        out ->  [[a_ik_jnt, a_fk_jnt, a_jnt],\n 
                 [b_ik_jnt, b_fk_jnt, b_jnt],\n
                 [c_ik_jnt, c_fk_jnt, c_jnt]]\n
    """
    # count the number of children from first joint in root joint list
    min = len(cmds.listRelatives(rootJntLis[0], ad = True, type = "joint"))

    # check if every root joint in the list have the minimum amount of joints down the chain
    for i in range(len(rootJntLis)-1):
        if len(cmds.listRelatives(rootJntLis[i+1], ad = True, type = "joint")) < min:
            raise ValueError('Joint [{}] contains insufficient child joints'.format(rootJntLis[i+1]))

    # append child joints to the list
    fullJntLis = [rootJntLis]
    for i in range(1, min+1):
        temp = []
        for j in range(len(rootJntLis)):
            temp.append(cmds.listRelatives(fullJntLis[i-1][j])[0])
        fullJntLis.append(temp)
    return fullJntLis
    
def read_jnt_pfx(name):
    """
    ### Description:
    returns prefix of an joint before 'fk', 'ik', or 'jnt'
    ### Parameters:
    1. name: string
        - the joint object's name
    ### Output:
    1. namePfx: string
        - prefix of name
    ### Example:
    eg. l_leg_jnt    ->  l_leg\n
        l_leg_fk_jnt    ->  l_leg\n
        l_leg_fk_1_jnt  ->  l_leg\n
        l_leg_1_fk_jnt  ->  l_leg_1\n
    """
    # names should have a minimum length of 2
    if len(name) <= 2:
        return name
    
    # check every word in the name that are seperated by '_'
    # and returns the position of 'fk' or 'ik'
    buffer = name.split('_')
    pos = -1
    
    for i in range(len(buffer)):
        current = buffer[i]
        current = current.lower()
        if current == 'fk' or current == 'ik' or current == 'jnt':
            pos = i
            break
    # no keyword detected
    if pos == -1:
        raise ValueError("invalid joint name, only names with 'ik', 'fk', or 'jnt' are accepted.")

    # append everything before 'fk' or 'ik' back into the namePfx
    namePfx = buffer[0]
    for i in range(1, pos):
        namePfx = namePfx + '_' + buffer[i]
    return str(namePfx)

def create_ik_fk_system(blend = False):
    """
    ### Description:
    Creates an IK/FK system where joints and their child joints will be 
    parent constrained to both IK and FK joints with the same naming convention.\n
    Optional: blend control\n
    Creates two nodes:
    -   control float
    -   reverse control float

    ### Parameters:
    1. blend: bool
    -   defalt False
    -   when True, creates a control with offset group at world origin
        that is capable of controlling the blend between IK and FK created
        by the function

    ### Prerequisites: 
    -   only one of the IK/FK root joint needs to be selected
    -   naming convention needs to be formatted properly
    -   the selected joint (either ik or fk) needs to have the minimum amount 
        of child joints among the other root joints
    """
    rootJntLis = get_root_jnt()
    jntPfx = read_jnt_pfx(rootJntLis[0])
    fullJntLis = get_child_jnt(rootJntLis)
    floatNode = cmds.createNode('floatCorrect', name = jntPfx + '_ik_fk_ctrl_float')
    cmds.setAttr(floatNode + '.clampOutput', True)
    revNode = cmds.createNode('reverse', name = jntPfx + '_ik_fk_ctrl_float_reverse')
    
    cmds.connectAttr(floatNode + '.outFloat', revNode + '.inputX')
    
    for subJntLis in fullJntLis:
        constraintNode = cmds.parentConstraint(subJntLis[0],subJntLis[1],subJntLis[2], maintainOffset=False)[0]
        constraintNodeAttrLis = cmds.listAttr(constraintNode, userDefined=True)
        
        cmds.connectAttr(floatNode + '.outFloat', constraintNode + '.' + constraintNodeAttrLis[0])
        cmds.connectAttr(revNode + '.outputX', constraintNode + '.' + constraintNodeAttrLis[1])

    # sets up a blend control if needed
    if blend == True:
        blendCtrl = create_ctrl(jntPfx+"_ik_fk_ctrl", "diamond")
        cmds.select(blendCtrl)
        cmds.addAttr(cmds.ls(sl=1)[0], longName='IK_FK_Blend', defaultValue=0, min=0, max=1, at = "float" )
        cmds.setAttr(cmds.ls(sl=1)[0]+'.IK_FK_Blend',channelBox=True)
        cmds.setAttr(cmds.ls(sl=1)[0]+'.IK_FK_Blend',lock=False)
        cmds.setAttr(cmds.ls(sl=1)[0]+'.IK_FK_Blend',keyable=True)
        cmds.connectAttr(blendCtrl+".IK_FK_Blend", floatNode+".inFloat")

def get_root_jnt():
    """
    ### Description:
    Help select root joints in an "IK -> FK -> Main" order
    
    ### Prerequisites: 
    -   one of the IK/FK root joint needs to be selected
    -   naming convention needs to be formatted properly
    
    ### Output:
    rootJntLis: unicode list
    """
    rootJointName = cmds.ls(selection = True)[0]
    prefix = read_jnt_pfx(rootJointName)
    rootJntLis = [  (prefix+'_ik_jnt').decode('utf_8'),
                    (prefix+'_fk_jnt').decode('utf_8'),
                    (prefix+'_jnt').decode('utf_8')]
    return rootJntLis
    
def create_ctrl(ctrlName, type='open_circle', color = 'blue', matchObj = '', constraint = False):
    """
    ### Description:
    Creates a control with offset grp, it will be placed at the world center if no matching object were specified,
    it is also optional to constrain the matching object with a parent constraint

    ### Output:
    ctrlName: string
    """
    # available shapes: 
    # 'cube','diamond','arrow','open_circle',
    # 'sphere','move','crown','cross',
    # '5_cv_streight','cube_on_base','half_circle',
    # 'fist','single_rotate','foot','rotation'
    newCtrl = tpControl.Control(name=ctrlName) 
    newCtrl.set_type(type)
    newCtrl.set_color_preset(color)
    newCtrl.add_offset_grp()
    if matchObj != '':
        cmds.matchTransform(newCtrl.get_top_group(), matchObj)
        if constraint:
            cmds.parentConstraint(ctrlName, matchObj, maintainOffset = True)
    return ctrlName

def constraint_jnt():
    """
    ### Description:
    Creates a control with offset grp that constraints the selected joints
    """
    jnt_list = cmds.ls(selection= True)
    for jnt in jnt_list:
        ctrl = tpControl.Control(name=jnt+'_ctrl')
        # ctrl.set_type('open_circle')
        ctrl.add_offset_grp()
        cmds.matchTransform(ctrl.get_top_group(), jnt)
        cmds.parentConstraint(ctrl.get_name(), jnt, maintainOffset = True)


def create_IK_handle(rootJnt, d=10):
    """
    ### Description:
    Gets 2 children down the chain, and create a ik handle using rotate plane solver.

    ### Output:
    ikHandle: 
    position: position of pole vector
    """
    midJnt = cmds.listRelatives(rootJnt, ad = False, children=True, type = 'joint')[0]
    endJnt = cmds.listRelatives(midJnt, ad = False, children=True, type = 'joint')[0]
    ikHandle = cmds.ikHandle(n = read_jnt_pfx(rootJnt)+'_ikHandle', startJoint=rootJnt, endEffector=endJnt, autoPriority = False, solver='ikRPsolver')
    position = calculate_pole_vector_position(rootJnt, midJnt, endJnt, d)
    
    return ikHandle, position
    
def calculate_pole_vector_position(start_joint, middle_joint, end_joint, distance=10):

    start_pos = cmds.xform(start_joint, q=True, ws=True, t=True)
    middle_pos = cmds.xform(middle_joint, q=True, ws=True, t=True)
    end_pos = cmds.xform(end_joint, q=True, ws=True, t=True)

    start_vector = om.MVector(start_pos[0], start_pos[1], start_pos[2])
    middle_vector = om.MVector(middle_pos[0], middle_pos[1], middle_pos[2])
    end_vector = om.MVector(end_pos[0], end_pos[1], end_pos[2])

    line = end_vector - start_vector
    point = middle_vector - start_vector

    scale_value = (point * line) / (line * line)
    projected_vector = line * scale_value + start_vector

    final_vector = middle_vector - projected_vector
    final_vector.normalize()

    final_vector *= distance
    final_position = middle_vector + final_vector

    return final_position
    
def place_ctrl_at_pos(ctrlName, position):
    """
    ### Description:
    Places a control at provided position
    ### Output:
    ctrlName
    """
    loc = cmds.spaceLocator()[0]
    cmds.xform(loc, ws=True, t=[position.x, position.y, position.z])
    create_ctrl(ctrlName = ctrlName, type="open_circle", matchObj=loc)
    cmds.delete(loc)

    # ctrl = tpControl.Control(name=ctrlName)
    # ctrl.set_type('open_circle')
    # ctrl.add_offset_grp()
    # cmds.matchTransform(ctrl.get_top_group(), loc)


def create_3_jnt_RP_IK():
    """
    ### Description:
    Creates a 3 joint Ik chain using rotate plane solver,
    and places a pole vector control at the correct position.
    Simply have the root selected before executing
    """
    rootJnt = cmds.ls(selection = True, type='joint')[0] 
    ikHandle, pos = create_IK_handle(rootJnt)
    ctrlName = read_jnt_pfx(rootJnt)+"_pv_ctrl"
    place_ctrl_at_pos(ctrlName, pos)
    cmds.poleVectorConstraint( ctrlName, ikHandle[0])


# create_3_jnt_RP_IK()
    
# create_ik_fk_system(1)
