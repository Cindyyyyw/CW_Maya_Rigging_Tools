import maya.cmds as cmds

rDict = {'thumb': [0,0,0]}

def build_pose_const(poseNum, jntLis):
    nodeLis = []
    for jnt in jntLis:
        # try:
        poseNode = cmds.createNode('colorConstant', n=jnt+'_constant_'+str(poseNum))
        tempX = cmds.getAttr(jnt+'.jointOrientX')
        cmds.setAttr(poseNode+'.inColorR', tempX)
        tempY = cmds.getAttr(jnt+'.jointOrientY')
        cmds.setAttr(poseNode+'.inColorG', tempY)
        tempZ = cmds.getAttr(jnt+'.jointOrientZ')
        cmds.setAttr(poseNode+'.inColorB', tempZ)
        nodeLis.append(poseNode)
        # except:
        #     print("Failed to create poseNode for " + jnt )
    return nodeLis

def build_condition(poseNum, jntLis):

    nodeLis = build_pose_const(poseNum, jntLis)
    condNodeLis = []
    
    for jnt in jntLis:
        poseNode = jnt+'_constant_'+str(poseNum)
        condNode = cmds.createNode('condition', n=jnt+'_condition_'+str(poseNum))
        cmds.setAttr(condNode+'.ft', poseNum)
        cmds.connectAttr('l_gesture_ctrl'+'.initialPose', condNode+'.st')
        cmds.connectAttr(poseNode + '.outColor',condNode+'.ct')
        condNodeLis.append(condNode)
    return condNodeLis

def connect_condition_to_plus_node(poseNum):
    jntLis = cmds.ls(sl=1)
    build_condition(poseNum, jntLis)
    plusNode = jnt+'_condition_'+str(poseNum)
    if cmds.objExists(plusNode):
        pass
    else: # create the node if none exists already
        cmds.createNode('plusMinusAverage', n = plusNode)
    print(cmds.getAttr(plusNode+"i3"))
    
    
    

# build_pose_const('0')
# build_condition(0)
ctrlLis = cmds.ls("*_ctrl", sl=1)

for ctrl in ctrlLis:
    poseGrp = cmds.group(em=1, w=1, n=ctrl+"_pose_grp")
    cmds.matchTransform(poseGrp, ctrl)
    cmds.parent(ctrl, poseGrp)
    cmds.parent(poseGrp, ctrl+"_grp")
    
    
    
cmds.select(cmds.ls("*_pose_grp", sl=1))

    
    
    
    
    
    