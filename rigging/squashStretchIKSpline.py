import maya.cmds as cmds


def squash_stretch_IK_spline(globalScaleCtrl = None):
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
    
    
    ratioNode = cmds.createNode("multiplyDivide", n = currCrv.replace("currShape", "ratio"))
    cmds.connectAttr(currNode+".arcLength",ratioNode+".i1x")
    cmds.connectAttr(origNode+".arcLength",ratioNode+".i2x")
    cmds.setAttr(ratioNode+".operation",2)
    
    globalScaleNode = cmds.createNode("multiplyDivide", n = currCrv.replace("currShape", "globalScale"))
    cmds.connectAttr(ratioNode+".ox",globalScaleNode+".i1x")
    
    cmds.setAttr(globalScaleNode+".i1y",1)
    cmds.setAttr(globalScaleNode+".i1z",1)
    
    if globalScaleCtrl:
        cmds.connectAttr(globalScaleCtrl+".sx",globalScaleNode+".i2x")
        cmds.connectAttr(globalScaleCtrl+".sy",globalScaleNode+".i2y")
        cmds.connectAttr(globalScaleCtrl+".sz",globalScaleNode+".i2z")

    
    fromAttr = '.ox'
    toAttr = '.scaleX'
    for jnt in jntLis:
        cmds.connectAttr(globalScaleNode+fromAttr, jnt+toAttr)
        cmds.connectAttr(globalScaleNode+'.oy', jnt+'.scaleY')
        cmds.connectAttr(globalScaleNode+'.oz', jnt+'.scaleZ')

        
squash_stretch_IK_spline("cable_global_ctrl")