import maya.cmds as cmds

'''
Prerequisite: 
    advanced skeleton facial rig setup completed

    two locators named browBulge_destLoc_{postfix}
    placed where you need the brow bulge to be
    oriented such that Y axis is pointing outwards,
    and Z axis is pointing downwards. X should be 
    pointing towards left side(from the character's
    perspective)

'''


postfix_lis = ['L', 'R']

for postfix in postfix_lis:
    # create ctrl and offset grp
    cmds.select(cl=1)
    offsetGrp = cmds.group(n = f'browBulgeOffsetTest_{postfix}',w=1, em=1)
    parentGrp = f'SideReverse_{postfix}'
    cmds.matchTransform(offsetGrp, f'browBulge_destLoc_{postfix}', pos=1, rot=1)
    cmds.parent(offsetGrp, parentGrp, absolute=1)
    
    # setup attribute for brow ctrl
    browCtrl = f'ctrlBrow_{postfix}'
    cmds.addAttr(browCtrl, longName='frownLineOptions', at = 'enum', en='-------', k=0,h=0 )
    cmds.addAttr(browCtrl, longName='bulge', at = 'float', minValue = 0, k=1,h=0, defaultValue = 0.3 )
    cmds.addAttr(browCtrl, longName='intensity', at = 'float', minValue = 0, k=1,h=0,defaultValue = 1.8 )
    
    offsetRemap = cmds.createNode("remapValue", n = f'browBulgeOffsetRemap_{postfix}' )
    offsetMult = cmds.createNode("multiplyDivide", n = f'browBulgeOffsetMD_{postfix}' )
    
    if postfix == 'R':
        cmds.connectAttr(f'{browCtrl}.intensity', f'{offsetMult}.input2X')
    else:
        L_intensityRev = cmds.createNode('floatMath', n='browBulgeIntensity_reverse')
        cmds.setAttr(f'{L_intensityRev}.operation', 2)
        cmds.setAttr(f'{L_intensityRev}.floatB', -1)

        cmds.connectAttr(f'{browCtrl}.intensity', f'{L_intensityRev}.floatA')
        cmds.connectAttr(f'{L_intensityRev}.outFloat', f'{offsetMult}.input2X')

    cmds.connectAttr(f'{browCtrl}.bulge', f'{offsetMult}.input2Y')
    
    cmds.connectAttr(f'{browCtrl}.squeeze', f'{offsetRemap}.inputValue')
    cmds.connectAttr(f'{offsetRemap}.outColor', f'{offsetMult}.input1')
    cmds.connectAttr(f'{offsetMult}.output', f'{offsetGrp}.translate')

    cmds.setAttr(f'{offsetRemap}.inputMax', 10)
    
    
    mid1_distanceMM = cmds.createNode("multMatrix", n=f'EyeBrowMid1Joint_distanceMM_{postfix}')
    inner_distanceMM = cmds.createNode("multMatrix", n=f'EyeBrowInnerJoint_distanceMM_{postfix}')
    cmds.connectAttr(f'EyeBrowMid1Joint_{postfix}.worldMatrix[0]', f'{mid1_distanceMM}.matrixIn[0]')
    cmds.connectAttr(f'EyeBrowInnerJoint_{postfix}.worldMatrix[0]', f'{inner_distanceMM}.matrixIn[0]')
    cmds.connectAttr(f'{parentGrp}.worldInverseMatrix[0]', f'{mid1_distanceMM}.matrixIn[1]')
    cmds.connectAttr(f'{parentGrp}.worldInverseMatrix[0]', f'{inner_distanceMM}.matrixIn[1]')

    bulgeOffsetBM = cmds.createNode('blendMatrix', n=f'browBulgeOffsetBM_R{postfix}')
    cmds.connectAttr(f'{inner_distanceMM}.matrixSum',f'{bulgeOffsetBM}.target[0].targetMatrix')
    cmds.connectAttr(f'{mid1_distanceMM}.matrixSum',f'{bulgeOffsetBM}.target[1].targetMatrix')
    cmds.connectAttr(f'{offsetGrp}.dagLocalMatrix',f'{bulgeOffsetBM}.inputMatrix')
    
    cmds.setAttr(f'{bulgeOffsetBM}.target[0].rotateWeight', 0)
    cmds.setAttr(f'{bulgeOffsetBM}.target[1].rotateWeight', 0)
    cmds.setAttr(f'{bulgeOffsetBM}.target[1].weight', 0.52)

    
    cmds.disconnectAttr(f'{offsetGrp}.dagLocalMatrix',f'{bulgeOffsetBM}.inputMatrix')
    cmds.connectAttr(f'{bulgeOffsetBM}.outputMatrix', f'{offsetGrp}.offsetParentMatrix')
    cmds.makeIdentity(offsetGrp)
    
    
    
    cmds.select(cl=1)
    bulgeCtrl = cmds.circle(nr=(0, 1, 0), c=(0, 0, 0), n= f'browBulge_{postfix}')[0]
    cmds.delete(bulgeCtrl,ch=1)
    cmds.parent(bulgeCtrl, offsetGrp)
    cmds.makeIdentity(bulgeCtrl)

    cmds.select('FaceJoint_M', replace=1)
    bulgeJoint = cmds.joint(n=f'browBulge_{postfix}')
    bulgeJointMM = cmds.createNode('multMatrix', n=f'browBulgeJointMM_{postfix}')
    
    cmds.connectAttr(f'{bulgeCtrl}.worldMatrix[0]',f'{bulgeJointMM}.matrixIn[0]' )
    cmds.connectAttr(f'FaceJoint_M.worldInverseMatrix[0]',f'{bulgeJointMM}.matrixIn[1]' )
    cmds.connectAttr(f'{bulgeJointMM}.matrixSum', f'{bulgeJoint}.offsetParentMatrix' )

    
    
    
    