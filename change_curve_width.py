import maya.cmds as cmds

# Function to change the curve width
def change_curve_width(*args):
    # Get the slider value
    new_width = cmds.floatSliderGrp('width_slider', query=True, value=True)
    
    # Get selected objects
    selected_objects = cmds.ls(selection=True)
    
    if not selected_objects:
        cmds.warning("No objects selected!")
        return
    
    # Loop through selected objects
    for obj in selected_objects:
        # Find the shape node (since 'lineWidth' is typically on the shape, not the transform)
        shape_nodes = cmds.listRelatives(obj, shapes=True)
        for shape_node in shape_nodes:
            # Apply the new width using 'setAttr' to change the curve width
            if cmds.attributeQuery('lineWidth', node=shape_node, exists=True):
                cmds.setAttr(shape_node + ".lineWidth", new_width)
                print("Object [{}] width changed.".format(shape_node))
            else:
                cmds.warning("Object {} does not have the 'lineWidth' attribute.".format(obj))

# Function to create the UI
def create_ui():
    # If the window exists, delete it
    if cmds.window("curveWidthUI", exists=True):
        cmds.deleteUI("curveWidthUI")
    
    # Create a new window
    window = cmds.window("curveWidthUI", title="Change Curve Width", widthHeight=(300, 100))
    
    # Create a layout to hold the UI elements
    cmds.columnLayout(adjustableColumn=True)
    
    # Add a slider for changing the curve width
    cmds.floatSliderGrp('width_slider', field=True, label='Curve Width', minValue=0.1, maxValue=10.0, value=1.0)
    
    # Add a button to apply the width change
    cmds.button(label="Apply Width", command=change_curve_width)
    
    # Show the window
    cmds.showWindow(window)

# Run the UI
create_ui()
