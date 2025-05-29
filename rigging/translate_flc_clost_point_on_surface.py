import maya.cmds as cmds

def get_closest_uv(mesh, locator):
    """
    Query the UV parameter of the closest point on a mesh to a locator.

    Args:
        mesh (str): The name of the mesh object.
        locator (str): The name of the locator object.

    Returns:
        tuple: U and V parameters of the closest point on the mesh.
    """
    # Ensure the mesh and locator exist
    if not cmds.objExists(mesh) or not cmds.objExists(locator):
        cmds.error("Mesh or locator does not exist.")
        return None

    # Get the world position of the locator
    locator_position = cmds.xform(locator, query=True, worldSpace=True, translation=True)

    # Create a closestPointOnMesh node
    cpom_node = cmds.createNode("closestPointOnMesh", name="temp_closestPointOnMesh")

    # Connect the mesh's shape to the closestPointOnMesh node
    mesh_shape = cmds.listRelatives(mesh, shapes=True, fullPath=True)
    if not mesh_shape:
        cmds.error("The mesh has no shape node.")
        return None
    cmds.connectAttr(mesh_shape[0] + ".outMesh", cpom_node + ".inMesh", force=True)

    # Set the position on the closestPointOnMesh node
    cmds.setAttr(cpom_node + ".inPositionX", locator_position[0])
    cmds.setAttr(cpom_node + ".inPositionY", locator_position[1])
    cmds.setAttr(cpom_node + ".inPositionZ", locator_position[2])

    # Query the U and V parameters
    u_value = cmds.getAttr(cpom_node + ".parameterU")
    v_value = cmds.getAttr(cpom_node + ".parameterV")

    # Clean up the temporary node
    cmds.delete(cpom_node)

    return u_value, v_value

def move_flc_in_place(flc, u_value, v_value, loc):
    cmds.setAttr("%s.parameterU"%flc, u_value)
    cmds.setAttr("%s.parameterV"%flc, v_value)
    cmds.rename(flc, loc.replace("loc", "flc"))



loc_lis = cmds.ls(selection=True)
flc_lis = cmds.ls("flc_*", et="transform",shapes=0)

mesh = "Dragon_spike_proxy"
print(loc_lis)
i = 0
for loc in loc_lis:
    [u, v] = get_closest_uv(mesh, loc)
    move_flc_in_place(flc_lis[i], u, v, loc)
    i+=1