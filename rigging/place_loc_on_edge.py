# Uniformly places user defined amount of locators onto selected edge
import maya.cmds as cmds

def locatorsOnEdgeUI():
    """Create a UI for the user to place locators on an edge."""
    # Check if the window already exists and delete it
    if cmds.window("locatorsOnEdgeWin", exists=True):
        cmds.deleteUI("locatorsOnEdgeWin")
    
    # Create the window
    window = cmds.window("locatorsOnEdgeWin", title="Locators on Edge", widthHeight=(300, 150))
    cmds.columnLayout(adjustableColumn=True)
    
    # Add input field for number of locators
    cmds.text(label="Number of Locators:")
    num_locators_field = cmds.intField(value=10, minValue=1)
    
    # Add a button to run the function
    cmds.button(label="Place Locators", command=lambda _: locatorsOnEdgeUICallback(num_locators_field))
    
    # Add a close button
    cmds.button(label="Close", command=lambda _: cmds.deleteUI(window))
    
    # Show the window
    cmds.showWindow(window)

def locatorsOnEdgeUICallback(num_locators_field):
    """Callback function for the UI to create locators."""
    try:
        num_locators = cmds.intField(num_locators_field, query=True, value=True)
        locatorsOnEdge(num_locators)
    except Exception as e:
        cmds.error("Error: %s" % str(e))

def isConsecutiveEdges(selection):
    
    # Ensure the selection contains edges
    if not selection or not all(".e[" in edge for edge in selection):
        return False
    
    # Convert edges to vertices
    connected_vertices = cmds.polyListComponentConversion(selection, toVertex=True)
    connected_vertices = cmds.ls(connected_vertices, flatten=True)
    
    # Convert vertices back to edges to find all connected edges
    connected_edges = cmds.polyListComponentConversion(connected_vertices, toEdge=True)
    connected_edges = cmds.ls(connected_edges, flatten=True)
    
    # Check if all selected edges are part of the connected edges set
    selected_set = set(selection)
    connected_set = set(connected_edges)
    
    if selected_set.issubset(connected_set):
        return True
    
    return False

def locatorsOnEdge(num_locators):
    """Place locators along a selected edge."""
    # Ensure the user selected an edge
    selection = cmds.ls(selection=True, fl=True)
    if not selection or not isConsecutiveEdges(selection):
        cmds.error("Please select a single edge.")
        return
    
    selected_edge = selection[0]
    
    # Create a curve from the selected edge
    curve = cmds.polyToCurve(form=2, degree=1, conformToSmoothMeshPreview=0)[0]
    
    # Prepare locators placement
    locators = []
    for i in range(num_locators):
        # Calculate the parameter along the curve (0.0 to 1.0)
        param = float(i) / (num_locators - 1) if num_locators > 1 else 0.5
        
        # Create a locator
        loc_name = "locator_%s" % (i + 1)
        locator = cmds.spaceLocator(name=loc_name)[0]
        locators.append(locator)
        
        # Create a pointOnCurveInfo node
        poc_node = cmds.createNode("pointOnCurveInfo", name="%s_poc" % loc_name)
        cmds.connectAttr("%s.worldSpace[0]" % curve, "%s.inputCurve" % poc_node)
        cmds.setAttr("%s.parameter" % poc_node, param)
        cmds.setAttr("%s.turnOnPercentage" % poc_node, 1)

        # Connect the pointOnCurveInfo node to the locator's position
        cmds.connectAttr("%s.position" % poc_node, "%s.translate" % locator)
    
    # Group locators for organizational purposes
    locator_group = cmds.group(locators, name="locators_group")
    print("Created %s locators on %s, grouped as %s." % (num_locators, curve, locator_group))
    # Clean up
    cmds.delete(curve)

def runUI():
    locatorsOnEdgeUI()
