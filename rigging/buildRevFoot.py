import maya.cmds as cmds
import maya.api.OpenMaya as om

import sys
# on windows
sys.path.append("E:/Rigging/CW_Maya_Rigging_Tools")
# on mac
# sys.path.append("/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools")

import cwInitTools as cw

def create_single_chain_IK():
    rootJnt = cmds.ls(sl=True, type="joint")[0]
    currJnt = rootJnt
    ikHandleLis = []
    childCnt = len(cmds.listRelatives(ad=True, type="joint"))
    for i in range(childCnt):
        currPfx = cw.get_jnt_pfx(currJnt)
        try:
            cmds.select(currJnt)
            childJnt = cmds.listRelatives(children=True, type="joint")[0]
        except:
            break
        ikHandleLis.append(cmds.ikHandle(n=currPfx+"_ikHandle", startJoint=currJnt,endEffector=childJnt, solver = 'ikSCsolver'))
        currJnt = childJnt
    return ikHandleLis

    
def create_rev_foot_jnts(d = -17.5):
    rootJnt = cmds.ls(sl=True, type="joint")[0]
    revEndJnt = cmds.duplicate(rootJnt, rr=1, rc=True)[0]
    cmds.parent(revEndJnt, world=True)
    # revEndJnt
    revSecondJnt = revEndJnt
    while(True):
        try:
            revSecondJnt = cmds.listRelatives(revSecondJnt, children=1, type="joint")[0]
        except:
            break
    print(revSecondJnt)
    revFirstJnt = cmds.duplicate(revSecondJnt,rr=1, rc=True)[0]
    
    cmds.parent(revFirstJnt,revSecondJnt)
    cmds.select(revFirstJnt)
    cmds.setAttr(revFirstJnt+".translateX",d)
    cmds.reroot(revFirstJnt)
    jntLis = cmds.listRelatives(revFirstJnt, ad=1, type="joint")
    cmds.rename(revFirstJnt, cw.get_jnt_pfx(revFirstJnt)[0]+"_heel_rev_jnt")

    for jnt in jntLis:
        cmds.rename(jnt, cw.get_jnt_pfx(jnt)+"_rev_jnt")
    
    
def add_foot_ctrl_attr():
    footCtrl = cmds.ls(sl=1)[0]
    
    cmds.addAttr(footCtrl, longName='Foot_Ctrl', at = "enum", en='------' )
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Foot_Ctrl',channelBox=True)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Foot_Ctrl',lock=False)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Foot_Ctrl',keyable=True)
    
    cmds.addAttr(footCtrl, longName='Bank',at='float')
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Bank',channelBox=True)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Bank',lock=False)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Bank',keyable=True)

    cmds.addAttr(footCtrl, longName='Roll',at='float', max=10, min=-10)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Roll',channelBox=True)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Roll',lock=False)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Roll',keyable=True)
    
    cmds.addAttr(footCtrl, longName='Heel_Twist',at='float')
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Heel_Twist',channelBox=True)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Heel_Twist',lock=False)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Heel_Twist',keyable=True)
    
    cmds.addAttr(footCtrl, longName='Toe_Twist',at='float')
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Toe_Twist',channelBox=True)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Toe_Twist',lock=False)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Toe_Twist',keyable=True)
    
    cmds.addAttr(footCtrl, longName='Toe_Tap',at='float')
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Toe_Tap',channelBox=True)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Toe_Tap',lock=False)
    cmds.setAttr(cmds.ls(sl=1)[0]+'.Toe_Tap',keyable=True)
    
    
def place_IK_handle():
    rootJnt = cmds.ls(sl=1)[0]
    currJnt = rootJnt
    i=0
    while(True):
        try:
            print(i)
            childJnt = cmds.listRelatives(currJnt, children=1, type='joint')[0]
            print(cw.get_jnt_pfx(childJnt)+'_ikHandle')
            cmds.parent(cw.get_jnt_pfx(childJnt)+'_ikHandle', currJnt)
            currJnt = childJnt
            i+=1
            
        except:
            print('break at: ', i)
            break

            
def create_os_ctrl_grp(footWidth = 7):
    rootJnt = cmds.ls(sl=1)[0]
    
    # match T with ikHandle
    jntGrp = cmds.group(n = rootJnt[0]+"_rev_jnt_grp", em=True)
    cmds.matchTransform(jntGrp, rootJnt[0]+"_leg_ik_ctrl")

    # match T with rootJnt
    heelOSGrp = cmds.group(n = rootJnt[0]+"_heel_os_grp", em=True)
    heelCtrlGrp = cmds.group(n = rootJnt[0]+"_heel_ctrl_grp", em=True)
    cmds.matchTransform(heelOSGrp, rootJnt)
    cmds.matchTransform(heelCtrlGrp, rootJnt)
    cmds.parent(heelCtrlGrp, heelOSGrp)
    cmds.parent(heelOSGrp, jntGrp)
    
    # match T manually
    bankOuterOsGrp = cmds.group(n = rootJnt[0]+"_foot_bank_outer_os_grp", em=True)
    bankOuterCtrlGrp = cmds.group(n = rootJnt[0]+"_foot_bank_outer_ctrl_grp", em=True)
    cmds.parent(bankOuterCtrlGrp, bankOuterOsGrp)
    cmds.matchTransform(bankOuterOsGrp, rootJnt, rot=True)

    # match T automatically
    bankInnerOsGrp = cmds.group(n = rootJnt[0]+"_foot_bank_inner_os_grp", em=True)
    bankInnerCtrlGrp = cmds.group(n = rootJnt[0]+"_foot_bank_inner_ctrl_grp", em=True)
    cmds.parent(bankInnerCtrlGrp, bankInnerOsGrp)
    cmds.matchTransform(bankInnerOsGrp, bankOuterCtrlGrp)
    cmds.parent(bankInnerOsGrp, bankOuterCtrlGrp)
    cmds.parent(bankOuterOsGrp, heelCtrlGrp)
    cmds.setAttr(bankInnerOsGrp+".translateZ", footWidth)
    
def setup_toeTap_grp():
    pfx = cmds.ls(sl=1)[0][0]
    ttOsGrp = cmds.group(n=pfx+"_toe_tap_os_grp", em=1, w=1)
    ttCtrlGrp = cmds.group(n=pfx+"_toe_tap_ctrl_grp", em=1, w=1)
    cmds.parent(ttCtrlGrp, ttOsGrp)
    cmds.matchTransform(ttOsGrp, pfx+"_toe_rev_jnt")
    cmds.parent(ttOsGrp, pfx+"_toe_end_rev_jnt")
    cmds.parent(pfx+"_toe_ikHandle", ttCtrlGrp)
    
    
    
    
def connect_foot_attr(revBank=False):
    rootJnt = cmds.ls(sl=1)[0]
    pfx = rootJnt[0]
    # bank control
    bankCondNode = cmds.createNode('condition', n = pfx +'_bank_condition')
    cmds.setAttr(bankCondNode+".op", 2)
    cmds.setAttr(bankCondNode+".cf", 0,0,0)
    cmds.connectAttr(pfx + "_leg_ik_ctrl.Bank" , bankCondNode+".ft" )
    cmds.connectAttr(pfx + "_leg_ik_ctrl.Bank" , bankCondNode+".cfr" )
    cmds.connectAttr(pfx + "_leg_ik_ctrl.Bank", bankCondNode+".ctg" )
    
    if revBank == True:
        cmds.connectAttr( bankCondNode + ".ocg" , pfx + "_foot_bank_outer_ctrl_grp.rotateX")
        cmds.connectAttr( bankCondNode + ".ocr" , pfx + "_foot_bank_inner_ctrl_grp.rotateX")
        
    else:  
        cmds.connectAttr( bankCondNode + ".ocr" , pfx + "_foot_bank_outer_ctrl_grp.rotateX")
        cmds.connectAttr( bankCondNode + ".ocg" , pfx + "_foot_bank_inner_ctrl_grp.rotateX")
        
    
    # Heel_Twist
    cmds.connectAttr(pfx + "_leg_ik_ctrl.Heel_Twist", pfx+"_heel_ctrl_grp.rotateY")
    
    # Toe_Twist
    cmds.connectAttr(pfx + "_leg_ik_ctrl.Toe_Twist", pfx+"_toe_end_rev_jnt.rotateY")
    
    # Toe_Tap
    cmds.connectAttr(pfx + "_leg_ik_ctrl.Toe_Tap", pfx+"_toe_tap_ctrl_grp.rotateZ")


# Step 1: create rev foot jnts and single chain IK

# create_rev_foot_jnts()
# create_single_chain_IK()

# Step 2: setup hierarchy

# place_IK_handle()
# setup_toeTap_grp()
# ** remember to manually place the bank grp
# create_os_ctrl_grp()


# Step 3: add and connect foot control attributes
   
# add_foot_ctrl_attr()
# connect_foot_attr()
