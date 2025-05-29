import maya.cmds as cmds
from maya import OpenMaya

def getUParam( pnt = [], crv = None):

    point = OpenMaya.MPoint(pnt[0],pnt[1],pnt[2])
    curveFn = OpenMaya.MFnNurbsCurve(getDagPath(crv))
    paramUtill=OpenMaya.MScriptUtil()
    paramPtr=paramUtill.asDoublePtr()
    isOnCurve = curveFn.isPointOnCurve(point)
    if isOnCurve == True:
        
        curveFn.getParamAtPoint(point , paramPtr,0.001,OpenMaya.MSpace.kObject )
    else :
        point = curveFn.closestPoint(point,paramPtr,0.001,OpenMaya.MSpace.kObject)
        curveFn.getParamAtPoint(point , paramPtr,0.001,OpenMaya.MSpace.kObject )
    
    param = paramUtill.getDouble(paramPtr)  
    return param

def getDagPath( objectName):
    
    if isinstance(objectName, list)==True:
        oNodeList=[]
        for o in objectName:
            selectionList = OpenMaya.MSelectionList()
            selectionList.add(o)
            oNode = OpenMaya.MDagPath()
            selectionList.getDagPath(0, oNode)
            oNodeList.append(oNode)
        return oNodeList
    else:
        selectionList = OpenMaya.MSelectionList()
        selectionList.add(objectName)
        oNode = OpenMaya.MDagPath()
        selectionList.getDagPath(0, oNode)
        return oNode
        
        
def build_jnt():
    cmds.select(cmds.polyListComponentConversion(tv=1))
    vtxLis = cmds.ls(sl=1, fl=1)

    for vtx in vtxLis:
        cmds.select(cl=1)
        newJnt = cmds.joint()
        pos = cmds.xform(vtx, q=1 ,ws=1, t=1)[0:3]
        cmds.xform(newJnt, ws=1, t=pos)
        cmds.select(cl=1)
        cJnt = cmds.joint()
        posC = cmds.xform('l_eye_back_loc', q=1, ws=1, t=1)[0:3]
        cmds.xform(cJnt, ws=1, t=posC)
        
        cmds.parent(newJnt, cJnt)

def build_loc():
    jntLis = cmds.ls(sl=1)

    for jnt in jntLis:
        loc = cmds.spaceLocator()[0]
        pos = cmds.xform(jnt, q = 1, ws = 1, t =1)
        cmds.xform(loc, ws =1, t = pos)
        parent = cmds.listRelatives(jnt, p =1)[0]
        
        cmds.aimConstraint( loc, parent, mo =1, weight =1, aimVector =(1,0,0), upVector=(0,1,0), worldUpType="object", worldUpObject ='r_eye_up_loc' )

def attach_crv():
    loc_lis = cmds.ls(sl = 1)
    crv = 'l_eye_mid_crvShape'

    for loc in loc_lis:
        pos = cmds.xform(loc, q = 1, ws = 1, t = 1)
        u = getUParam(pos, crv)
        print(u)
        name = loc.replace('_loc', '_pci')
        pci = cmds.createNode('pointOnCurveInfo', n = name)
        cmds.connectAttr(crv + '.worldSpace', pci + '.inputCurve')
        cmds.setAttr(pci+ '.parameter', u)
        cmds.connectAttr(pci + '.position', loc + '.t')

def attach_crv2():
    ofc_lis = cmds.ls(sl = 1)
    crv = 'l_eye_mid_crvShape'

    for i in range(30):
        name = ofc_lis[i].replace('_offset', '_pci')
        pci = cmds.createNode('pointOnCurveInfo', n = name)
        cmds.connectAttr(crv + '.worldSpace', pci + '.inputCurve')
        cmds.connectAttr(pci + '.position', ofc_lis[i] + '.t')
        cmds.setAttr(pci+ '.parameter', i)

        # pos = cmds.xform(ofc, q = 1, ws = 1, t = 1)
        # u = getUParam(pos, crv)
        
 
 
def build_aim_constraint(name_pfx):
    jnt_lis= cmds.ls(sl=1)
    aim_obj = '%s_back_loc'%name_pfx
    for jnt in jnt_lis:
        cmds.aimConstraint(aim_obj,jnt, aim=(-1,0,0) ,wuo='%s_up_loc'%name_pfx, wut= 'object')
        


def build_joint_on_crv(jnt_name_pfx):
    crv = cmds.ls(sl=1)[0]
    cmds.select(cl=1)
    for i in range(cmds.getAttr("%s.spans"%crv)+1):
        jnt_name = jnt_name_pfx+str(i+1)+"_jnt"
        cmds.joint(n=jnt_name)
        pci_name = jnt_name.replace("jnt", 'pci')
        pci = cmds.createNode('pointOnCurveInfo', n = pci_name)

        cmds.connectAttr(crv + '.worldSpace', pci_name + '.inputCurve')
        cmds.connectAttr(pci_name + '.position', jnt_name + '.t')
        cmds.setAttr(pci_name+ '.parameter', i)
        

def change_crv_color():
    crv_lis = cmds.ls(sl=1, shapes=1)
    for crv in crv_lis:
        cmds.setAttr(crv+'.overrideEnabled', 1)
        cmds.setAttr(crv+'.overrideColor', 24)
        print(crv)



# change_crv_color()



build_aim_constraint("r_blink")






# ofc_lis = cmds.ls(sl = 1)
# crv = 'up_finalShape'

# for i in range(9):
#     pci = cmds.createNode('pointOnCurveInfo', n = "eye_up_pci_%s"%i)
#     jnt = cmds.joint(n="eye_up_jnt_%s"%i)
#     cmds.connectAttr(crv + '.worldSpace', pci + '.inputCurve')
#     cmds.connectAttr(pci + '.position', jnt + '.t')
#     cmds.setAttr(pci+ '.parameter', i)
# attach_crv2()
# build_joint_on_crv("r_blink_lo_")

# jnt_lis = cmds.ls(sl=1)
# for jnt in jnt_lis:
#     cmds.setAttr(jnt+".jo", 0,0,0, type="double3")
    
    
    
    
    
    
    