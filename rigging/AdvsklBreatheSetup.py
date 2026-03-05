import maya.cmds as cmds

def setup():
    breathe_ctrl= 'breathe_M'
    offset_grp = cmds.listRelatives(breathe_ctrl,p=1)[0]

    # 1. give offset parent matrix to breathe control's offset grp

    # cmds.connectAttr('ChestPM_M.outputMatrix', f'{offset_grp}.offsetParentMatrix')
    cmds.connectAttr('Chest_M.worldMatrix', f'{offset_grp}.offsetParentMatrix')

    cmds.xform(offset_grp, r=1, t=(-2.5, 0, -25))
    cmds.setAttr(f'{offset_grp}.translate', l=1, cb=0)
    cmds.setAttr(f'{offset_grp}.rotate', l=1, cb=0)
    cmds.setAttr(f'{offset_grp}.scale', l=1, cb=0)
    cmds.setAttr(f'{offset_grp}.visibility', l=1, cb=0)

    # 2. attribute setup for breathe control

    cmds.addAttr(breathe_ctrl, longName='breathe', at='short', hnv=1, hxv=1, min=0, max=10, dv=0 )
    cmds.addAttr(breathe_ctrl, longName='breatheAttributes', at='enum', en='-------' )
    cmds.addAttr(breathe_ctrl, longName='chestScale', at='float', hnv=1, min=0, dv=1.015 )
    cmds.addAttr(breathe_ctrl, longName='scapulaRotY', at='float', dv=-1 )
    cmds.addAttr(breathe_ctrl, longName='scapulaRotZ', at='float', dv=0.5 )

    cmds.setAttr(f'{breathe_ctrl}.breathe', cb=1, k=1)
    cmds.setAttr(f'{breathe_ctrl}.breatheAttributes', cb=1, k=0, l=1)
    cmds.setAttr(f'{breathe_ctrl}.chestScale', cb=1, k=1)
    cmds.setAttr(f'{breathe_ctrl}.scapulaRotY', cb=1, k=1)
    cmds.setAttr(f'{breathe_ctrl}.scapulaRotZ', cb=1, k=1)


    # 3. build nodes

    chestScaleRemap = cmds.createNode('remapValue',n='breathe_remap_chest_scale')
    scapulaRotYRemap = cmds.createNode('remapValue',n='breathe_remap_scapula_rotY')
    scapulaRotZRemap = cmds.createNode('remapValue',n='breathe_remap_scapula_rotZ')
    chestCompMatrix  = cmds.createNode('composeMatrix',n='breathe_comp_chest_scale')


    # 4. connect nodes

    cmds.connectAttr(f'{breathe_ctrl}.breathe',f'{chestScaleRemap}.inputValue')
    cmds.connectAttr(f'{breathe_ctrl}.breathe',f'{scapulaRotYRemap}.inputValue')
    cmds.connectAttr(f'{breathe_ctrl}.breathe',f'{scapulaRotZRemap}.inputValue')
    cmds.connectAttr(f'{breathe_ctrl}.chestScale',f'{chestScaleRemap}.outputMax')
    cmds.connectAttr(f'{breathe_ctrl}.scapulaRotY',f'{scapulaRotYRemap}.outputMax')
    cmds.connectAttr(f'{breathe_ctrl}.scapulaRotZ',f'{scapulaRotZRemap}.outputMax')

    cmds.connectAttr(f'{chestScaleRemap}.outColor',f'{chestCompMatrix}.inputScale')

    # cmds.connectAttr(f'{chestCompMatrix}.outputMatrix', 'ChestMM_M.matrixIn[2]')
    cmds.connectAttr(f'{chestCompMatrix}.outputMatrix', 'Chest_M.offsetParentMatrix')

    ScapulaCM_L = cmds.createNode('composeMatrix', n = 'FKExtraScapulaCM_L' )
    cmds.connectAttr(f'{scapulaRotYRemap}.outValue', f'{ScapulaCM_L}.inputRotateY')
    cmds.connectAttr(f'{scapulaRotZRemap}.outValue', f'{ScapulaCM_L}.inputRotateZ')
    cmds.connectAttr(f'{ScapulaCM_L}.outputMatrix', 'FKExtraScapula_L.offsetParentMatrix')
    
    
    
    cmds.connectAttr(f'{scapulaRotYRemap}.outValue', 'FKExtraScapula_R.rotateY')
    # cmds.connectAttr(f'{scapulaRotYRemap}.outValue', 'FKExtraScapula_L.rotateY')
    cmds.connectAttr(f'{scapulaRotZRemap}.outValue', 'FKExtraScapula_R.rotateZ')
    # cmds.connectAttr(f'{scapulaRotZRemap}.outValue', 'FKExtraScapula_L.rotateZ')


    cmds.setAttr(f'{chestScaleRemap}.inputMax', 10)
    cmds.setAttr(f'{scapulaRotYRemap}.inputMax', 10)
    cmds.setAttr(f'{scapulaRotZRemap}.inputMax', 10)

    cmds.setAttr(f'{chestScaleRemap}.outputMin', 1)
