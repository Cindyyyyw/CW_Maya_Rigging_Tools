import maya.cmds as cmds

sl_lis = cmds.ls(sl=1)

for sl in sl_lis:
    parent = cmds.listRelatives(sl, p=1)[0]
    cmds.select(parent)
    bulge_joint = cmds.joint(n = f'{sl}_bulge')
    BM_node = cmds.createNode("blendMatrix", n = f'{bulge_joint}_blendMatrix' )
    remap_node = cmds.createNode("remapValue", n = f'{bulge_joint}_remap' )
    cmds.connectAttr(f'{sl}.rotateZ', f'{remap_node}.inputValue')
    cmds.connectAttr(f'{sl}.dagLocalMatrix', f'{BM_node}.target[0].targetMatrix')
    cmds.connectAttr( f'{BM_node}.outputMatrix', f'{bulge_joint}.offsetParentMatrix')
    cmds.connectAttr(f'{remap_node}.outValue', f'{bulge_joint}.translateY')
    cmds.setAttr(f'{remap_node}.imx', -60)
    cmds.setAttr(f'{remap_node}.omx', -1)
    
    cmds.setAttr(f'{BM_node}.target[0].rotateWeight', 0.25)
    
    cmds.connectAttr(f'{sl}.dagLocalMatrix', f'{BM_node}.inputMatrix')
    cmds.disconnectAttr(f'{sl}.dagLocalMatrix', f'{BM_node}.inputMatrix')