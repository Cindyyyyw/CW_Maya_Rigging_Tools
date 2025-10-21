import maya.cmds as cmds
import maya.mel as mel


#   select all visible mesh
allMeshShapes = cmds.ls(exactType = 'mesh', v=1)
selectList = []
for shape in allMeshShapes:
    allParents = cmds.listRelatives(shape, ap=1)
    globalVisbility = 1
    for parent in allParents:
        if cmds.getAttr(f'{parent}.visibility') == 0:
            globalVisbility = 0
            break
    if globalVisbility == 1:
        selectList.append(cmds.listRelatives(shape, p=1)[0])
cmds.select(selectList)

#   select main skeleton
rootList = cmds.ls('*Root_M', et='joint', r=1)
root = ''
for jnt in rootList:
    if len(jnt)>6 and jnt[-7]==':':
        root = jnt   
    elif jnt == 'Root_M':
        root = jnt
    else:
        continue
cmds.select(cmds.listRelatives(root, ad=1, type='joint'), add=1)
cmds.select(root, add=1)

# cmds.playbackOptions(minTime='-35')

mel.eval("gameFbxExporter();")
