import maya.cmds as cmds
from importlib import reload
import sys
sys.path.insert(0, r"/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools")
from control import CWControlManager as ctrl
from utility import renameShapeNodes as renameSN

# 1. add locator for ikHandle Twist object up
# 2. place everything in correct place
# 3. optimize scale issue
# 4. rotation matching
# 5. blend matrix for cover open motion

systemParent = 'CustomSystem'
jointParent = 'Page_R'
locatorParent = 'Cover_R'


# build bookpage rig, by inputting the dimension of the page: width, height, width subdiv, height subdiv
# the script is going to create a plane, while assuming that the vertice of the plane is going to follow the sequential order 

def buildCtrl(width=10, height=10):
    libDir = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/control/'
    manager = ctrl(os.path.join(libDir, 'CWControlLib.json'))
    main_ctrl = manager.createShape('cube', 'main_ctrl', True)
    rot_ctrl = manager.createShape('square', 'rot_ctrl', True)
    manager.setCurveWidth(5, rot_ctrl)
    cmds.xform(rot_ctrl, s=[1,1,(height/2)+1])
    cmds.makeIdentity(rot_ctrl, apply=1)

    main_ctrl_parent = cmds.listRelatives(main_ctrl, p=1)[0]
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
    cmds.addAttr(main_ctrl, longName = 'coverRotateFollow', min=0, max=1, dv=0.5 )

    
    cmds.setAttr(f'{main_ctrl}.bound', cb=1, k=1)
    cmds.setAttr(f'{main_ctrl}.height', cb=1, k=1)
    cmds.setAttr(f'{main_ctrl}.coverRotateFollow', cb=1, k=1)

    cmds.transformLimits( main_ctrl, tx=(-width, 0), tz=(height/-2, height/2), etx=(True, True), etz=(True, True ) )
    
    return main_ctrl, rot_ctrl
    
def createPageGeo(pagePfx, height=10, width=10, subHeight=10, subWidth=10):
    pageName = cmds.polyPlane(ch=False, cuv=2, h=height, w=width, sh=subHeight, sw=subWidth, n=pagePfx+'_proxy')[0]
    cmds.xform(pageName, t=[width/2,0,0],piv=[width/-2,0,0], absolute=True)
    cmds.makeIdentity(pageName, apply=1)
    # print(plane_geo)
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
                # jntLis.append(jnt)
        print(f'{pagePfx}_jnt_{i+1}_0')
        ikHandle, _, ikCrv = cmds.ikHandle(sj=f'{pagePfx}_jnt_{i+1}_0', ee=f'{pagePfx}_jnt_{i+1}_{len(vert_lis[0])-1}', ccv=1, sol='ikSplineSolver', pcv=0, scv=0, n=f'{pagePfx}_ikHandle_{i+1}')
        
        
        cmds.setAttr(f'{ikHandle}.dTwistControlEnable', 1)
        cmds.setAttr(f'{ikHandle}.dWorldUpType', 1)
        cmds.connectAttr(f'{upLoc}.worldMatrix[0]', f'{ikHandle}.dWorldUpMatrix')

        
        # ikCrv = cmds.ikHandle(q=1, curve=1).split('|')[1]
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
    mainRemap_node = cmds.createNode('remapValue', n=f'{pagePfx}_curvature_remap')
    cmds.setAttr(f'{mainRemap_node}.inputMax', -1*width)
    cmds.setAttr(f'{mainRemap_node}.inputMin', 0)
    cmds.setAttr(f'{mainRemap_node}.outputMax', 180)
    cmds.setAttr(f'{mainRemap_node}.outputMin', 0)
    
    cmds.connectAttr(f'{mainCtrl}.tx', f'{mainRemap_node}.inputValue')
    
    crvMult = cmds.createNode('multiplyDivide', n=f'{pagePfx}_curvature_multDiv')
    
    for i in range(2):
        remap_node = cmds.createNode('remapValue', n=f'{pagePfx}_curvature_remap_{i}')
        if i == 0:
            cmds.setAttr(f'{remap_node}.inputMax', height/-2)
            cmds.setAttr(f'{remap_node}.inputMin', height/2)
            cmds.connectAttr(f'{remap_node}.outValue', f'{crvMult}.i1x')
            cmds.connectAttr(f'{mainRemap_node}.outValue', f'{crvMult}.i2x')
            cmds.connectAttr(f'{crvMult}.ox', f'{bendNodeLis[2]}.curvature')
        else:
            cmds.setAttr(f'{remap_node}.inputMax', height/2)
            cmds.setAttr(f'{remap_node}.inputMin', height/-2)
            cmds.connectAttr(f'{remap_node}.outValue', f'{crvMult}.i1y')                
            cmds.connectAttr(f'{mainRemap_node}.outValue', f'{crvMult}.i2y')
            cmds.connectAttr(f'{crvMult}.oy', f'{bendNodeLis[0]}.curvature')


        cmds.setAttr(f'{remap_node}.outputMin', 0.5)
        cmds.setAttr(f'{remap_node}.outputMax', 1.5)
        cmds.connectAttr(f'{mainCtrl}.tz', f'{remap_node}.inputValue')
    cmds.connectAttr(f'{mainRemap_node}.outValue', f'{crvMult}.i1z')
    cmds.connectAttr(f'{crvMult}.oz', f'{bendNodeLis[1]}.curvature')
    
    boundRemap_node = cmds.createNode('remapValue', n=f'{pagePfx}_bound_remap')
    cmds.setAttr(f'{boundRemap_node}.outputMin', 0)
    cmds.setAttr(f'{boundRemap_node}.outputMax', -2)
    cmds.setAttr(f'{boundRemap_node}.inputMin', 0)
    cmds.setAttr(f'{boundRemap_node}.inputMax', 10)
    
    cmds.connectAttr(f'{mainCtrl}.bound', f'{boundRemap_node}.inputValue')

    for bendNode in bendNodeLis:
        cmds.connectAttr(f'{boundRemap_node}.outValue', f'{bendNode}.lowBound')
        handle = bendNode.replace('bend', 'bendHandle')
        cmds.connectAttr(f'{mainCtrl}.height', f'{handle}.sx' )
    
    cmds.parentConstraint(rotCtrl, curveCtrlGrp)
    cmds.parentConstraint(rotCtrl,upLocGrp)
    mainBM = cmds.createNode('blendMatrix', n=f'{pagePfx}_mainBM' )
    cmds.setAttr(f'{mainBM}.target[0].scaleWeight', 0)
    cmds.setAttr(f'{mainBM}.target[0].translateWeight', 0)
    cmds.setAttr(f'{mainBM}.target[0].shearWeight', 0)
    
    rotCtrlGrp = cmds.listRelatives(rotCtrl,p=1)[0]
    cmds.connectAttr(f'{locatorParent}.worldMatrix[0]', f'{mainBM}.target[0].targetMatrix')
    cmds.connectAttr(f'{jointParent}.worldMatrix[0]', f'{mainBM}.inputMatrix')
    cmds.connectAttr(f'{mainBM}.outputMatrix', f'{rotCtrlGrp}.offsetParentMatrix')
    cmds.connectAttr(f'{mainCtrl}.coverRotateFollow', f'{mainBM}.target[0].rotateWeight')
    
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


pagePfx = jointParent

main, rot = buildCtrl(width=36, height=28)
# print(jointParent)
pageName = createPageGeo(jointParent, width=36, height=28)
ikHandleLis, ikCrvLis, bendLis, bendHandleLis, jntLis, upLocLis = placeJoints( pagePfx, pageName, width=36, height=28)
curveCtrlGrp, ctrlGrp, upLocGrp, jntGrp = groupObjects(pagePfx,pageName, ikHandleLis, ikCrvLis, bendHandleLis, jntLis, upLocLis, rot)
connectAttr(pagePfx, bendLis, main, rot, bendHandleLis, curveCtrlGrp, ctrlGrp, upLocGrp, jntGrp, width=36, height=28)