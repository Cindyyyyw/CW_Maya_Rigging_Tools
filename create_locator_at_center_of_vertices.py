import maya.cmds as cmds

def create_locator_at_center_of_vertices():
    # Get selected vertices
    selected_vertices = cmds.ls(selection=True, flatten=True)
    
    if not selected_vertices:
        print("No vertices selected.")
        return None

    # Initialize sum variables for x, y, z coordinates
    total_x = 0
    total_y = 0
    total_z = 0
    num_vertices = len(selected_vertices)
    
    # Iterate through each selected vertex and sum up its coordinates
    for vertex in selected_vertices:
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
    
    print("Locator created at:", center)
    
    return locator

# Call the function to create the locator
create_locator_at_center_of_vertices()
