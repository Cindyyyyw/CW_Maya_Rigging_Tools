import maya.mel as mel
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from PySide2 import QtUiTools, QtCore, QtGui, QtWidgets
from functools import partial # optional, for passing args during signal function calls

import os
from re import findall
import xml.etree.ElementTree as ET
import sys
import maya.cmds as cmds

    
def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class MainUI(QtWidgets.QWidget):
    """
    Create a default tool window.
    """
    window = None
    
    def __init__(self, parent = None):
        """
        Initialize class..
        """
        super(MainUI, self).__init__(parent=get_maya_main_window())
        self.setWindowFlags(    QtCore.Qt.Tool |
                                QtCore.Qt.WindowTitleHint |
                                QtCore.Qt.WindowCloseButtonHint |
                                QtCore.Qt.CustomizeWindowHint)
        self.widgetPath = ('/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/CWToolsQtProj/')
        self.widget = QtUiTools.QUiLoader().load(self.widgetPath + 'inverseWeight.ui')
        self.widget.setParent(self)
        
        self.xmlFileName = 'tempBlendShapeLayer.xml'
        self.xmlProcessedFileName = 'tempBlendShapeLayer_processed.xml'
        
        self.workDir = cmds.workspace(q=1, dir=1)
        
        # set initial window size
        self.resize(500, 300) 
        self.setFixedSize(self.size())     
        # # locate UI widgets
        self.close_btn = self.widget.findChild(QtWidgets.QPushButton, 'close_btn')        
        self.apply_btn = self.widget.findChild(QtWidgets.QPushButton, 'apply_btn')
        self.invert_btn = self.widget.findChild(QtWidgets.QPushButton, 'invert_btn')
        self.get_btn = self.widget.findChild(QtWidgets.QPushButton, 'get_btn')
        
        self.blendShapeNode_cbb = self.widget.findChild(QtWidgets.QComboBox, 'blendShapeNode_cbb')
        self.sourceLayer_cbb = self.widget.findChild(QtWidgets.QComboBox, 'sourceLayer_cbb')
        self.targetLayer_cbb = self.widget.findChild(QtWidgets.QComboBox, 'targetLayer_cbb')
        
        
        self._updateBlendShapeNode_cbb()
        self._updateLayerNode_cbb()

        
        # assign functionality to buttons
        self.close_btn.clicked.connect(self.close)
        self.apply_btn.clicked.connect(self.runInvert)
        self.get_btn.clicked.connect(self._updateBlendShapeNode_cbb)
        
        
        self.blendShapeNode_cbb.currentTextChanged.connect(self._updateLayerNode_cbb)
        
        
        # self._getBlendShapeNode()
        
    # updates the BlendShape Node combo box contents
    def _updateBlendShapeNode_cbb(self):
        self.blendShapeNode_cbb.clear()
        allNodes = self._getBlendShapeNode()
        if allNodes:
            self.blendShapeNode_cbb.addItems(allNodes)
            self.blendShapeNode_cbb.setCurrentIndex(self.currentBlendShapeIndex)
        else:
            self.blendShapeNode_cbb.setCurrentIndex(-1)
    # updates the two Layer Nodes combo box contents
    def _updateLayerNode_cbb(self):
        self.sourceLayer_cbb.clear()
        self.targetLayer_cbb.clear()
        allNodes = self._getBlendShapeAttr()
        
        if allNodes:
            self.sourceLayer_cbb.addItems(allNodes)
            self.targetLayer_cbb.addItems(allNodes)
    
    
    def _getBlendShapeNode(self):
        currentSelection = cmds.ls(sl=1)
        allNodes = cmds.ls(type="blendShape")
        inputNode = self._getinputNode(currentSelection)
        if inputNode:
            self.currentBlendShapeIndex = allNodes.index(inputNode)
        else:
            self.currentBlendShapeIndex = 0
        return allNodes

    def _getinputNode(self, currentSelection):
        if len(currentSelection)==1:
            selectionNode = cmds.ls(cmds.listHistory(currentSelection[0]), type="blendShape")
            if selectionNode:
                return selectionNode[0]
        return None

    def _getBlendShapeAttr(self):
        return(cmds.listAttr(self.blendShapeNode_cbb.currentText() + ".weight", m=True))
        
        
    def closeWindow(self):
        """
        Close window.
        """
        print ('closing window')
        self.destroy()
        
    def reverse_normalized_value(self, value):
        """Reverse a normalized value (1 - x)"""
        try:
            num = float(value)
            if 0 <= num <= 1:
                return f"{1 - num:.3f}"
            else:
                print("Warning: Value {} is not normalized (0-1 range)".format(value))
                return f"{1 - num:.3f}"  # Still reverse it
        except ValueError:
            print("Error: Cannot convert '{}' to number".format(value))
            return value

    def process_xml_file(self):
        """
        Process XML file to reverse normalized values from source weight to destination weight
        """
        source_name= self.sourceLayer_cbb.currentText()
        destination_name = self.TargetLayer_cbb.currentText()
        try:
            # Parse the XML file
            tree = ET.parse(self.xmlFilePath)
            root = tree.getroot()

            size = 0
            # Find source weight element
            source_weight = None
            destination_weight = None

            for shape in root.findall('.//shape'):
                size_attr = int(shape.get('size'))
                if size_attr > size:
                    size = size_attr

            
            for weight in root.findall('.//weights'):
                source_attr = weight.get('source')
                if source_attr == source_name:
                    source_weight = weight
                elif source_attr == destination_name:
                    destination_weight = weight
            
            if source_weight is None:
                print("Error: Could not find weight with source='{}'".format(source_name))
                return False
                
            if destination_weight is None:
                print("Error: Could not find weight with source='{}'".format(destination_name))
                return False
            
            # Extract point values from source and reverse them
            source_points = source_weight.findall('point')
            dest_points = destination_weight.findall('point')
            
            print("Found {} points in source weight".format(len(source_points)))
            print("Found {} points in destination weight".format(len(dest_points)))
            
            # Clear existing points in destination
            for point in dest_points:
                destination_weight.remove(point)

            source_DefaultValue = source_weight.get('defaultValue')
            destination_DefaultValue = destination_weight.get('defaultValue')
            print("Found source default value {} and destination default value {}".format(source_DefaultValue, destination_DefaultValue))
            # Process source points and add reversed values to destination
            destination_sizeCount = 0
            destination_max = -1
            for i in range(size):
                point = source_weight.find(f"./point[@index='{i}']")
                if point is None:
                    value = source_DefaultValue
                else:
                    value = point.get('value')
                reversed_value = reverse_normalized_value(value)
                if reversed_value == destination_DefaultValue:
                    continue
                destination_sizeCount +=1
                destination_max = i
                print("Reversing {} to {}".format(value, reversed_value))
                
                # Create new point element for destination
                new_point = ET.Element('point')
                new_point.set('index', str(i))
                new_point.set('value', reversed_value)

                destination_weight.append(new_point)

            destination_weight.set('size', str(destination_sizeCount))
            destination_weight.set('max', str(destination_max))
            
            # Write the modified XML
            self.xmlProcessedFilePath = self.xmlFilePath.replace('.xml', '_processed.xml')
            tree.write(self.xmlProcessedFilePath, encoding='utf-8', xml_declaration=True)
            print("Processed XML written to: {}".format(self.xmlProcessedFilePath))
            
            return True
            
        except ET.ParseError as e:
            print("Error parsing XML file: {}".format(e))
            return False, None
        except IOError as e:
            print("Error reading file: {}".format(e))
            return False, None


    def exportXML(self):
        self.xmlFilePath = cmds.deformerWeights(self.xmlFileName, ex=True, deformer=self.blendShapeNode_cbb.currentText())

    def readXML(self):
        source_name = self.sourceLayer_cbb.currentText()
        destination_name = self.targetLayer_cbb.currentText()
        
        print("Processing XML file: {}".format(self.xmlFileName))
        print("Source weight: {}".format(source_name))
        print("Destination weight: {}".format(destination_name))
        
        success = process_xml_file()
        
        if success:
            print("Processing completed successfully!")
        else:
            print("Processing failed!")
        return processedFile

    def deleteXML(self,pathList):
        for item in pathList:
            os.remove(item)
            print("Removed XML file: {}".format(item))

    def importXML(self):
        cmds.deformerWeights(self.xmlProcessedFilePath, path=self.workDir , im=1, method='index', df = self.blendShapeNode_cbb.currentText())
    
    def runInvert(self):

        exportXML()

        readXML()

        importXML()

        deleteXML([self.xmlProcessedFilePath, self.xmlFilePath ])


def openWindow():
    """
    ID Maya and attach tool window.
    """
    # Maya uses this so it should always return True
    if QtWidgets.QApplication.instance():
        # Id any current instances of tool and destroy
        for win in (QtWidgets.QApplication.allWindows()):
            if 'myToolWindowName' in win.objectName(): # update this name to match name below
                win.destroy()

    #QtWidgets.QApplication(sys.argv)
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(int(mayaMainWindowPtr), QtWidgets.QWidget)
    MainUI.window = MainUI(parent = mayaMainWindow)
    MainUI.window.setObjectName('myToolWindowName') # code above uses this to ID any existing windows
    MainUI.window.setWindowTitle('Invert Layer Weight')
    MainUI.window.show()
    
openWindow()
print(1)
    
    
    
    