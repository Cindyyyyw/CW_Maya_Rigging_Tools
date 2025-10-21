import maya.cmds as cmds

def renameShapeNodes(sl_list = None):
    """
    Renames selected transforms' shape nodes to avoid duplicate names

    Args:
        N/A

    Returns:
        N/A

    Usage:
        >>> renameShapeNodes()
    """
    if not sl_list: sl_list = cmds.ls(selection=True, long=True)
    if not sl_list: return cmds.warning('[CWTools - renameShapeNodes]: Not enough object selected')

    # Check if something is selected
    if not sl_list:
        cmds.warning("No objects selected!")
        return

    for obj in sl_list:
        # Ensure the object is a transform node
        if cmds.objectType(obj) == "transform":
            # Get the shape nodes under the transform
            shape_nodes = cmds.listRelatives(obj, shapes=True, fullPath = True)
            obj_short = obj.split("|")[-1]
            
            if not shape_nodes:
                cmds.warning("No shape nodes found under {}".format(obj_short))
                continue

            # Rename each shape node
            for i in range(len(shape_nodes)):
                new_name = "{}_{}".format(obj_short, i+1)
                # try:
                cmds.rename(shape_nodes[i], new_name)
                print("Renamed {} to {}".format(shape_nodes[i], new_name))
                # except:
                #     cmds.warning("Could not rename shape {}".format(shape_nodes[i]))
        else:
            cmds.warning("{} is not a transform node.".format(obj))

def run(sl_list=None):
    renameShapeNodes(sl_list)
