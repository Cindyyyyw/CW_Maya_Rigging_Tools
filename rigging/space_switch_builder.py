import maya.cmds as cmds
import math


def create_space_loc(obj_lis, space_lis):
    obj_loc_grp=[]
    for obj in obj_lis:
        loc_grp = []
        space_grp = cmds.group(empty=True, w=1, name="%s_space_loc_grp"% obj)
        cmds.matchTransform(space_grp, obj)
        for space in space_lis:
            space_loc = cmds.spaceLocator(n="%s_%s_space_loc"% (obj, space))
            loc_grp.append(space_loc)
            cmds.matchTransform(space_loc, obj)
            cmds.parent(space_loc, space_grp)
        obj_loc_grp.append(loc_grp)
    return obj_loc_grp
    

def add_space_attr(obj_lis, space_lis):
    num_of_space = len(space_lis)
    space_enum_name = ''
    for i in range(num_of_space):
        if num_of_space - i > 1:
            space_enum_name = space_enum_name + space_lis[i] + ":"
        else:
            space_enum_name = space_enum_name + space_lis[i]
        
        
    for obj in obj_lis:
        spaceCtrlAttr = cmds.addAttr(obj, longName='spaceCtrl', attributeType="enum", enumName="------", defaultValue=0, keyable=0, h=0)
        spaceAAttr = cmds.addAttr(obj, longName='spaceA', attributeType="enum", enumName = space_enum_name, defaultValue=0, h=0)
        spaceBAttr = cmds.addAttr(obj, longName='spaceB', attributeType="enum", enumName = space_enum_name, defaultValue=0, h=0)
        spaceBlendAttr = cmds.addAttr(obj, longName='spaceBlend', attributeType="float", max=1, min=0, h=0)
        cmds.setAttr("%s.spaceCtrl"% obj, keyable=False, channelBox=True)
        cmds.setAttr("%s.spaceA"% obj, keyable=True)
        cmds.setAttr("%s.spaceB"% obj, keyable=True)
        cmds.setAttr("%s.spaceBlend"% obj, keyable=True)

def setup_node_graph(obj_lis, space_lis):
    for obj in obj_lis:
        num_of_space = len(space_lis)
        num_of_weighted_node_grp = int(math.ceil(num_of_space/3.0))

        
        cond_nodeA = []
        cond_nodeB = []
        
        weight_node = []
        
        for i in range(num_of_space):
            # build cond nodes
            nodeA = cmds.createNode("condition", n="%s_%s_cond_A"%(obj, space_lis[i]))
            cmds.connectAttr("%s.spaceA" %obj, "%s.firstTerm"%nodeA)
            cmds.setAttr("%s.secondTerm"%nodeA, i)
            cmds.setAttr("%s.operation"%nodeA, 0)
            cmds.setAttr("%s.colorIfTrue"%nodeA, 1,1,1)
            cmds.setAttr("%s.colorIfFalse"%nodeA, 0,0,0)
            
            cond_nodeA.append(nodeA)
            
            nodeB = cmds.createNode("condition", n="%s_%s_cond_B"%(obj, space_lis[i]))
            cmds.connectAttr("%s.spaceB" %obj, "%s.firstTerm"%nodeB)
            cmds.setAttr("%s.secondTerm"%nodeB, i)
            cmds.setAttr("%s.operation"%nodeB, 0)
            cmds.setAttr("%s.colorIfTrue"%nodeB, 1,1,1)
            cmds.setAttr("%s.colorIfFalse"%nodeB, 0,0,0)
            
            cond_nodeB.append(nodeB)
            
            nodeW = cmds.createNode("plusMinusAverage", n="%s_%s_weight"%(obj, space_lis[i]))
            
            weight_node.append(nodeW)

        weighted_nodeA = []
        weighted_nodeB = []
        
        
        invNode = cmds.createNode("floatMath", n = "%s_space_blend_inv"%obj)
        cmds.connectAttr("%s.spaceBlend"%obj, "%s.floatB"%invNode)
        cmds.setAttr("%s.floatA"%invNode, 1)
        cmds.setAttr("%s.operation"%invNode, 1)
        
        
        for i in range(num_of_weighted_node_grp):
            # build weighted nodes
            nodeA = cmds.createNode("multiplyDivide", n = "%s_space_weighted_A%s"%(obj, i))
            
            cmds.connectAttr("%s.outFloat"%invNode, "%s.input2X"%nodeA)
            cmds.connectAttr("%s.outFloat"%invNode, "%s.input2Y"%nodeA)
            cmds.connectAttr("%s.outFloat"%invNode, "%s.input2Z"%nodeA)
            
            weighted_nodeA.append(nodeA)

            nodeB = cmds.createNode("multiplyDivide", n = "%s_space_weighted_B%s"%(obj, i))
            
            cmds.connectAttr("%s.spaceBlend"%obj, "%s.input2X"%nodeB)
            cmds.connectAttr("%s.spaceBlend"%obj, "%s.input2Y"%nodeB)
            cmds.connectAttr("%s.spaceBlend"%obj, "%s.input2Z"%nodeB)
            
            weighted_nodeB.append(nodeB)
            curr_pos = i*3
            # print("curr_pos:"+str(curr_pos))
            # print("num_of_space"+str(num_of_space))
            if curr_pos + 2 >= num_of_space:
                num_of_connections = num_of_space - curr_pos
            else:
                num_of_connections = 3
            # print("num_of_connections"+str(num_of_connections))
            if num_of_connections >= 1:
                cmds.connectAttr("%s.outColorR"%cond_nodeA[curr_pos], "%s.input1X"%nodeA)
                cmds.connectAttr("%s.outputX"%nodeA, "%s.input1D[0]"%weight_node[curr_pos])
                cmds.connectAttr("%s.outColorR"%cond_nodeB[curr_pos], "%s.input1X"%nodeB)
                cmds.connectAttr("%s.outputX"%nodeB, "%s.input1D[1]"%weight_node[curr_pos])

                curr_pos+=1
                
                if num_of_connections >= 2:
                    cmds.connectAttr("%s.outColorR"%cond_nodeA[curr_pos], "%s.input1Y"%nodeA)
                    cmds.connectAttr("%s.outputY"%nodeA, "%s.input1D[0]"%weight_node[curr_pos])

                    cmds.connectAttr("%s.outColorR"%cond_nodeB[curr_pos], "%s.input1Y"%nodeB)
                    cmds.connectAttr("%s.outputY"%nodeB, "%s.input1D[1]"%weight_node[curr_pos])

                    curr_pos+=1
                    
                    if num_of_connections ==3:
                        cmds.connectAttr("%s.outColorR"%cond_nodeA[curr_pos], "%s.input1Z"%nodeA)
                        cmds.connectAttr("%s.outputZ"%nodeA, "%s.input1D[0]"%weight_node[curr_pos])

                        cmds.connectAttr("%s.outColorR"%cond_nodeB[curr_pos], "%s.input1Z"%nodeB)
                        cmds.connectAttr("%s.outputZ"%nodeB, "%s.input1D[1]"%weight_node[curr_pos])
                        



spaces = ["Global", "Local", "Sheath", "leftHand", "rightHand"]
obj_lis = cmds.ls(sl=1, ap=1)

add_space_attr(obj_lis, spaces)
obj_loc_grp = create_space_loc(obj_lis, spaces)
setup_node_graph(obj_lis, spaces)
