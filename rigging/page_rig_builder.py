import maya.cmds as cmds
from importlib import reload

import os
import sys
sys.path.insert(0, r"/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools")
from control import CWControlManager as ctrl
from utility import renameShapeNodes as renameSN

systemParent = 'CustomSystem'
jointParent = 'Root_M'
locatorParent = 'Root_M'

# build bookpage rig, by inputting the dimension of the page: width, height, width subdiv, height subdiv
# the script is going to create a plane, while assuming that the vertice of the plane is going to follow the sequential order 

def buildCtrl(pagePfx, width=10, height=10):
    libDir = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/control/'
    manager = ctrl(os.path.join(libDir, 'CWControlLib.json'))
    main_ctrl = manager.createShape('cube', f'{pagePfx}_main_ctrl', True)
    rot_ctrl = manager.createShape('square', f'{pagePfx}_rot_ctrl', True)
    manager.setCurveWidth(5, rot_ctrl)
    cmds.xform(rot_ctrl, s=[1,1,(height/2)+1])
    cmds.makeIdentity(rot_ctrl, apply=1)

    main_ctrl_parent = cmds.listRelatives(main_ctrl, p=1)[0]
    main_ctrl_parent = cmds.rename(main_ctrl_parent, f'{pagePfx}_main_ctrl_offset' )
    cmds.rename(cmds.listRelatives(rot_ctrl, p=1)[0], f'{pagePfx}_rot_ctrl_offset' )

    cmds.xform(main_ctrl_parent, t=[width,0,0])
    cmds.parent(main_ctrl_parent, rot_ctrl)
    
    # renameSN(sl_list=[main_ctrl, rot_ctrl])
    
    lock_attr_rot = ['tx', 'ty', 'tz', 'rx', 'ry', 'sx', 'sy', 'sz', 'visibility']
    lock_attr_main = [ 'ty', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility']

    # build attributes on both ctrl
    for attr in lock_attr_rot:
        cmds.setAttr(f'{rot_ctrl}.{attr}', l=1, cb=0, k=0)
    for attr in lock_attr_main:
        cmds.setAttr(f'{main_ctrl}.{attr}', l=1, cb=0, k=0)
    
    cmds.addAttr(main_ctrl, longName = 'bound', min=0, max=10, dv=5 )
    cmds.addAttr(main_ctrl, longName = 'height', min=0, max=width, dv=width/2 )
    cmds.addAttr(main_ctrl, longName = 'coverBendSettings',at='enum', en='-------')
    cmds.addAttr(main_ctrl, longName = 'rotateFollow', min=0, max=1, dv=0.5 )
    cmds.addAttr(main_ctrl, longName = 'bendFollow', min=0, max=1, dv=1 )
    cmds.addAttr(main_ctrl, longName = 'curvatureMax', min=0, max=50, dv=43 )
    cmds.addAttr(main_ctrl, longName = 'boundMax', min=0, max=2, dv=1 )

    cmds.setAttr(f'{main_ctrl}.bound', cb=1, k=1)
    cmds.setAttr(f'{main_ctrl}.height', cb=1, k=1)
    cmds.setAttr(f'{main_ctrl}.coverBendSettings', cb=1, l=1)
    cmds.setAttr(f'{main_ctrl}.rotateFollow', cb=1, k=1)
    cmds.setAttr(f'{main_ctrl}.bendFollow', cb=1, k=1)
    cmds.setAttr(f'{main_ctrl}.curvatureMax', cb=1, k=1)
    cmds.setAttr(f'{main_ctrl}.boundMax', cb=1, k=1)

    cmds.transformLimits( main_ctrl, tx=(-width, 0), tz=(height/-2, height/2), etx=(True, True), etz=(True, True ) )
    
    return main_ctrl, rot_ctrl
    
def createPageGeo(pagePfx, height=10, width=10, subHeight=10, subWidth=10):
    pageName = cmds.polyPlane(ch=False, cuv=2, h=height, w=width, sh=subHeight, sw=subWidth, n=pagePfx+'_proxy')[0]
    cmds.xform(pageName, t=[width/2,0,0],piv=[width/-2,0,0], absolute=True)
    cmds.makeIdentity(pageName, apply=1)
    return pageName

def placeJoints(pagePfx, pageName, subWidth=10, subHeight=10, width=10, height=10):
    vert_lis = [[],[],[]]
    # vertice number starts at 0
    bendLis = []
    bendHandleLis=[]
    ikCrvLis=[]
    ikHandleLis=[]
    jntLis=[]
    cmds.select(cl=1)
    rootJnt = cmds.joint(n=f'{pagePfx}_root_jnt')
    jntLis.append(rootJnt)
    upLocLis=[]
    for i in range((subHeight+1)*(subWidth+1)):
        if i < subWidth+1:
            vert_lis[0].append(str(i))
        elif i>= (subWidth+1)*(subHeight/2) and i< (subWidth+1)*(subHeight/2+1):
            vert_lis[1].append(str(i))
        elif i>= (subWidth+1)*(subHeight):
            vert_lis[2].append(str(i))
    for i in range(3):
        cmds.select(rootJnt,r=1)
        for j in range(len(vert_lis[0])):
            vert_pos = cmds.xform(f'{pageName}.vtx[{vert_lis[i][j]}]', q=True, translation=True, ws=True)
            jnt = cmds.joint(p=vert_pos, n=f'{pagePfx}_jnt_{i+1}_{j}')
            if j==0:
                x, y, z = cmds.xform(jnt, q=1, translation=1)
                upLoc = cmds.spaceLocator(a=1, n=f'{pagePfx}_upLoc_{i}')[0]
                upLocLis.append(upLoc)
                cmds.xform(upLoc, t=[x, y+10, z], a=1, os=1)
                cmds.select(jnt, r=1)
        ikHandle, _, ikCrv = cmds.ikHandle(sj=f'{pagePfx}_jnt_{i+1}_0', ee=f'{pagePfx}_jnt_{i+1}_{len(vert_lis[0])-1}', ccv=1, sol='ikSplineSolver', pcv=0, scv=0, n=f'{pagePfx}_ikHandle_{i+1}')
        
        
        cmds.setAttr(f'{ikHandle}.dTwistControlEnable', 1)
        cmds.setAttr(f'{ikHandle}.dWorldUpType', 1)
        cmds.connectAttr(f'{upLoc}.worldMatrix[0]', f'{ikHandle}.dWorldUpMatrix')

        
        ikCrv = cmds.rename(ikCrv,f'{pagePfx}_ikCurve_{i+1}')
        bendNode = cmds.nonLinear(ikCrv, type='bend', n=f'{pagePfx}_bend_{i+1}')[0]
        cmds.setAttr(f'{bendNode}.highBound', 0)
        bendHandle = cmds.rename(f'{bendNode}Handle', f'{pagePfx}_bendHandle_{i+1}')
        cmds.xform(bendHandle, t=[width/-2,0,0], ro=[0,0,90], r=1)
        
        ikHandleLis.append(ikHandle)
        ikCrvLis.append(ikCrv)
        bendLis.append(bendNode)
        bendHandleLis.append(bendHandle)
    return ikHandleLis, ikCrvLis, bendLis, bendHandleLis, jntLis, upLocLis

def connectAttr(pagePfx, bendNodeLis, mainCtrl, rotCtrl, bendHandleLis, curveCtrlGrp, ctrlGrp,upLocGrp,jntGrp, width=10, height=10):
    # Part 1: main ctrl attribute setup
    
    # DecomposeMatrix Nodes
    coverDM = cmds.createNode('decomposeMatrix', n=f'{pagePfx}_coverDM')    
    
    # RemapValue Nodes
    
    coverRotRM = cmds.createNode('remapValue', n=f'{pagePfx}_coverRotRM')
    mainRM = cmds.createNode('remapValue', n=f'{pagePfx}_curvatureRM')
    boundRM = cmds.createNode('remapValue', n=f'{pagePfx}_boundRM')
    
    # FloatMath Nodes
    boundMaxRevFM = cmds.createNode('floatMath', n=f'{pagePfx}_boundMaxRevFM')
    boundRotWeightFM = cmds.createNode('floatMath', n=f'{pagePfx}_boundRotWeightFM')
    boundMainWeightFM = cmds.createNode('floatMath', n=f'{pagePfx}_boundMainWeightFM')
    boundSumFM = cmds.createNode('floatMath', n=f'{pagePfx}_boundSumFM')
    
    curvRotWeightFM = cmds.createNode('floatMath', n=f'{pagePfx}_curvRotWeightFM')
    curvMainWeightFM = cmds.createNode('floatMath', n=f'{pagePfx}_curvMainWeightFM')
    curvSumFM = cmds.createNode('floatMath', n=f'{pagePfx}_curvSumFM')
    
    # crvSum = cmds.createNode('plusMinusAverage', n=f'{pagePfx}_curvature_sum')# need to fix
    
    # MultiplyDivide Nodes
    crvMult = cmds.createNode('multiplyDivide', n=f'{pagePfx}_curvature_multDiv')
    
    # setAttr
    cmds.setAttr(f'{mainRM}.inputMax', -1*width)
    cmds.setAttr(f'{mainRM}.inputMin', 0)
    cmds.setAttr(f'{mainRM}.outputMax', 180)
    cmds.setAttr(f'{mainRM}.outputMin', 0)
    
    cmds.setAttr(f'{boundRM}.outputMin', 0)
    cmds.setAttr(f'{boundRM}.outputMax', -2)
    cmds.setAttr(f'{boundRM}.inputMin', 0)
    cmds.setAttr(f'{boundRM}.inputMax', 10)
    
    cmds.setAttr(f'{coverRotRM}.inputMax', 90)
    
    cmds.setAttr(f'{boundMaxRevFM}.floatB', -1)
    
    cmds.setAttr(f'{boundMaxRevFM}.operation', 2)
    cmds.setAttr(f'{boundRotWeightFM}.operation', 2)
    cmds.setAttr(f'{boundMainWeightFM}.operation', 2)
    cmds.setAttr(f'{curvRotWeightFM}.operation', 2)
    cmds.setAttr(f'{curvMainWeightFM}.operation', 2)
    
    
    
    # connectAttr
    cmds.connectAttr(f'{locatorParent}.dagLocalMatrix', f'{coverDM}.inputMatrix')
    cmds.connectAttr(f'{coverDM}.outputRotateZ', f'{coverRotRM}.inputValue')
    

    cmds.connectAttr(f'{mainCtrl}.boundMax', f'{boundMaxRevFM}.floatA')
    cmds.connectAttr(f'{boundMaxRevFM}.outFloat', f'{boundRotWeightFM}.floatA')
    cmds.connectAttr(f'{coverRotRM}.outValue', f'{boundRotWeightFM}.floatB')
    cmds.connectAttr(f'{boundRotWeightFM}.outFloat', f'{boundMainWeightFM}.floatA')
    cmds.connectAttr(f'{mainCtrl}.bendFollow', f'{boundMainWeightFM}.floatB')
    cmds.connectAttr(f'{boundRM}.outValue', f'{boundSumFM}.floatA')
    cmds.connectAttr(f'{boundMainWeightFM}.outFloat', f'{boundSumFM}.floatB')
    cmds.connectAttr(f'{mainCtrl}.bound', f'{boundRM}.inputValue')
    
    cmds.connectAttr(f'{mainCtrl}.curvatureMax', f'{curvRotWeightFM}.floatA')
    cmds.connectAttr(f'{coverRotRM}.outValue', f'{curvRotWeightFM}.floatB')

    cmds.connectAttr(f'{mainCtrl}.bendFollow', f'{curvMainWeightFM}.floatA')
    cmds.connectAttr(f'{curvRotWeightFM}.outFloat', f'{curvMainWeightFM}.floatB')
    
    cmds.connectAttr(f'{mainRM}.outValue', f'{curvSumFM}.floatA')
    cmds.connectAttr(f'{curvMainWeightFM}.outFloat', f'{curvSumFM}.floatB')

    cmds.connectAttr(f'{curvSumFM}.outFloat', f'{crvMult}.i2x')
    cmds.connectAttr(f'{curvSumFM}.outFloat', f'{crvMult}.i2y')
    cmds.connectAttr(f'{curvSumFM}.outFloat', f'{crvMult}.i2z')

    
    
    # cmds.connectAttr(f'{locatorParent}.dagLocalMatrix',f'{coverDM}.inputMatrix')
    # cmds.connectAttr(f'{coverDM}.orz',f'{coverRotRM}.inputValue')

    cmds.connectAttr(f'{mainCtrl}.tx', f'{mainRM}.inputValue')
    
    
    
    
    
    
    
    # cmds.connectAttr(f'{mainRM}.outValue', f'{crvSum}.i1d[0]')
    # cmds.connectAttr(f'{crvSum}.outValue', f'{crvMult}.i2x')
    # cmds.connectAttr(f'{crvSum}.outValue', f'{crvMult}.i2y')
    # cmds.connectAttr(f'{crvSum}.outValue', f'{crvMult}.i2z')

    for i in range(2):
        remap_node = cmds.createNode('remapValue', n=f'{pagePfx}_curvature_remap_{i}')
        if i == 0:
            cmds.setAttr(f'{remap_node}.inputMax', height/-2)
            cmds.setAttr(f'{remap_node}.inputMin', height/2)
            cmds.connectAttr(f'{remap_node}.outValue', f'{crvMult}.i1x')
            # cmds.connectAttr(f'{mainRM}.outValue', f'{crvMult}.i2x')
            cmds.connectAttr(f'{crvMult}.ox', f'{bendNodeLis[2]}.curvature')
        else:
            cmds.setAttr(f'{remap_node}.inputMax', height/2)
            cmds.setAttr(f'{remap_node}.inputMin', height/-2)
            cmds.connectAttr(f'{remap_node}.outValue', f'{crvMult}.i1y')                
            # cmds.connectAttr(f'{mainRM}.outValue', f'{crvMult}.i2y')
            cmds.connectAttr(f'{crvMult}.oy', f'{bendNodeLis[0]}.curvature')


        cmds.setAttr(f'{remap_node}.outputMin', 0.5)
        cmds.setAttr(f'{remap_node}.outputMax', 1.5)
        cmds.connectAttr(f'{mainCtrl}.tz', f'{remap_node}.inputValue')
    # cmds.connectAttr(f'{mainRM}.outValue', f'{crvMult}.i1z')
    cmds.connectAttr(f'{crvMult}.oz', f'{bendNodeLis[1]}.curvature')
    cmds.setAttr(f'{crvMult}.i1z', 1)
    
    
    
    

    for bendNode in bendNodeLis:
        cmds.connectAttr(f'{boundSumFM}.outFloat', f'{bendNode}.lowBound')
        handle = bendNode.replace('bend', 'bendHandle')
        cmds.connectAttr(f'{mainCtrl}.height', f'{handle}.sx' )
    
    # Part 2: Others
    
    cmds.parentConstraint(rotCtrl, curveCtrlGrp)
    cmds.orientConstraint(rotCtrl,upLocGrp)
    
    upLocTzMD = cmds.createNode('multiplyDivide', n=f'{pagePfx}_upLocTzMD')
    cmds.connectAttr(f'{mainCtrl}.tz',f'{upLocTzMD}.i1z')
    cmds.connectAttr(f'{upLocTzMD}.oz', f'{upLocGrp}.tz')

    upLocRemap_node = cmds.createNode('remapValue', n=f'{pagePfx}_upLoc_remap')
    cmds.setAttr(f'{upLocRemap_node}.inputMax', -0.5*width)
    cmds.setAttr(f'{upLocRemap_node}.inputMin', 0)
    cmds.setAttr(f'{upLocRemap_node}.outputMax', -1)
    cmds.setAttr(f'{upLocRemap_node}.outputMin', 0)
    
    cmds.connectAttr(f'{mainCtrl}.tx',f'{upLocRemap_node}.inputValue')
    cmds.connectAttr(f'{upLocRemap_node}.outValue',f'{upLocTzMD}.i2z')

    
    
    mainBM = cmds.createNode('blendMatrix', n=f'{pagePfx}_mainBM' )
    cmds.setAttr(f'{mainBM}.target[0].scaleWeight', 0)
    cmds.setAttr(f'{mainBM}.target[0].translateWeight', 0)
    cmds.setAttr(f'{mainBM}.target[0].shearWeight', 0)
    
    rotCtrlGrp = cmds.listRelatives(rotCtrl,p=1)[0]
    cmds.connectAttr(f'{locatorParent}.worldMatrix[0]', f'{mainBM}.target[0].targetMatrix')
    cmds.connectAttr(f'{jointParent}.worldMatrix[0]', f'{mainBM}.inputMatrix')
    cmds.connectAttr(f'{mainBM}.outputMatrix', f'{rotCtrlGrp}.offsetParentMatrix')
    cmds.connectAttr(f'{mainCtrl}.rotateFollow', f'{mainBM}.target[0].rotateWeight')
    
    mainDM = cmds.createNode('decomposeMatrix', n=f'{pagePfx}_mainDM')
    cmds.connectAttr(f'{mainBM}.outputMatrix', f'{mainDM}.inputMatrix')
    cmds.connectAttr(f'{mainDM}.outputScale', f'{jntGrp}.scale')
    cmds.connectAttr(f'{mainDM}.outputScale', f'{curveCtrlGrp}.scale')
    cmds.connectAttr(f'{mainDM}.outputScale', f'{upLocGrp}.scale')
 
def groupObjects(pagePfx, pageName, ikHandleLis, ikCrvLis, bendHandleLis, jntLis, upLocLis, rotCtrl):
    ikHandleGrp = cmds.group(ikHandleLis, n=f'{pagePfx}_ikHandle_grp',w=1)
    ikCrvGrp = cmds.group(ikCrvLis, n=f'{pagePfx}_ikCrv_grp')
    bendHandleGrp = cmds.group(bendHandleLis, n=f'{pagePfx}_bendHandle_grp')
    jntGrp = cmds.group(jntLis, n=f'{pagePfx}_jnt_grp')
    curveCtrlGrp = cmds.group(ikCrvGrp, bendHandleGrp, n=f'{pagePfx}_crv_ctrl_grp')
    upLocGrp = cmds.group(upLocLis, n=f'{pagePfx}_upLoc_grp')

    ctrlGrp = cmds.group(pageName, ikHandleGrp, curveCtrlGrp, jntGrp, upLocGrp, n=f'{pagePfx}_ctrl_grp')
    cmds.xform([ikHandleGrp, ikCrvGrp, bendHandleGrp, jntGrp, curveCtrlGrp, upLocGrp,ctrlGrp],piv=[0,0,0], absolute=True)
    rotCtrlGrp = cmds.listRelatives( rotCtrl, p=1 )[0]
    pageMainGrp = cmds.group([ctrlGrp,rotCtrlGrp],n=f'{pagePfx}_main_grp')
    cmds.xform(pageMainGrp,piv=[0,0,0], absolute=True)
    cmds.matchTransform(pageName, jointParent)
    cmds.makeIdentity(pageName, apply=1)
    cmds.parent(pageMainGrp, systemParent)
    
    
    return curveCtrlGrp, ctrlGrp, upLocGrp, jntGrp

def single_page_fix(pagePfx):

    cmds.disconnectAttr(f'{pagePfx}_curvatureRM.outValue', f'{pagePfx}_curvSumFM.floatA')
    cmds.disconnectAttr(f'{pagePfx}_boundRM.outValue', f'{pagePfx}_boundSumFM.floatA')

    cmds.delete(f'{pagePfx}_curvSumFM')
    cmds.delete(f'{pagePfx}_boundSumFM')

    cmds.connectAttr(f'{pagePfx}_boundRM.outValue',f'{pagePfx}_bend_1.lowBound')
    cmds.connectAttr(f'{pagePfx}_boundRM.outValue',f'{pagePfx}_bend_2.lowBound')
    cmds.connectAttr(f'{pagePfx}_boundRM.outValue',f'{pagePfx}_bend_3.lowBound')

    cmds.connectAttr(f'{pagePfx}_curvatureRM.outValue', f'{pagePfx}_curvature_multDiv.i2x' )
    cmds.connectAttr(f'{pagePfx}_curvatureRM.outValue', f'{pagePfx}_curvature_multDiv.i2y' )
    cmds.connectAttr(f'{pagePfx}_curvatureRM.outValue', f'{pagePfx}_curvature_multDiv.i2z' )



    cmds.setAttr(f'{pagePfx}_main_ctrl_offset.tx', 18)

    cmds.setAttr(f'{pagePfx}_curvatureRM.inputMin', -18)
    cmds.setAttr(f'{pagePfx}_curvatureRM.inputMax', 18)

    cmds.setAttr(f'{pagePfx}_curvatureRM.outputMin', -180)
    cmds.setAttr(f'{pagePfx}_curvatureRM.outputMax', 180)

    cmds.transformLimits(f'{pagePfx}_main_ctrl', tx=[-18, 18])

    mainTXRevFM = cmds.createNode('floatMath', n=f'{pagePfx}_mainTXRev_FM')

    mainTXPositive_CON = cmds.createNode('condition', n=f'{pagePfx}_mainTXPositive_CON' )

    upLoc_TY_remap_1 = cmds.createNode('remapValue', n=f'{pagePfx}_upLoc_TY_remap_1' )
    upLoc_TY_remap_2 = cmds.createNode('remapValue', n=f'{pagePfx}_upLoc_TY_remap_2' )

    cmds.setAttr(f'{mainTXRevFM}.floatB', -1)
    cmds.setAttr(f'{mainTXRevFM}.operation', 2)

    cmds.setAttr(f'{upLoc_TY_remap_1}.inputMax', -15)
    cmds.setAttr(f'{upLoc_TY_remap_1}.outputMax', 36)

    cmds.setAttr(f'{upLoc_TY_remap_2}.inputMax', 36)
    cmds.setAttr(f'{upLoc_TY_remap_2}.outputMin', 10)
    cmds.setAttr(f'{upLoc_TY_remap_2}.outputMax', -15)


    cmds.connectAttr(f'{pagePfx}_main_ctrl.tx',f'{mainTXRevFM}.floatA')
    cmds.connectAttr(f'{mainTXRevFM}.outFloat', f'{mainTXPositive_CON}.colorIfTrue.colorIfTrueR')
    cmds.connectAttr(f'{pagePfx}_main_ctrl.tx', f'{mainTXPositive_CON}.colorIfFalse.colorIfFalseR')

    cmds.connectAttr(f'{pagePfx}_mainTXPositive_CON.outColorR', f'{pagePfx}_upLoc_remap.inputValue',f=1)
    cmds.connectAttr(f'{pagePfx}_main_ctrl.tx', f'{upLoc_TY_remap_1}.inputValue')

    cmds.connectAttr(f'{upLoc_TY_remap_1}.outValue', f'{upLoc_TY_remap_2}.inputValue')
    cmds.connectAttr(f'{upLoc_TY_remap_1}.outValue',f'{pagePfx}_upLoc_0.tx')
    cmds.connectAttr(f'{upLoc_TY_remap_1}.outValue',f'{pagePfx}_upLoc_1.tx')
    cmds.connectAttr(f'{upLoc_TY_remap_1}.outValue',f'{pagePfx}_upLoc_2.tx')
    cmds.connectAttr(f'{upLoc_TY_remap_2}.outValue',f'{pagePfx}_upLoc_0.ty')
    cmds.connectAttr(f'{upLoc_TY_remap_2}.outValue',f'{pagePfx}_upLoc_1.ty')
    cmds.connectAttr(f'{upLoc_TY_remap_2}.outValue',f'{pagePfx}_upLoc_2.ty')


def run(pagePfx, width = 36, height = 28):
    main, rot = buildCtrl(pagePfx, width=36, height=28)
    pageName = createPageGeo(pagePfx, width=36, height=28)
    ikHandleLis, ikCrvLis, bendLis, bendHandleLis, jntLis, upLocLis = placeJoints( pagePfx, pageName, width=36, height=28)
    curveCtrlGrp, ctrlGrp, upLocGrp, jntGrp = groupObjects(pagePfx,pageName, ikHandleLis, ikCrvLis, bendHandleLis, jntLis, upLocLis, rot)
    connectAttr(pagePfx, bendLis, main, rot, bendHandleLis, curveCtrlGrp, ctrlGrp, upLocGrp, jntGrp, width=36, height=28)
    single_page_fix(pagePfx)
    
# run("Page_2")