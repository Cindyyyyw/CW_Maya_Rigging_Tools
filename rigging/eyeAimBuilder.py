import maya.cmds as cmds




def makeNodes():
    sls = cmds.ls(sl=1)

    iris_diameter = cmds.createNode("floatConstant", n = "l_iris_diameter")    
    eye_buldge_factor = cmds.createNode("floatConstant", n = "l_eye_buldge_factor")    
    cmds.setAttr("%s._f"%iris_diameter, 20)
    cmds.setAttr("%s._f"%eye_buldge_factor, 0.1)
    
    ctrl_jnt = 'l_remote_eye_jnt'
    
    
    for sl in sls:
        parent_jnt = cmds.listRelatives(sl, p=1)[0]
        
        TXNode = cmds.createNode("plusMinusAverage", n = sl+"_TX")
        scaledNode = cmds.createNode("floatMath", n = sl+"_push_factor_scaled")
        YZNode = cmds.createNode("floatMath", n = sl+"_push_factor_YZ")
        sumYNode = cmds.createNode("plusMinusAverage", n = sl+"_push_sum_Y")
        sumZNode = cmds.createNode("plusMinusAverage", n = sl+"_push_sum_Z")
        remapY1Node = cmds.createNode("remapValue", n = sl+"_remap_Y_1")
        remapY2Node = cmds.createNode("remapValue", n = sl+"_remap_Y_2")
        remapZ1Node = cmds.createNode("remapValue", n = sl+"_remap_Z_1")
        remapZ2Node = cmds.createNode("remapValue", n = sl+"_remap_Z_2")
        remapMinY1Node = cmds.createNode("floatMath", n = sl+"_remapMin_Y_1")
        remapMinY2Node = cmds.createNode("floatMath", n = sl+"_remapMin_Y_2")
        remapMinZ1Node = cmds.createNode("floatMath", n = sl+"_remapMin_Z_1")
        remapMinZ2Node = cmds.createNode("floatMath", n = sl+"_remapMin_Z_2")
        remapCondY1Node = cmds.createNode("condition", n = sl+"_remapCond_Y_1")
        remapCondY2Node = cmds.createNode("condition", n = sl+"_remapCond_Y_2")
        remapCondZ1Node = cmds.createNode("condition", n = sl+"_remapCond_Z_1")
        remapCondZ2Node = cmds.createNode("condition", n = sl+"_remapCond_Z_2")
        
        
        # cmds.connectAttr("%s.output1D"%TXNode, "%s.tx"%sl)
        cmds.connectAttr("%s.of"%scaledNode, "%s.i1[0]"%TXNode)
        cmds.setAttr("%s.i1[1]"%TXNode, cmds.getAttr("%s.tx"%sl))
        cmds.connectAttr("%s.output1D"%TXNode, "%s.tx"%sl)

        cmds.connectAttr("%s.of"%eye_buldge_factor, "%s._fa"%scaledNode)
        cmds.connectAttr("%s.of"%YZNode, "%s._fb"%scaledNode)
        cmds.setAttr("%s._cnd"%scaledNode, 2)
        cmds.connectAttr("%s.output1D"%sumYNode, "%s._fa"%YZNode)
        cmds.connectAttr("%s.output1D"%sumZNode, "%s._fb"%YZNode)
        cmds.setAttr("%s._cnd"%YZNode, 2)
        
        cmds.connectAttr("%s.ov"%remapY1Node, "%s.i1[0]"%sumYNode)
        cmds.connectAttr("%s.ov"%remapY2Node, "%s.i1[1]"%sumYNode)
        cmds.connectAttr("%s.ov"%remapZ1Node, "%s.i1[0]"%sumZNode)
        cmds.connectAttr("%s.ov"%remapZ2Node, "%s.i1[1]"%sumZNode)
        
        cmds.connectAttr("%s.of"%remapMinY1Node, "%s.imn"%remapY1Node)
        cmds.connectAttr("%s.of"%remapMinY2Node, "%s.imn"%remapY2Node)
        cmds.connectAttr("%s.of"%remapMinZ1Node, "%s.imn"%remapZ1Node)
        cmds.connectAttr("%s.of"%remapMinZ2Node, "%s.imn"%remapZ2Node)
        
        cmds.connectAttr("%s.imx"%remapY1Node, "%s._fa"%remapMinY1Node)
        cmds.connectAttr("%s.imx"%remapY2Node, "%s._fa"%remapMinY2Node)
        cmds.connectAttr("%s.imx"%remapZ1Node, "%s._fa"%remapMinZ1Node)
        cmds.connectAttr("%s.imx"%remapZ2Node, "%s._fa"%remapMinZ2Node)

        cmds.connectAttr("%s.of"%iris_diameter, "%s._fb"%remapMinY1Node)
        cmds.connectAttr("%s.of"%iris_diameter, "%s._fb"%remapMinY2Node)
        cmds.connectAttr("%s.of"%iris_diameter, "%s._fb"%remapMinZ1Node)
        cmds.connectAttr("%s.of"%iris_diameter, "%s._fb"%remapMinZ2Node)
        
        cmds.setAttr("%s._cnd"%remapMinY1Node, 0)
        cmds.setAttr("%s._cnd"%remapMinY2Node, 1)
        cmds.setAttr("%s._cnd"%remapMinZ1Node, 0)
        cmds.setAttr("%s._cnd"%remapMinZ2Node, 1)
        
        cmds.connectAttr("%s.ry"%ctrl_jnt, "%s.ft"%remapCondY1Node)
        cmds.connectAttr("%s.ry"%ctrl_jnt, "%s.ft"%remapCondY2Node)
        cmds.connectAttr("%s.rz"%ctrl_jnt, "%s.ft"%remapCondZ1Node)
        cmds.connectAttr("%s.rz"%ctrl_jnt, "%s.ft"%remapCondZ2Node)
        
        cmds.connectAttr("%s.imx"%remapY1Node, "%s.st"%remapCondY1Node)
        cmds.connectAttr("%s.imx"%remapY2Node, "%s.st"%remapCondY2Node)
        cmds.connectAttr("%s.imx"%remapZ1Node, "%s.st"%remapCondZ1Node)
        cmds.connectAttr("%s.imx"%remapZ2Node, "%s.st"%remapCondZ2Node)
        
        cmds.setAttr("%s.op"%remapCondY1Node,5)
        cmds.setAttr("%s.op"%remapCondY2Node,2)
        cmds.setAttr("%s.op"%remapCondZ1Node,5)
        cmds.setAttr("%s.op"%remapCondZ2Node,2)
        
        cmds.connectAttr("%s.ry"%ctrl_jnt, "%s.cfr"%remapCondY1Node)
        cmds.connectAttr("%s.ry"%ctrl_jnt, "%s.cfr"%remapCondY2Node)
        cmds.connectAttr("%s.rz"%ctrl_jnt, "%s.cfr"%remapCondZ1Node)
        cmds.connectAttr("%s.rz"%ctrl_jnt, "%s.cfr"%remapCondZ2Node)
        
        cmds.connectAttr("%s.imn"%remapY1Node, "%s.ctr"%remapCondY1Node)
        cmds.connectAttr("%s.imn"%remapY2Node, "%s.ctr"%remapCondY2Node)
        cmds.connectAttr("%s.imn"%remapZ1Node, "%s.ctr"%remapCondZ1Node)
        cmds.connectAttr("%s.imn"%remapZ2Node, "%s.ctr"%remapCondZ2Node)
        
        cmds.setAttr("%s.imx"%remapY1Node, cmds.getAttr("%s.ry"%parent_jnt))
        cmds.setAttr("%s.imx"%remapY2Node, cmds.getAttr("%s.ry"%parent_jnt))
        cmds.setAttr("%s.imx"%remapZ1Node, cmds.getAttr("%s.rz"%parent_jnt)/2)
        cmds.setAttr("%s.imx"%remapZ2Node, cmds.getAttr("%s.rz"%parent_jnt)/2)
        
        

        cmds.setAttr("%s.omx"%remapY1Node, 0.5)
        cmds.setAttr("%s.omx"%remapY2Node, 0.5)
        cmds.setAttr("%s.omx"%remapZ1Node, 0.5)
        cmds.setAttr("%s.omx"%remapZ2Node, 0.5)
        
        cmds.connectAttr("%s.ocr"%remapCondY1Node, "%s.i"%remapY1Node)
        cmds.connectAttr("%s.ocr"%remapCondY2Node, "%s.i"%remapY2Node)
        cmds.connectAttr("%s.ocr"%remapCondZ1Node, "%s.i"%remapZ1Node)
        cmds.connectAttr("%s.ocr"%remapCondZ2Node, "%s.i"%remapZ2Node)


makeNodes()