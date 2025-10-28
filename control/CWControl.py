import json
import os
import maya.cmds as cmds
from utility.build_zero_grp import buildZeroGrp

from importlib import reload

# import utility as util

# reload(utility)

class CWControlManager:
    def __init__(self, json_path):
        self.json_path = json_path
        if not os.path.exists(self.json_path):
            with open(self.json_path, 'w') as f:
                json.dump({}, f)

    def _loadData(self):
        with open(self.json_path, 'r') as f:
            return json.load(f)

    def _saveData(self, data):
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=4)

    def _shapeNode(self, curve_name: str):
        if not cmds.objExists(curve_name): 
            cmds.warning(f"Object does not exist: {curve_name}")
            return None
        shape_nodes = cmds.listRelatives(curve_name, shapes=True, type = 'nurbsCurve', c=1)
        if not shape_nodes:
            cmds.warning(f"Transform does not contain nurbsCurve shape nodes: {curve_name}")
            return None
        return shape_nodes
        
    def listShapes(self):
        data = self._loadData()
        return list(data.keys())

    def createShape(self, shape_name: str, ctrl_name : str = 'CWCtrl', zero_grp : bool=False, obj=None):
        """
        Creates a control curve from saved shape data. Supports multiple shapes.
        """
        data = self._loadData()
        shape_data = data.get(shape_name)
        if not shape_data:
            cmds.warning(f"Shape '{shape_name}' not found.")
            return

        # If it's a single shape segment (dict), wrap in list
        if isinstance(shape_data, dict):
            shape_data = [shape_data]

        temp_curves = []

        for i, shape in enumerate(shape_data):
            points = shape['points']
            degree = shape.get('degree', 1)
            form = shape.get('form', 'open')
            knot = shape.get('knot')
            form_flag = {'open': False, 'closed': True, 'periodic': True}[form]
            temp_curve = cmds.curve(name=f"{ctrl_name}_tempShape{i}", degree=degree, p=points, knot=knot)

            temp_curves.append(temp_curve)

        # Use the first transform as the final control name
        ctrl = cmds.rename(temp_curves[0], ctrl_name)

        # Parent other shape nodes under this transform
        for temp in temp_curves[1:]:
            shapes = cmds.listRelatives(temp, shapes=True, fullPath=True) or []
            for s in shapes:
                cmds.parent(s, ctrl, shape=True, r=True)
            cmds.delete(temp)  # delete empty transform
        if obj:
            cmds.matchTransform(ctrl, obj)
        
        if zero_grp:
            buildZeroGrp([ctrl])
        return ctrl_name

    def extractShape(self, curve_name: str, shape_name: str):
        print('extract shape')
        shape_nodes = self._shapeNode(curve_name)
        if not shape_nodes: return cmds.warning('Not enough object was selected')
        shape_data = []

        existing_shapes = self.listShapes()
        if shape_name in existing_shapes:
            return cmds.warning(f'A control named [{curve_name}] already exists, rename and try again.')
        
        for shape_node in shape_nodes:
            temp = cmds.createNode( 'curveInfo' )
            degree = cmds.getAttr(f"{shape_node}.degree")
            form_val = cmds.getAttr(f"{shape_node}.form")
            spans = cmds.getAttr(f"{shape_node}.spans")
            cmds.connectAttr( f"{shape_node}.worldSpace", f'{temp}.inputCurve', f=1 )
            cvs = cmds.getAttr( f'{temp}.controlPoints[*]' )
            knots = cmds.getAttr( f'{temp}.knots[*]' )

            form = {0: 'open', 1: 'closed', 2: 'periodic'}.get(form_val, 'open')

            shape_data.append({
                'points': cvs,
                'degree': degree,
                'form': form,
                'spans': spans,
                'knot': knots
            })
            cmds.delete(temp)
        data = self._loadData()
        data[shape_name] = shape_data
        self._saveData(data)
        print(f"Saved shape '{shape_name}' to {self.json_path}")

    # Function to set the curve width
    def setCurveWidth(self, new_width: int, curve_name: str):
        shape_nodes = self._shapeNode(curve_name)     
        if not shape_nodes:
            return
        
        # # Find the shape node (since 'lineWidth' is typically on the shape, not the transform)
        # shape_nodes = cmds.listRelatives(curve_name, shapes=True, type = 'nurbsCurve')
        
        # if not shape_nodes:return cmds.warning(f"Transform does not contain nurbsCurve shape nodes: {curve_name}")
        for shape_node in shape_nodes: 
            # Apply the new width using 'setAttr' to change the curve width
            if cmds.attributeQuery('lineWidth', node=shape_node, exists=True):
                cmds.setAttr(shape_node + ".lineWidth", new_width)
                print(f"Object {shape_node} width changed to {new_width}".format())
            else:
                cmds.warning(f"Object {shape_node} does not contain 'lineWidth' attribute, skipped")
        return
    
    def setCurveColor(self, new_color: int, curve_name: str):        
        if not cmds.objExists(curve_name): return cmds.warning(f"Object does not exist: {curve_name}")
        if new_color > 31 or new_color < 0: 
            return cmds.warning(f"Invalid color index, must be between 0 and 31.")
        # Find the shape node (since 'lineWidth' is typically on the shape, not the transform)
        shape_nodes = cmds.listRelatives(curve_name, shapes=True, type = 'nurbsCurve')
        
        if not shape_nodes:return cmds.warning(f"Transform does not contain nurbsCurve shape nodes: {curve_name}")
        for shape_node in shape_nodes: 
            # Apply the new width using 'setAttr' to change the curve width
            if cmds.attributeQuery('overrideColor', node=shape_node, exists=True):
                cmds.setAttr(f"{shape_node}.overrideEnabled", 1)
                cmds.setAttr(f"{shape_node}.overrideColor", new_color)
                print(f"Object {shape_node} color changed.".format())
            else:
                cmds.warning(f"Object {shape_node} does not contain 'overrideColor' attribute, skipped")
        return


# libDir = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/control/'

# manager = CWControlManager(os.path.join(libDir, 'CWControlLib.json'))

# List available shapes
# print(manager.listShapes())

# change curve width
# manager.setCurveWidth(5, cmds.ls(sl=1)[0])
# manager.setCurveColor(6, cmds.ls(sl=1)[0])

# Create a control
# manager.createShape('pin', 'testName', True)

# Extract curves and store it
# sl_lis = cmds.ls(sl=1)
# for sl in sl_lis:
#     manager.extractShape(sl, sl)
