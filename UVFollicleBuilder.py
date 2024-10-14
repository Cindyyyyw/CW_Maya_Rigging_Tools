import maya.cmds as cmds


flcLis = cmds.ls(sl=1)

for flc in flcLis:
    # build nodes 
    nodeLis = [ ['floatConstant',   'defaltDiffU'],         #0
                ['floatConstant',   'defaltDiffV'],         #1
                ['floatConstant',   'defaltU'],             #2
                ['floatConstant',   'defaltV'],             #3
                ['floatConstant',   'UVratio'],             #4
                ['floatMath',   'UVratio_rev'],             #5
                ['plusMinusAverage', 'minU'],               #6
                ['plusMinusAverage', 'minV'],               #7
                ['plusMinusAverage', 'maxU'],               #8
                ['plusMinusAverage', 'maxV'],               #9
                ['multiplyDivide', 'calculatedDiffU'],      #10
                ['multiplyDivide', 'calculatedDiffV'],      #11
                ['multiplyDivide', 'UVratio_preprocess'],   #12
                ['multiplyDivide', 'UVratio_calc'],         #13
                ['remapValue', 'remapU'],                   #14
                ['remapValue', 'remapV']    ]               #15
    nodeNameLis = []
    namePfx = flc.replace("flcShape", "flc")
    for i in range(len(nodeLis)):
        nodeNameLis.append(cmds.createNode(nodeLis[i][0], n = namePfx+"_"+nodeLis[i][1]))
    for j in range(2):
        cmds.connectAttr(nodeNameLis[1-j]+'.outFloat',  nodeNameLis[11-j]+'.i1x')
        cmds.connectAttr(nodeNameLis[1-j]+'.outFloat',  nodeNameLis[11-j]+'.i1y')
        cmds.connectAttr(nodeNameLis[15-j]+'.imx',       nodeNameLis[11-j]+'.i2x')
        cmds.connectAttr(nodeNameLis[15-j]+'.imn',       nodeNameLis[11-j]+'.i2y')
        cmds.connectAttr(nodeNameLis[11-j]+'.ox',        nodeNameLis[9-j]+'.i1[0]')
        cmds.connectAttr(nodeNameLis[11-j]+'.oy',        nodeNameLis[7-j]+'.i1[0]')
        cmds.connectAttr(nodeNameLis[7-j]+'.o1',        nodeNameLis[15-j]+'.omn')
        cmds.connectAttr(nodeNameLis[9-j]+'.o1',        nodeNameLis[15-j]+'.omx')
        cmds.connectAttr(nodeNameLis[3-j]+'.of',        nodeNameLis[9-j]+'.i1[1]')
        cmds.connectAttr(nodeNameLis[3-j]+'.of',        nodeNameLis[7-j]+'.i1[1]')

    cmds.connectAttr(nodeNameLis[4]+'.of',              nodeNameLis[5]+'.floatB')
    cmds.setAttr(nodeNameLis[5]+'.floatA', 1)
    cmds.setAttr(nodeNameLis[5]+'.operation', 1)
    cmds.connectAttr(nodeNameLis[4]+'.of',              nodeNameLis[12]+'.i1x')
    cmds.connectAttr(nodeNameLis[5]+'.of',              nodeNameLis[12]+'.i1y')
    cmds.connectAttr(nodeNameLis[12]+'.ox',             nodeNameLis[13]+'.i1x')
    cmds.connectAttr(nodeNameLis[12]+'.oy',             nodeNameLis[13]+'.i1y')
    cmds.connectAttr(nodeNameLis[13]+'.ox',              nodeNameLis[14]+'.i')
    cmds.connectAttr(nodeNameLis[13]+'.oy',              nodeNameLis[15]+'.i')
    cmds.setAttr(nodeNameLis[0]+'.inFloat', 0.01)
    cmds.setAttr(nodeNameLis[1]+'.inFloat', 0.01)
    cmds.setAttr(nodeNameLis[2]+'.inFloat', cmds.getAttr(namePfx+'.parameterU'))
    cmds.setAttr(nodeNameLis[3]+'.inFloat', cmds.getAttr(namePfx+'.parameterV'))
    cmds.connectAttr(nodeNameLis[14]+'.outValue', namePfx+'.parameterU')
    cmds.connectAttr(nodeNameLis[15]+'.outValue', namePfx+'.parameterV')



    
    
    
    
    
    
    
