'''
  1.  manually place all joint chains and 
      rename them to the {geo_name}_jnt_{i}
  2.  select all root hair joints
  3.  script start - rebuild joint chain as iKSpline
  4.  take IK spline's curves, duplicate as start curves,
      and connect them to hair base(needs to be clean mesh
      for easy attachment, otherwise it might get attached
      to backfaces), make sure they're renamed properly
  5.  Start simulating to get the rest curves, duplicate, 
      and adjust the curves if needed
  6.  Setup start curve and rest curve properly, set the,
      parameters for hair system and follicles properly
'''

import maya.cmds as cmds
import maya.mel as mel


'''
Returns the newly created hairSystemShape
'''
def latestHairSystemShape():
            hairSystemShape_lis = cmds.ls('hairSystemShape*', shapes=1)
            if hairSystemShape_lis:
                def sortHairSystem(e):
                    return int(e.replace('hairSystemShape',''))
                hairSystemShape_lis.sort(key = sortHairSystem)
                return hairSystemShape_lis[-1]
            cmds.warning('No hairSystem found in scene.')
            return None
def buildIKSpline(hair_style):
    sl_lis = cmds.ls(sl=1)
    ikHandle_lis = []
    ikCrv_lis = []
    startCrv_lis = []
    for sl in sl_lis:
        end_jnt = sl.replace('_jnt_1', '_jnt_6')
        ikHandle,_, ikCrv = cmds.ikHandle(sj = sl, ee= end_jnt, rootOnCurve=1, pcv=1, ccv=1, n=f'{sl.replace("_jnt_1", "_ikHandle")}', scv=0, sol='ikSplineSolver' )
        ikCrv = cmds.rename(ikCrv, f"{sl.replace('_jnt_1', '_ikCurve')}")
        startCrv = cmds.duplicate(ikCrv, n = ikCrv.replace('_ikCurve', '_startCurve'))[0]
        
        ikHandle_lis.append(ikHandle)
        ikCrv_lis.append(ikCrv)
        startCrv_lis.append(startCrv)
        
    cmds.group(ikHandle_lis,w=1,n=f'{hair_style}_hair_ikHandle_grp')
    cmds.group(ikCrv_lis,w=1,n=f'{hair_style}_hair_ikCurve_grp')   
    cmds.group(startCrv_lis,w=1,n=f'{hair_style}_hair_startCurve_grp')   

# start attaching follicles here
def buildFollicle(startCrv_lis, hair_attach_proxy):
    cmds.select(startCrv_lis ,replace=1)
    cmds.select(hair_attach_proxy, add=1)

    mel.eval('makeCurvesDynamic 2 { "1", "0", "1", "1", "0"};')
    outputCrv_lis =[]
    for i in range(len(startCrv_lis)):
        outputCrv = cmds.rename(f'curve{i+1}', startCrv_lis[i].replace("start", 'output'))
        outputCrv_lis.append(outputCrv)
        flc = cmds.rename(f'follicle{i+1}', startCrv_lis[i].replace("_start_", '_').replace("Curve", "flc"))
        cmds.setAttr(f"{flc}.restPose", 1)
        cmds.setAttr(f"{flc}.startDirection", 1)
        cmds.setAttr(f"{flc}.pointLock", 1)
        # # create blendshape
        cmds.blendShape(outputCrv, ikCrv_lis[i], w=[(0,1)])
    
    hairSystemShape = latestHairSystemShape()
    if not hairSystemShape:
        return
    
    cmds.setAttr(f'{hairSystemShape}.stiffnessScale[0].stiffnessScale_FloatValue', 0.5)
    cmds.setAttr(f'{hairSystemShape}.attractionScale[1].attractionScale_FloatValue', 0.1)
    cmds.setAttr(f'{hairSystemShape}.attractionScale[2].attractionScale_Position', 0.5)
    cmds.setAttr(f'{hairSystemShape}.attractionScale[2].attractionScale_FloatValue', 0.3)
    cmds.setAttr(f'{hairSystemShape}.attractionScale[2].attractionScale_Interp', 3)

    cmds.setAttr('hairSystemShape2.startCurveAttract', 1)

    # worldUpObject = 'relaxed_hair_TwistStartLoc'
    # worldUpObject2 = 'relaxed_hair_TwistEndLoc'

    # for ikHandle in ikHandle_lis:
    #     cmds.setAttr(f'{ikHandle}.dTwistControlEnable', 1)
    #     cmds.setAttr(f'{ikHandle}.dWorldUpType', 2)
    #     cmds.setAttr(f'{ikHandle}.dWorldUpAxis', 1)
    #     cmds.connectAttr(f'{worldUpObject}.worldMatrix[0]', f'{ikHandle}.dWorldUpMatrix')
    #     cmds.connectAttr(f'{worldUpObject2}.worldMatrix[0]', f'{ikHandle}.dWorldUpMatrixEnd')









