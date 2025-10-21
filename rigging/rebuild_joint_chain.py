import maya.cmds as cmds

def build_joint_on_curve_point(curve_name, name='joint', parameter = 0):
    pos = cmds.pointOnCurve(curve_name, pr= parameter, p=1, turnOnPercentage=1)
    return cmds.joint(n=name, position = pos)
    
def aim_child_jnt(parent_jnt, child_jnt):
    pos = cmds.xform(child_jnt, q=1, t=1, worldSpace=1)
    temp_loc = cmds.spaceLocator(name='temp_loc')
    cmds.matchTransform(temp_loc, child_jnt)
    temp_constraint = cmds.aimConstraint(temp_loc, parent_jnt,aim=[1,0,0], mo=0,wut='scene' )
    cmds.matchTransform(child_jnt,temp_loc)
    cmds.delete(temp_constraint, temp_loc)
    cmds.makeIdentity(parent_jnt, r=1,a=1)
    
    
def rebuild_joint_chain(rebuild_jnt_amount = 6, keepOriginal=0):
    sl_lis = cmds.ls(sl=1, type='joint')
    print(sl_lis)
    root_jnt = ''
    end_jnt = ''
    decendent_0 = cmds.listRelatives(sl_lis[0], ad=1)
    decendent_1 = cmds.listRelatives(sl_lis[1], ad=1)
    # between two joints that are parent and decendent
    if (len(sl_lis)!=2):
        cmds.warning('must select one parent and one decendent joint')
        return
    if decendent_1 and sl_lis[0] in decendent_1:
        root_jnt = sl_lis[1]
        end_jnt = sl_lis[0]
    elif decendent_0 and sl_lis[1] in decendent_0:
        root_jnt = sl_lis[0]
        end_jnt = sl_lis[1]
    else:
        cmds.warning('Selected joints are not parent and decendents')
        return
    temp_ikHandle,_, crv = cmds.ikHandle(sj = root_jnt, ee= end_jnt, rootOnCurve=1, pcv=1, ccv=1, n='tempIkHandle', scv=0, sol='ikSplineSolver' )
    cmds.delete(temp_ikHandle)
    step = 1/(rebuild_jnt_amount-1)
    percent = 0
    jnt_lis = []
    # jnt_pfx = '_'.join(root_jnt.split('_')[:-1])
    for i in range(1, rebuild_jnt_amount+1):
        jnt_lis.append(build_joint_on_curve_point(crv, name=f'rebuilt_{root_jnt}_{i}', parameter = percent ))
        percent=percent+step
    
    for i in range(len(jnt_lis)-1):
        aim_child_jnt(jnt_lis[i],jnt_lis[i+1])
    cmds.makeIdentity(jnt_lis[-1], r=1,jo=1,a=1)
    cmds.delete(crv)
    if not keepOriginal:
         cmds.delete(root_jnt,end_jnt)

sl_lis = cmds.ls(sl=1)
for sl in sl_lis:
    end_jnt = cmds.listRelatives(sl, children=1)[0]
    while True:
        try:
            end_jnt = cmds.listRelatives(end_jnt, children=1)[0]
        except:
            break
    cmds.select(sl,end_jnt, replace=1)
    rebuild_joint_chain()