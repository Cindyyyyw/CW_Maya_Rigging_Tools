import maya.cmds as cmds

def rename_shape_nodes():
    # Get selected objects
    selected_objects = cmds.ls(selection=True, long=True)

    # Check if something is selected
    if not selected_objects:
        cmds.warning("No objects selected!")
        return

    for obj in selected_objects:
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
            cmds.warning("{} is not a transform node.".format(obj_short))

# Run the function
rename_shape_nodes()
