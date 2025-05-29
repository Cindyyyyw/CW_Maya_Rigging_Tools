import maya.cmds as cmds

def buildZeroGrp(sl_list = None):
    """
    Builds a parent group on top of selection to ensure that selected object will have 
    zero values for transformation, rotation, and scale

    Args:
        N/A

    Returns:
        N/A

    Usage:
        >>> buildZeroGrp()
    """
    if not sl_list: sl_list = cmds.ls(sl=1)
    if not sl_list: return cmds.warning('[CWTools - buildZeroGrp]: Not enough object selected')
    
    for sl in sl_list:
        try:
            sl_parent = cmds.listRelatives(sl, p=1)
            zero_grp = cmds.group(em=1,p=sl_parent,name=sl+'_ZeroGrp')
        except:
            sl_parent = ''
            zero_grp = cmds.group(em=1,w=1,name=sl+'_ZeroGrp')

        cmds.matchTransform(zero_grp, sl)
        cmds.parent(sl, zero_grp)
    return zero_grp

def run(sl_list = None):
    if sl_list:
        buildZeroGrp(sl_list)
    else:
        buildZeroGrp(cmds.ls(sl=1))
