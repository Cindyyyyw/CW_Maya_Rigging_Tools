import maya.cmds as cmds

def placeLocatorAtVertCenter(sl_list = None):
    """
    Retrieves the average center position of selected vertices and place a locator at the position.

    Args:
        N/A

    Returns:
        N/A

    Usage:
        >>> placeLocatorAtVertCenter()
    """
    if not sl_list: sl_list = cmds.ls('*.vtx[*]', selection=True, flatten=True, type='float3')
    if not sl_list: return cmds.warning("[CWTools - placeLocatorAtVertCenter]: No vertices were selected.")
    
    # Initialize sum variables for x, y, z coordinates
    total_x = 0
    total_y = 0
    total_z = 0
    num_vertices = len(sl_list)
    
    # Iterate through each selected vertex and sum up its coordinates
    for vertex in sl_list:
        position = cmds.pointPosition(vertex, world=True)
        total_x += position[0]
        total_y += position[1]
        total_z += position[2]

    # Calculate the average (center)
    center_x = total_x / num_vertices
    center_y = total_y / num_vertices
    center_z = total_z / num_vertices

    center = (center_x, center_y, center_z)
    
    # Create a locator at the calculated center
    locator = cmds.spaceLocator()[0]
    cmds.xform(locator, worldSpace=True, translation=center)
    return locator

def run():
    placeLocatorAtVertCenter()
