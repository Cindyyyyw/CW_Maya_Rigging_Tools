import maya.cmds as cmds


def squash_stretch_IK_spline():
    cmds.select(hi=1)
    jntLis = cmds.ls(sl=1, type="joint")

    crvLis = cmds.ls(sl=1, type="nurbsCurve")

    for i in range(2):
        if 'curr' in crvLis[i]:
            currCrv = crvLis[i]
            currNode = cmds.createNode('curveInfo',n=crvLis[i]+"_crvInfo")
        else:
            origCrv = crvLis[i]
            origNode = cmds.createNode('curveInfo',n=crvLis[i]+"_crvInfo")

    cmds.connectAttr(currCrv+".worldSpace[0]", currNode+".inputCurve")
    cmds.connectAttr(origCrv+".worldSpace[0]", origNode+".inputCurve")


    ratioNode = cmds.createNode("multiplyDivide", n = currCrv.replace("curr", "ratio"))
    cmds.connectAttr(currNode+".arcLength",ratioNode+".i1x")
    cmds.connectAttr(origNode+".arcLength",ratioNode+".i2x")
    cmds.setAttr(ratioNode+".operation",2)

    fromAttr = '.ox'
    toAttr = '.scaleX'
    for jnt in jntLis:
        cmds.connectAttr(ratioNode+fromAttr, jnt+toAttr)
        
squash_stretch_IK_spline()