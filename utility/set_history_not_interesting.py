import maya.cmds as cmds

def setHistoryNotInteresting(sl_list = None):
    """
    Sets isHistoricallyInteresting False for selected objects

    Args:
        N/A

    Returns:
        N/A

    Usage:
        >>> setHistoryNotInteresting()
    """
    if not sl_list: sl_list = cmds.ls(sl=1)
    if not sl_list: return cmds.warning('[CWTools - setHistoryNotInteresting]: Not enough object selected')
    for sl in sl_list:
        setObj = cmds.listRelatives(sl,shapes=1)
        if setObj:
            for obj in setObj:
                cmds.setAttr(f'{obj}.isHistoricallyInteresting',0)
    return

def run():
    setHistoryNotInteresting()