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

    return [u_value, v_value]

def move_flc_in_place(flc, u_value, v_value):
    cmds.setAttr("%s.parameterU"%flc, u_value)
    cmds.setAttr("%s.parameterV"%flc, v_value)

def create_flc_on_mesh(num, mesh):
    flc_lis = []
    for j in range(num):
        print(f'creating {mesh}_flc_{j}Shape')
        flc_shape = cmds.createNode('follicle', name=f'{mesh}_flc_{j}Shape')
        
        flc_trans = cmds.listRelatives(flc_shape, parent=1)[0]
        flc_trans = cmds.rename(flc_trans, f'{mesh}_flc_{j}')
        
        # Connect mesh shape to follicle input
        mesh_shape = cmds.listRelatives(mesh, shapes=1, type='mesh')[0]
        cmds.connectAttr(mesh_shape + ".outMesh", flc_shape + ".inputMesh", force=True)
        cmds.connectAttr(mesh_shape + ".worldMatrix[0]", flc_shape + ".inputWorldMatrix", force=True)

        # Connect follicle output to transform
        cmds.connectAttr(flc_shape + ".outTranslate", flc_trans + ".translate", force=True)
        cmds.connectAttr(flc_shape + ".outRotate", flc_trans + ".rotate", force=True)
        flc_lis.append(flc_shape)
    
    return flc_lis

def runFunc():
    sl_lis = cmds.ls(sl=1)
    loc_lis = []
    mesh_lis = []
    
    for sl in sl_lis:
        if cmds.listRelatives(sl, shapes=1, type='locator'):
            loc_lis.append(sl)
        elif cmds.listRelatives(sl,shapes=1, type='mesh'):
            mesh_lis.append(sl)

    if not mesh_lis or len(mesh_lis)>1:
        return cmds.warning('Please select one mesh only.')
    mesh = mesh_lis[0]

    flc_lis = create_flc_on_mesh(len(loc_lis), mesh)
    
    i = 0
    for loc in loc_lis:
        [u, v] = get_closest_uv(mesh, loc)
        move_flc_in_place(flc_lis[i], u, v, loc)
        i+=1