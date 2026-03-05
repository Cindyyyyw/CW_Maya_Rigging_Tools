import maya.cmds as cmds
import json
import math

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance

import maya.OpenMayaUI as omui


path = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/facialRig/ARFaceAnchor.json'


# ─────────────────────────────────────────────────────────────────────────────
#  Backend
# ─────────────────────────────────────────────────────────────────────────────

class BSBuilder:
    def __init__(self, face_geo, blendshape_name='', transform_step=200, generate_side=True):
        self.face_geo = face_geo
        self.blendshape_name = blendshape_name
        self.blendShape_names = []
        self.blendShape_grp = []
        self.transform_step = transform_step
        self.generate_side = generate_side
        self.default_side = 'Left'
        self.loadFaceAnchor()

    def loadFaceAnchor(self, filter_groups=None):
        """Load face anchors from JSON.

        Args:
            filter_groups (dict | None): {group_name: [anchor_name, ...]}
                When provided only the listed groups/anchors are loaded.
                Pass None to load everything.
        """
        self.blendShape_names = []
        self.blendShape_grp = []
        with open(path, 'r') as f:
            self.blendShapeData = json.load(f)
            for group, name_array in self.blendShapeData['ARFaceAnchor'].items():
                if filter_groups is not None:
                    if group not in filter_groups:
                        continue
                    filtered = [n for n in name_array if n in filter_groups[group]]
                    if not filtered:
                        continue
                    self.blendShape_names.extend(filtered)
                    self.blendShape_grp.append(filtered)
                else:
                    self.blendShape_names.extend(name_array)
                    self.blendShape_grp.append(name_array)

    def _prepare_source(self):
        """Return (mesh_name, is_temp).

        If the source has any locked transform channels or construction history,
        a clean temp duplicate is created outside the undo queue so it does not
        pollute Ctrl+Z.  The caller is responsible for deleting the temp (also
        outside the undo queue) once it is no longer needed.
        """
        transform_attrs = ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz')

        has_locked = any(
            cmds.getAttr(f'{self.face_geo}.{a}', lock=True)
            for a in transform_attrs
        )
        has_history = bool(cmds.listHistory(self.face_geo, pruneDagObjects=True))

        if not has_locked and not has_history:
            return self.face_geo, False

        # Build the temp outside of Maya's undo queue so it is invisible to Ctrl+Z
        cmds.undoInfo(stateWithoutFlush=False)
        try:
            temp = cmds.duplicate(self.face_geo, n=self.face_geo + '_BSBuilder_tmp')[0]
            cmds.delete(temp, constructionHistory=True)
            for attr in transform_attrs:
                cmds.setAttr(f'{temp}.{attr}', lock=False)
        finally:
            cmds.undoInfo(stateWithoutFlush=True)

        return temp, True

    def generateBSMesh(self):
        prefix = (self.blendshape_name + '_') if self.blendshape_name else ''

        source, is_temp = self._prepare_source()

        cmds.undoInfo(openChunk=True, chunkName='BSBuilder_generateBSMesh')
        try:
            for i, group in enumerate(self.blendShape_grp):
                for j, anchor in enumerate(group):
                    tx = self.transform_step * (j % 3) + i * 5 * self.transform_step
                    ty = self.transform_step * math.floor(j / 3)

                    if self.generate_side and anchor.endswith('_DIR_'):
                        left_name = prefix + anchor[:-5] + 'Left'
                        right_name = prefix + anchor[:-5] + 'Right'
                        geo_left = cmds.duplicate(source, n=left_name)
                        cmds.xform(geo_left, translation=(tx, ty, 0))
                        geo_right = cmds.duplicate(source, n=right_name)
                        cmds.xform(geo_right, translation=(tx, ty, -self.transform_step * 3))
                        continue

                    geo = cmds.duplicate(source, n=prefix + anchor)
                    cmds.xform(geo, translation=(tx, ty, 0))
        finally:
            cmds.undoInfo(closeChunk=True)
            if is_temp:
                # Delete temp outside the undo queue for the same reason it was created there
                cmds.undoInfo(stateWithoutFlush=False)
                try:
                    cmds.delete(source)
                finally:
                    cmds.undoInfo(stateWithoutFlush=True)


# ─────────────────────────────────────────────────────────────────────────────
#  UI helpers
# ─────────────────────────────────────────────────────────────────────────────

def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    try:
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  UI
# ─────────────────────────────────────────────────────────────────────────────

class BSBuilderUI(QtWidgets.QDialog):
    WINDOW_TITLE = 'ARKit BlendShape Builder'

    def __init__(self, parent=None):
        if parent is None:
            parent = _maya_main_window()
        super(BSBuilderUI, self).__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(440)
        self.setWindowFlags(
            self.windowFlags()
            ^ QtCore.Qt.WindowContextHelpButtonHint
            | QtCore.Qt.WindowStaysOnTopHint
        )

        self._anchor_data = {}          # {group: [anchors]}
        self._group_checkboxes = {}     # {group: QCheckBox}
        self._anchor_checkboxes = {}    # {group: {anchor: QCheckBox}}
        self._anchor_widgets = {}       # {group: QWidget}  (the indented container)

        self._load_anchor_data()
        self._build_ui()

    # ── data ──────────────────────────────────────────────────────────────────

    def _load_anchor_data(self):
        with open(path, 'r') as f:
            data = json.load(f)
        self._anchor_data = data.get('ARFaceAnchor', {})

    # ── build layout ──────────────────────────────────────────────────────────

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        main_layout.addWidget(self._build_mesh_group())
        main_layout.addWidget(self._build_side_group())
        main_layout.addWidget(self._build_anchors_group())

        build_btn = QtWidgets.QPushButton('Build BlendShape Meshes')
        build_btn.setFixedHeight(36)
        build_btn.setStyleSheet('font-weight: bold; font-size: 13px;')
        build_btn.clicked.connect(self._on_build)
        main_layout.addWidget(build_btn)

    # ── Mesh & Settings group ─────────────────────────────────────────────────

    def _build_mesh_group(self):
        group = QtWidgets.QGroupBox('Mesh & BlendShape Settings')
        layout = QtWidgets.QFormLayout(group)
        layout.setSpacing(6)

        # Face geometry row
        geo_row = QtWidgets.QHBoxLayout()
        self.geo_field = QtWidgets.QLineEdit()
        self.geo_field.setPlaceholderText('Select or type mesh name...')
        load_btn = QtWidgets.QPushButton('<<')
        load_btn.setFixedWidth(32)
        load_btn.setToolTip('Load selected object from Maya viewport')
        load_btn.clicked.connect(self._load_selected_geo)
        geo_row.addWidget(self.geo_field)
        geo_row.addWidget(load_btn)
        layout.addRow('Face Mesh:', geo_row)

        # BlendShape name
        self.bs_name_field = QtWidgets.QLineEdit()
        self.bs_name_field.setPlaceholderText('e.g. CharacterName_face  (optional prefix)')
        layout.addRow('BlendShape Name:', self.bs_name_field)

        # Transform step
        self.transform_spin = QtWidgets.QSpinBox()
        self.transform_spin.setRange(1, 99999)
        self.transform_spin.setValue(200)
        self.transform_spin.setSuffix('  units')
        self.transform_spin.setToolTip(
            'Spacing between generated blendshape meshes in world units'
        )
        layout.addRow('Transform Step:', self.transform_spin)

        return group

    # ── Side generation group ─────────────────────────────────────────────────

    def _build_side_group(self):
        group = QtWidgets.QGroupBox('Side Generation')
        layout = QtWidgets.QVBoxLayout(group)
        layout.setSpacing(4)

        self.radio_both = QtWidgets.QRadioButton(
            'Generate both Left && Right meshes'
        )
        self.radio_both.setChecked(True)
        self.radio_both.setToolTip(
            'For _DIR_ anchors, immediately duplicate into separate Left and Right meshes.'
        )

        self.radio_single = QtWidgets.QRadioButton(
            'Generate single mesh  \u2014  mirror / weight-mask later  (upcoming)'
        )
        self.radio_single.setToolTip(
            'Generate one mesh per directional anchor.\n'
            'Left/Right split will be handled via mirror blendshape or weight masking (coming soon).'
        )
        self.radio_single.setEnabled(True)   # visually available; no-op for now

        btn_grp = QtWidgets.QButtonGroup(self)
        btn_grp.addButton(self.radio_both)
        btn_grp.addButton(self.radio_single)

        layout.addWidget(self.radio_both)
        layout.addWidget(self.radio_single)
        return group

    # ── Face Anchors group ────────────────────────────────────────────────────

    def _build_anchors_group(self):
        outer = QtWidgets.QGroupBox('Face Anchors')
        outer_layout = QtWidgets.QVBoxLayout(outer)
        outer_layout.setSpacing(6)

        # Select all / none bar
        bar = QtWidgets.QHBoxLayout()
        sel_all = QtWidgets.QPushButton('Select All')
        sel_none = QtWidgets.QPushButton('Select None')
        sel_all.setFixedHeight(22)
        sel_none.setFixedHeight(22)
        sel_all.clicked.connect(lambda: self._set_all_groups(True))
        sel_none.clicked.connect(lambda: self._set_all_groups(False))
        bar.addWidget(sel_all)
        bar.addWidget(sel_none)
        bar.addStretch()
        outer_layout.addLayout(bar)

        # Scrollable area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setMinimumHeight(260)

        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(2)
        scroll_layout.setContentsMargins(4, 4, 4, 4)

        for group, anchors in self._anchor_data.items():
            self._build_anchor_group(scroll_layout, group, anchors)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        outer_layout.addWidget(scroll)
        return outer

    def _build_anchor_group(self, parent_layout, group_name, anchors):
        """One collapsible group: bold checkbox header + indented anchor checkboxes."""
        container = QtWidgets.QWidget()
        c_layout = QtWidgets.QVBoxLayout(container)
        c_layout.setContentsMargins(0, 2, 0, 0)
        c_layout.setSpacing(1)

        # Group header
        group_cb = QtWidgets.QCheckBox(group_name)
        group_cb.setChecked(True)
        font = group_cb.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        group_cb.setFont(font)
        self._group_checkboxes[group_name] = group_cb
        c_layout.addWidget(group_cb)

        # Individual anchors (indented)
        anchor_container = QtWidgets.QWidget()
        a_layout = QtWidgets.QVBoxLayout(anchor_container)
        a_layout.setContentsMargins(28, 0, 0, 4)
        a_layout.setSpacing(1)
        self._anchor_checkboxes[group_name] = {}

        for anchor in anchors:
            display = anchor.replace('_DIR_', '  \u2194  (L / R)')
            cb = QtWidgets.QCheckBox(display)
            cb.setChecked(True)
            cb.setProperty('anchor_name', anchor)
            self._anchor_checkboxes[group_name][anchor] = cb
            a_layout.addWidget(cb)

        self._anchor_widgets[group_name] = anchor_container
        c_layout.addWidget(anchor_container)

        # Wire group toggle → enable/disable individual row
        group_cb.toggled.connect(
            lambda checked, w=anchor_container: w.setEnabled(checked)
        )

        parent_layout.addWidget(container)

        # Hairline separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        parent_layout.addWidget(line)

    # ── slots ─────────────────────────────────────────────────────────────────

    def _load_selected_geo(self):
        sel = cmds.ls(selection=True, long=False)
        if sel:
            self.geo_field.setText(sel[0])
        else:
            cmds.warning('ARKit BS Builder: nothing selected – please select a mesh first.')

    def _set_all_groups(self, state):
        for cb in self._group_checkboxes.values():
            cb.setChecked(state)

    def _get_selected_anchors(self):
        """Return {group: [anchor, ...]} for all checked items."""
        result = {}
        for group, group_cb in self._group_checkboxes.items():
            if not group_cb.isChecked():
                continue
            selected = [
                anchor
                for anchor, cb in self._anchor_checkboxes[group].items()
                if cb.isChecked()
            ]
            if selected:
                result[group] = selected
        return result

    def _on_build(self):
        face_geo = self.geo_field.text().strip()
        if not face_geo:
            QtWidgets.QMessageBox.warning(
                self, 'Missing Input', 'Please specify a face mesh.'
            )
            return
        if not cmds.objExists(face_geo):
            QtWidgets.QMessageBox.warning(
                self, 'Object Not Found',
                f"'{face_geo}' does not exist in the current scene."
            )
            return

        selected_anchors = self._get_selected_anchors()
        if not selected_anchors:
            QtWidgets.QMessageBox.warning(
                self, 'Nothing Selected',
                'Please enable at least one face anchor group.'
            )
            return

        builder = BSBuilder(
            face_geo=face_geo,
            blendshape_name=self.bs_name_field.text().strip(),
            transform_step=self.transform_spin.value(),
            generate_side=self.radio_both.isChecked(),
        )
        builder.loadFaceAnchor(filter_groups=selected_anchors)
        builder.generateBSMesh()

        total = len(builder.blendShape_names)
        cmds.inViewMessage(
            amg=f'<hl>Done!</hl>  {total} blendshape mesh(es) generated.',
            pos='midCenter',
            fade=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Launch
# ─────────────────────────────────────────────────────────────────────────────

_window_instance = None


def show():
    """Open (or raise) the ARKit BlendShape Builder window."""
    global _window_instance
    try:
        _window_instance.close()
        _window_instance.deleteLater()
    except Exception:
        pass
    _window_instance = BSBuilderUI()
    _window_instance.show()


# To open: run  show()  in Maya's Script Editor
show()
