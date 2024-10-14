import maya.cmds as cmds

# Global variable to store dynamic space fields
space_fields = []

def create_control_space(control, space_options):
    # Add the "spaceCtrl" attribute (enum, locked, non-keyable)
    cmds.addAttr(control, longName="spaceCtrl", attributeType="enum", enumName="------")
    cmds.setAttr("%s.spaceCtrl" % control, lock=True, keyable=False)
    
    # Add "spaceA" and "spaceB" attributes with user-defined space options
    space_enum = ":".join(space_options)
    cmds.addAttr(control, longName="spaceA", attributeType="enum", enumName=space_enum, keyable=True)
    cmds.addAttr(control, longName="spaceB", attributeType="enum", enumName=space_enum, keyable=True)
    
    # Add "spaceBlend" attribute (float, min 0, max 1)
    cmds.addAttr(control, longName="spaceBlend", attributeType="float", minValue=0.0, maxValue=1.0, defaultValue=0.0, keyable=True)
    
    # Iterate over the spaces to create condition nodes and space blend calculations
    for i, space_name in enumerate(space_options):
        # Create condition node for space A
        condition_a = cmds.createNode("condition", name="%s_conditionA_%s" % (control, space_name))
        cmds.connectAttr("%s.spaceA" % control, "%s.firstTerm" % condition_a)
        cmds.setAttr("%s.secondTerm" % condition_a, i)
        cmds.setAttr("%s.colorIfTrueR" % condition_a, 1)  # Output 1 if true
        cmds.setAttr("%s.colorIfFalseR" % condition_a, 0)  # Output 0 if false
        
        # Create condition node for space B
        condition_b = cmds.createNode("condition", name="%s_conditionB_%s" % (control, space_name))
        cmds.connectAttr("%s.spaceB" % control, "%s.firstTerm" % condition_b)
        cmds.setAttr("%s.secondTerm" % condition_b, i)
        cmds.setAttr("%s.colorIfTrueR" % condition_b, 1)  # Output 1 if true
        cmds.setAttr("%s.colorIfFalseR" % condition_b, 0)  # Output 0 if false
        
        # Create multiplyDivide nodes for weighted space A and B
        mult_div_a = cmds.createNode("multiplyDivide", name="%s_multDivA_%s" % (control, space_name))
        cmds.connectAttr("%s.outColorR" % condition_a, "%s.input1X" % mult_div_a)
        cmds.connectAttr("%s.spaceBlend" % control, "%s.input2X" % mult_div_a)
        
        mult_div_b = cmds.createNode("multiplyDivide", name="%s_multDivB_%s" % (control, space_name))
        cmds.connectAttr("%s.outColorR" % condition_b, "%s.input1X" % mult_div_b)
        cmds.connectAttr("%s.spaceBlend" % control, "%s.input2X" % mult_div_b)
        
        # For every three spaces, create a plusMinusAverage node to sum up the weighted spaces
        if (i % 3) == 0:
            plus_minus_avg = cmds.createNode("plusMinusAverage", name="%s_plusMinusAvg_%s" % (control, space_name))
            
        # Connect the weighted values from mult_div_a and mult_div_b into the plusMinusAverage node
        cmds.connectAttr("%s.outputX" % mult_div_a, "%s.input1D[%d]" % (plus_minus_avg, i * 2))
        cmds.connectAttr("%s.outputX" % mult_div_b, "%s.input1D[%d]" % (plus_minus_avg, i * 2 + 1))
    
    print("Control space setup completed for %s." % control)

def control_space_builder_UI():
    global space_fields
    
    if cmds.window("controlSpaceBuilderUI", exists=True):
        cmds.deleteUI("controlSpaceBuilderUI")
    
    window = cmds.window("controlSpaceBuilderUI", title="Control Space Builder", widthHeight=(300, 400))
    form_layout = cmds.formLayout()

    # Scroll layout to allow dynamic addition of space options
    scroll_layout = cmds.scrollLayout(width=300, height=250, parent=form_layout)
    space_field_layout = cmds.columnLayout(adjustableColumn=True, parent=scroll_layout)
    
    # Initial space fields
    space_fields = []
    add_space_field(space_field_layout)
    add_space_field(space_field_layout)
    
    # Add buttons for adding/removing spaces and building the control space
    add_button = cmds.button(label="Add Space", command=lambda x: add_space_field(space_field_layout), parent=form_layout)
    remove_button = cmds.button(label="Remove Space", command=lambda x: remove_space_field(space_field_layout), parent=form_layout)
    build_button = cmds.button(label="Build Control Space", command=build_control_space_from_UI, parent=form_layout)
    
    # Positioning the UI elements in the form layout
    cmds.formLayout(form_layout, edit=True,
                    attachForm=[(scroll_layout, 'top', 10), (scroll_layout, 'left', 10), (scroll_layout, 'right', 10),
                                (add_button, 'left', 10), (add_button, 'right', 160), (remove_button, 'left', 160), (remove_button, 'right', 10), 
                                (build_button, 'left', 10), (build_button, 'right', 10), (build_button, 'bottom', 10)],
                    attachControl=[(scroll_layout, 'bottom', 10, add_button), (add_button, 'bottom', 10, build_button)])

    cmds.showWindow(window)

def add_space_field(parent_layout):
    global space_fields
    space_field = cmds.textFieldGrp(label="Space Option %d" % (len(space_fields)+1), placeholderText="Enter space name", columnAlign=(1, 'right'), parent=parent_layout)
    space_fields.append(space_field)
    cmds.setParent(parent_layout)  # Ensure the new fields are added to the correct layout

def remove_space_field(parent_layout):
    global space_fields
    if space_fields:
        field_to_remove = space_fields.pop()  # Remove the last space field
        cmds.deleteUI(field_to_remove)  # Remove the UI element from the layout
    else:
        cmds.warning("No more space options to remove.")

def build_control_space_from_UI(*args):
    global space_fields
    
    selected_control = cmds.ls(selection=True)
    
    if not selected_control:
        cmds.warning("Please select a control.")
        return
    
    selected_control = selected_control[0]
    
    # Collect user-defined space options from the text fields
    space_options = []
    for field in space_fields:
        space_name = cmds.textFieldGrp(field, query=True, text=True)
        if space_name:
            space_options.append(space_name)
    
    if len(space_options) < 2:
        cmds.warning("Please define at least two space options.")
        return
    
    # Build the control space
    create_control_space(selected_control, space_options)

# Launch the UI
control_space_builder_UI()
