import maya.cmds as cmds


grpLis = cmds.ls(sl=1)

for grp in grpLis:
    newGrp = grp.replace("l_f", "r_f")
    rx = cmds.getAttr(grp+".rotateX")
    ry = cmds.getAttr(grp+".rotateY")
    rz = cmds.getAttr(grp+".rotateZ")
    cmds.setAttr(newGrp+".rotateX", rx)
    cmds.setAttr(newGrp+".rotateY", ry)
    cmds.setAttr(newGrp+".rotateZ", rz)
    
print("done")