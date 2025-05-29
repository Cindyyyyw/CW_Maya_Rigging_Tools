import maya.cmds as cmds

def sortSelection(sl_list = None):
    """
    Sorts selected objects that are under the same parent

    Args:
        N/A

    Returns:
        N/A

    Usage:
        >>> sortSelection()
    """
    if not sl_list: sl_list = cmds.ls(sl=1)
    if not sl_list: return cmds.warning('[CWTools - sortSelection]: Not enough object selected')
    try:
        parent = cmds.listRelatives(sl_list[0], p=1)[0]
    except:
        parent = "world"
    
    for item in sl_list:
        try:
            item_parent = cmds.listRelatives(item, p=1)[0]
        except:
            item_parent = "world"
        if item_parent != parent:
            cmds.error("All selection must be under the same parent")
    
    
    if parent == "world":
        temp = cmds.group(sl_list, w=1, name ="temp_sort_grp")
        cmds.parent(sorted(sl_list), w = 1, a = 1)
    else:
        temp = cmds.group(sl_list, p=parent, name ="temp_sort_grp")
        cmds.parent(sorted(sl_list)+[parent], a = 1)
    cmds.delete(temp)
    return

def run():
    sortSelection()