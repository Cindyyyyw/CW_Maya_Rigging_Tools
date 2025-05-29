import maya.cmds as cmds

def mergeCrv(sl_list = None):
    """
    Merges selected curves into one named 'mergedCrv'

    Args:
        N/A

    Returns:
        N/A

    Usage:
        >>> mergeCrv()
    """
    if not sl_list: sl_list = cmds.ls(sl=1, type='transform')
    if not sl_list: return cmds.warning('[CWTools - mergeCrv]: Not enough object selected')
    newCrv = cmds.group(em=1, w=1, n='mergedCrv')
    crvShape = []
    print(sl_list)
    for sl in sl_list:
        print(sl)
        cmds.delete(sl, ch=1)
        cmds.makeIdentity(sl, a=1)
        crvShape.extend(cmds.listRelatives(sl,type='nurbsCurve', shapes=1))
    cmds.select(crvShape,r=1)
    cmds.select(newCrv, add=1)
    cmds.parent(r=1, s=1)
    cmds.select(newCrv,r=1)
    cmds.delete(newCrv, ch=1)
    cmds.delete(sl_list)
    return

def run():
    mergeCrv()