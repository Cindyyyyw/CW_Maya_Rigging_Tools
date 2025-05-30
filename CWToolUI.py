import os
import maya.cmds as cmds
import maya.mel as mel
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from PySide2 import QtUiTools, QtCore, QtGui, QtWidgets
from functools import partial # optional, for passing args during signal function calls
import traceback
from PySide2.QtGui import QIntValidator
from importlib import reload

import sys
sys.path.insert(0, '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/')

import utility as util
import control as ctrl
import rigging as rig

reload(util)
reload(ctrl)
reload(rig)

# reload(util.place_locator_at_vert_center)
# reload(util.build_zero_grp)
# reload(util.rename_shape_nodes)
# reload(util.place_locator_at_vert_center)
# reload(util.sort_selection)
# reload(util.merge_crv)
# reload(util.set_history_not_interesting)
# reload(ctrl.CWControl)
reload(rig.attach_flc_to_mesh)


def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class CWToolsMainUI(QtWidgets.QWidget):
    """
    Create a default tool window.
    """
    window = None
    
    def __init__(self, parent = get_maya_main_window()):
        """
        Initialize class.
        """
        super(CWToolsMainUI, self).__init__(parent)
        self.setWindowFlags(    QtCore.Qt.Tool |
                                QtCore.Qt.WindowTitleHint |
                                QtCore.Qt.WindowCloseButtonHint |
                                QtCore.Qt.CustomizeWindowHint)
        self.widgetPath = ('/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/CWToolsQtProj/')
        self.widget = QtUiTools.QUiLoader().load(self.widgetPath + 'mainWindow.ui')
        self.widget.setParent(self)
        # set initial window size
        self.resize(300, 600)
        self.setFixedSize(300,600)

        self.color_table=self._getUserColorIndex()

        # locate UI widgets
        self.btn_close = self.widget.findChild(QtWidgets.QPushButton, 'btn_close')
        self.btn_buildZeroGrp = self.widget.findChild(QtWidgets.QPushButton, 'btn_buildZeroGrp')
        self.btn_placeLocatorAtVertCenter = self.widget.findChild(QtWidgets.QPushButton, 'btn_placeLocatorAtVertCenter')
        self.btn_renameShapeNodes = self.widget.findChild(QtWidgets.QPushButton, 'btn_renameShapeNodes')
        self.btn_sortSelection = self.widget.findChild(QtWidgets.QPushButton, 'btn_sortSelection')
        self.btn_mergeCrv = self.widget.findChild(QtWidgets.QPushButton, 'btn_mergeCrv')
        self.btn_setHistoryNotInteresting = self.widget.findChild(QtWidgets.QPushButton, 'btn_setHistoryNotInteresting')
        
        # extract ctrl shape items
        self.txt_ctrlName = self.widget.findChild(QtWidgets.QLineEdit, 'txt_ctrlName')
        self.btn_extractShape = self.widget.findChild(QtWidgets.QPushButton, 'btn_extractShape')

        # create ctrl shape items
        self.btn_createShape = self.widget.findChild(QtWidgets.QPushButton, 'btn_createShape')
        self.cbx_ctrlZeroGrp = self.widget.findChild(QtWidgets.QCheckBox, 'cbx_ctrlZeroGrp')
        self.cbb_setCtrlShape = self.widget.findChild(QtWidgets.QComboBox, 'cbb_setCtrlShape')

        # change ctrl width items
        self.txt_width = self.widget.findChild(QtWidgets.QLineEdit, 'txt_width')
        self.sdr_width = self.widget.findChild(QtWidgets.QSlider, 'sdr_width')
        self.btn_setCtrlWidth = self.widget.findChild(QtWidgets.QPushButton, 'btn_setCtrlWidth')
        
        self.txt_width.setValidator(QIntValidator(0, 99999, self))

        # change ctrl color items
        self.sdr_color = self.widget.findChild(QtWidgets.QSlider, 'sdr_color')
        self.lbl_colorIndicator = self.widget.findChild(QtWidgets.QLabel, 'lbl_colorIndicator')
        self.btn_setCtrlColor = self.widget.findChild(QtWidgets.QPushButton, 'btn_setCtrlColor')

        # rigging tab btns
        self.btn_wireRig = self.widget.findChild(QtWidgets.QPushButton, 'btn_wireRig')
        self.btn_twistJoint = self.widget.findChild(QtWidgets.QPushButton, 'btn_twistJoint')
        self.btn_locatorOnEdge = self.widget.findChild(QtWidgets.QPushButton, 'btn_locatorOnEdge')
        self.btn_attachFlc = self.widget.findChild(QtWidgets.QPushButton, 'btn_attachFlc')
        print(self.btn_attachFlc)






        self.libDir = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/control/'

        self.ctrlManager = ctrl.CWControlManager(os.path.join(self.libDir, 'CWControlLib.json'))


        # assign functionality to buttons
        self.btn_close.clicked.connect(self.closeWindow)
        self.btn_buildZeroGrp.clicked.connect(self.buildZeroGrp)
        self.btn_placeLocatorAtVertCenter.clicked.connect(self.placeLocatorAtVertCenter)
        self.btn_renameShapeNodes.clicked.connect(self.renameShapeNodes)
        self.btn_sortSelection.clicked.connect(self.sortSelection)
        self.btn_mergeCrv.clicked.connect(self.mergeCrv)
        self.btn_setHistoryNotInteresting.clicked.connect(self.setHistoryNotInteresting)
        self.btn_createShape.clicked.connect(self.createCtrlShape)
        self.btn_extractShape.clicked.connect(self.extractCtrlShape)

        # self.sdr_width.sliderMoved.connect(self.update_txt_width)
        self.txt_width.editingFinished.connect(self.txt_widthUpdateEvt)
        self.sdr_width.valueChanged.connect(self.sdr_widthUpdateEvt)
        self.btn_setCtrlWidth.clicked.connect(self.setCtrlWidth)

        self._fetchCtrlName()
        
        self.sdr_color.valueChanged.connect(self.sdr_colorUpdateEvt)
        self.btn_setCtrlColor.clicked.connect(self.setCtrlColor)

        self.btn_wireRig.clicked.connect(self.launchWireRigUI)
        self.btn_twistJoint.clicked.connect(self.launchTwistJntUI)
        self.btn_locatorOnEdge.clicked.connect(self.launchlocOnEdgeUI)
        self.btn_attachFlc.clicked.connect(self.attachFlc)


    # def resizeEvent(self, event):
    #     """
    #     Called on automatically generated resize event
    #     """
    #     self.widget.resize(self.widget.width(), self.widget.height())
    def _fetchCtrlName(self):
        ctrlNames = self.ctrlManager.listShapes()
        self.cbb_setCtrlShape.addItems(ctrlNames)

    def closeWindow(self):
        """
        Close window.
        """
        print ('closing window')
        self.destroy()

    def wrapUndoInfo(self, func):
        try:
            cmds.undoInfo(openChunk=True)
            func()
        except Exception as e:
            print("Error occurred:", e)
            traceback.print_exc()
        finally:
            cmds.undoInfo(closeChunk=True)   
            return

    def buildZeroGrp(self):
        self.wrapUndoInfo(util.buildZeroGrp)

    def placeLocatorAtVertCenter(self):
        self.wrapUndoInfo(util.placeLocatorAtVertCenter)
        
    def renameShapeNodes(self):
        self.wrapUndoInfo(util.renameShapeNodes)

    def sortSelection(self):
        self.wrapUndoInfo(util.sortSelection)

    def mergeCrv(self):
        self.wrapUndoInfo(util.mergeCrv)
    
    def setHistoryNotInteresting(self):
        self.wrapUndoInfo(util.setHistoryNotInteresting)

    def createCtrlShape(self):
        sl_lis = cmds.ls(sl=1)
        if sl_lis:
            for sl in sl_lis:
                self.wrapUndoInfo(lambda: self.ctrlManager.createShape(self.cbb_setCtrlShape.currentText(),f'{sl}_ctrl', self.cbx_ctrlZeroGrp.isChecked(),sl))
        else:
            self.wrapUndoInfo(lambda: self.ctrlManager.createShape(self.cbb_setCtrlShape.currentText(),f'{self.cbb_setCtrlShape.currentText()}_ctrl', self.cbx_ctrlZeroGrp.isChecked()))
    
    def extractCtrlShape(self):
        sl_lis = cmds.ls(sl=1)
        if len(sl_lis)>1:
            cmds.warning(f'Can only extract one shape at a time, {sl_lis[0]} was extracted.')
        elif sl_lis:
            self.wrapUndoInfo(lambda: self.ctrlManager.extractShape( sl_lis[0], self.txt_ctrlName.text()))
        else:
            cmds.warning("Nothing selected")

    def setCtrlWidth(self):
        self.wrapUndoInfo(self.setCtrlWidthFunc)

    def setCtrlWidthFunc(self):
        sl_lis = cmds.ls(sl=1)
        if sl_lis:
            for sl in sl_lis:
                self.ctrlManager.setCurveWidth(self.sdr_width.value(),sl)

    def txt_widthUpdateEvt(self):
        value = 1
        try:
            value = int(self.txt_width.text())
            min_val, max_val = 1, 50

            # Clamp to range
            value = max(min(value, max_val), min_val)
            self.txt_width.setText(str(value))
        except ValueError:
            # Handle edge case where text can't be parsed
            self.txt_width.setText("1")
            print("Invalid input. Resetting to 1.")
        self.sdr_width.setValue(value)

    def sdr_widthUpdateEvt(self):
        value = self.sdr_width.value()
        self.txt_width.setText(f'{value}')

    def _getUserColorIndex(self):
        color_table = []
        for i in range(54):
            r, g, b = [int(c*255) for c in cmds.colorIndex( i, q=True )]
            color_table.append([r,g,b])
        return color_table
    
    def sdr_colorUpdateEvt(self):
        index = self.sdr_color.value()
        
        style = f"background-color: rgb({self.color_table[index][0]}, {self.color_table[index][1]}, {self.color_table[index][2]}); border: 1px solid #888;"
        self.lbl_colorIndicator.setStyleSheet(style)

    def setCtrlColorFunc(self):
        sl_lis = cmds.ls(sl=1)
        if sl_lis:
            for sl in sl_lis:
                self.ctrlManager.setCurveColor(self.sdr_color.value(), sl)

    def setCtrlColor(self):
        self.wrapUndoInfo(self.setCtrlColorFunc)

    def launchWireRigUI(self):
        rig.wireRigUI()

    def launchTwistJntUI(self):
        rig.twistJntUI()

    def launchlocOnEdgeUI(self):
        rig.placeLocUI()

    def attachFlc(self):
        self.wrapUndoInfo(rig.attachFlc)

def openWindow():
    """
    ID Maya and attach tool window.
    """
    # Maya uses this so it should always return True
    if QtWidgets.QApplication.instance():
        # Id any current instances of tool and destroy
        for win in (QtWidgets.QApplication.allWindows()):
            if 'cwToolsWindow' in win.objectName(): # update this name to match name below
                win.destroy()

    #QtWidgets.QApplication(sys.argv)
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(int(mayaMainWindowPtr), QtWidgets.QWidget)
    CWToolsMainUI.window = CWToolsMainUI(parent = mayaMainWindow)
    CWToolsMainUI.window.setObjectName('cwToolsWindow') # code above uses this to ID any existing windows
    CWToolsMainUI.window.show()
    
openWindow()