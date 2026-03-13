"""ARKit BlendShape Builder — Qt UI (BSBuilderUI and supporting widgets).

Imports backend classes from bs_builder and muscle_joints in the same directory.
"""

import sys
import os

# Add this file's directory to sys.path so sibling modules can be imported,
# even when the file is loaded via Maya's Script Editor (where __file__ may
# not be set and the package directory might not be on sys.path yet).
try:
    _PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _PACKAGE_DIR = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/facialRig'

if _PACKAGE_DIR not in sys.path:
    sys.path.insert(0, _PACKAGE_DIR)

import maya.cmds as cmds
import json

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance

import maya.OpenMayaUI as omui

from bs_builder import (
    BSBuilder,
    check_symmetry,
    flip_target,
    split_by_weight_mask,
    path,
    _maya_main_window,
)
from muscle_joints import MuscleJointBuilder, _muscle_json_default


# ─────────────────────────────────────────────────────────────────────────────
#  Shared UI helpers
# ─────────────────────────────────────────────────────────────────────────────

class _CollapsibleSection(QtWidgets.QWidget):
    """Accordion-style collapsible panel used in the Muscle Joints tab.

    Usage::
        sec = _CollapsibleSection('My Title', parent_widget)
        layout = QtWidgets.QVBoxLayout(sec.body())
        layout.addWidget(some_widget)
        parent_layout.addWidget(sec)
    """

    def __init__(self, title, parent=None, expanded=True):
        super(_CollapsibleSection, self).__init__(parent)

        # ── Toggle button ────────────────────────────────────────────────────
        self._btn = QtWidgets.QToolButton()
        self._btn.setCheckable(True)
        self._btn.setChecked(expanded)
        self._btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self._btn.setArrowType(
            QtCore.Qt.DownArrow if expanded else QtCore.Qt.RightArrow
        )
        self._btn.setText(f'  {title}')
        self._btn.setStyleSheet('QToolButton { border: none; font-weight: bold; }')
        self._btn.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        # Horizontal rule next to the title
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        hdr = QtWidgets.QHBoxLayout()
        hdr.setContentsMargins(0, 4, 0, 2)
        hdr.setSpacing(4)
        hdr.addWidget(self._btn)
        hdr.addWidget(line)

        # ── Body ─────────────────────────────────────────────────────────────
        self._body = QtWidgets.QWidget()

        body_wrap = QtWidgets.QVBoxLayout()
        body_wrap.setContentsMargins(10, 2, 0, 6)
        body_wrap.setSpacing(0)
        body_wrap.addWidget(self._body)

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(hdr)
        root.addLayout(body_wrap)

        self._body.setVisible(expanded)
        self._btn.clicked.connect(self._on_toggle)

    # ── slots ─────────────────────────────────────────────────────────────────
    def _on_toggle(self, checked):
        self._body.setVisible(checked)
        self._btn.setArrowType(
            QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow
        )

    # ── public ────────────────────────────────────────────────────────────────
    def body(self):
        """Return the content QWidget; install a layout on it to add children."""
        return self._body


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
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(10, 10, 10, 10)

        tabs = QtWidgets.QTabWidget()

        # ── Tab 1: Build ──────────────────────────────────────────────────────
        tab1 = QtWidgets.QWidget()
        t1 = QtWidgets.QVBoxLayout(tab1)
        t1.setSpacing(8)
        t1.setContentsMargins(0, 8, 0, 0)
        t1.addWidget(self._build_mesh_group())
        t1.addWidget(self._build_side_group())
        t1.addWidget(self._build_anchors_group())

        build_btn = QtWidgets.QPushButton('Build BlendShape Meshes')
        build_btn.setFixedHeight(36)
        build_btn.setStyleSheet('font-weight: bold; font-size: 13px;')
        build_btn.clicked.connect(self._on_build)
        t1.addWidget(build_btn)

        tabs.addTab(tab1, 'Build')

        # ── Tab 2: Mirror / Split ─────────────────────────────────────────────
        tabs.addTab(self._build_tab2(), 'Flip / Split')

        # ── Tab 3: Facial Muscle Joints ───────────────────────────────────────
        tabs.addTab(self._build_tab3(), 'Muscle Joints')

        main_layout.addWidget(tabs)

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
            'Generate single mesh  \u2014  flip / weight-mask later  (upcoming)'
        )
        self.radio_single.setToolTip(
            'Generate one mesh per directional anchor.\n'
            'Left/Right split will be handled via flip target or weight masking (coming soon).'
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

    # ── Tab 2 builder ──────────────────────────────────────────────────────────

    def _build_tab2(self):
        """Build the Flip / Split tab."""
        self._is_symmetric    = None  # True | False | None (not yet checked)
        self._midline_edges   = []    # confirmed edge indices (asymmetric case)
        self._midline_indices = []    # midline vertex indices derived from edges

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 8, 0, 0)

        # ── Step 1: Symmetry check ────────────────────────────────────────────
        sym_box = QtWidgets.QGroupBox('Step 1 — Symmetry Check')
        sym_layout = QtWidgets.QVBoxLayout(sym_box)

        src_row = QtWidgets.QHBoxLayout()
        src_lbl = QtWidgets.QLabel('Base Mesh:')
        src_lbl.setFixedWidth(72)
        self.t2_src_field = QtWidgets.QLineEdit()
        self.t2_src_field.setPlaceholderText('Source (neutral) mesh…')
        src_btn = QtWidgets.QPushButton('<<')
        src_btn.setFixedWidth(32)
        src_btn.setToolTip('Load selected mesh from viewport')
        src_btn.clicked.connect(self._t2_load_src)
        src_row.addWidget(src_lbl)
        src_row.addWidget(self.t2_src_field)
        src_row.addWidget(src_btn)
        sym_layout.addLayout(src_row)

        check_row = QtWidgets.QHBoxLayout()
        self.t2_check_btn = QtWidgets.QPushButton('Check Symmetry')
        self.t2_check_btn.clicked.connect(self._t2_check_symmetry)
        self.t2_sym_label = QtWidgets.QLabel('—')
        self.t2_sym_label.setMinimumWidth(200)
        check_row.addWidget(self.t2_check_btn)
        check_row.addWidget(self.t2_sym_label)
        check_row.addStretch()
        sym_layout.addLayout(check_row)

        # Midline override — only shown when mesh is asymmetric
        self.t2_midline_widget = QtWidgets.QWidget()
        ml_v = QtWidgets.QVBoxLayout(self.t2_midline_widget)
        ml_v.setContentsMargins(0, 4, 0, 0)
        ml_v.setSpacing(4)
        warn_lbl = QtWidgets.QLabel(
            '⚠  Asymmetric mesh detected.\n'
            '    Select the midline edges on the base mesh, then click Confirm.'
        )
        warn_lbl.setStyleSheet('color: #E67E22;')
        ml_v.addWidget(warn_lbl)
        ml_btn_row = QtWidgets.QHBoxLayout()
        self.t2_sel_mid_btn     = QtWidgets.QPushButton('Select Midline Edges')
        self.t2_confirm_mid_btn = QtWidgets.QPushButton('Confirm')
        self.t2_mid_count_lbl   = QtWidgets.QLabel('0 edges stored')
        self.t2_sel_mid_btn.clicked.connect(self._t2_enter_midline_select)
        self.t2_confirm_mid_btn.clicked.connect(self._t2_confirm_midline)
        ml_btn_row.addWidget(self.t2_sel_mid_btn)
        ml_btn_row.addWidget(self.t2_confirm_mid_btn)
        ml_btn_row.addWidget(self.t2_mid_count_lbl)
        ml_btn_row.addStretch()
        ml_v.addLayout(ml_btn_row)
        self.t2_midline_widget.setVisible(False)
        sym_layout.addWidget(self.t2_midline_widget)

        layout.addWidget(sym_box)

        # ── Step 2: Flip axis ─────────────────────────────────────────────────
        axis_box = QtWidgets.QGroupBox('Step 2 — Flip Axis')
        axis_layout = QtWidgets.QHBoxLayout(axis_box)
        self.t2_axis_x = QtWidgets.QRadioButton('X')
        self.t2_axis_y = QtWidgets.QRadioButton('Y')
        self.t2_axis_z = QtWidgets.QRadioButton('Z')
        self.t2_axis_x.setChecked(True)
        axis_bg = QtWidgets.QButtonGroup(self)
        for rb in (self.t2_axis_x, self.t2_axis_y, self.t2_axis_z):
            axis_bg.addButton(rb)
            axis_layout.addWidget(rb)
        axis_layout.addStretch()
        layout.addWidget(axis_box)

        # ── Step 3: Mode ──────────────────────────────────────────────────────
        self.t2_mode_box = QtWidgets.QGroupBox('Step 3 — Mode')
        mode_layout = QtWidgets.QVBoxLayout(self.t2_mode_box)

        self.t2_mode_flip  = QtWidgets.QRadioButton('Flip Target')
        flip_desc = QtWidgets.QLabel(
            '      Duplicates the original as-is, then flips a second copy\n'
            '      using blendShape flipTarget across the chosen axis.'
        )
        flip_desc.setStyleSheet('color: gray; font-size: 11px;')

        # Name replacement fields — shown only when Flip Target is active
        self.t2_flip_opts = QtWidgets.QWidget()
        fo = QtWidgets.QFormLayout(self.t2_flip_opts)
        fo.setContentsMargins(24, 4, 0, 4)
        fo.setSpacing(4)
        self.t2_find_field = QtWidgets.QLineEdit('_DIR_')
        self.t2_find_field.setToolTip(
            'Substring in the mesh name to replace when renaming the outputs'
        )
        repl_row = QtWidgets.QHBoxLayout()
        self.t2_repl_orig_field = QtWidgets.QLineEdit('Left')
        self.t2_repl_flip_field = QtWidgets.QLineEdit('Right')
        self.t2_repl_orig_field.setToolTip('Replacement for the pre-flip (original) copy')
        self.t2_repl_flip_field.setToolTip('Replacement for the flipped copy')
        repl_row.addWidget(self.t2_repl_orig_field)
        repl_row.addWidget(QtWidgets.QLabel('/'))
        repl_row.addWidget(self.t2_repl_flip_field)
        fo.addRow('Find:', self.t2_find_field)
        fo.addRow('Replace (orig / flip):', repl_row)

        self.t2_mode_split = QtWidgets.QRadioButton('Split by Weight Mask')
        split_desc = QtWidgets.QLabel(
            '      Creates Left (+axis) and Right (-axis) duplicates of the base\n'
            '      mesh, inputs the selected target as a blendShape, then masks\n'
            '      each half by vertex position.  Midline verts receive 0.5.'
        )
        split_desc.setStyleSheet('color: gray; font-size: 11px;')

        self.t2_mode_flip.setChecked(True)
        mode_bg = QtWidgets.QButtonGroup(self)
        mode_bg.addButton(self.t2_mode_flip)
        mode_bg.addButton(self.t2_mode_split)

        mode_layout.addWidget(self.t2_mode_flip)
        mode_layout.addWidget(flip_desc)
        mode_layout.addWidget(self.t2_flip_opts)
        mode_layout.addWidget(self.t2_mode_split)
        mode_layout.addWidget(split_desc)

        # Show/hide name-replacement options with the Flip Target radio
        self.t2_mode_flip.toggled.connect(self.t2_flip_opts.setVisible)

        # Locked until symmetry is confirmed
        self.t2_mode_box.setEnabled(False)
        layout.addWidget(self.t2_mode_box)

        layout.addStretch()

        # ── Execute ───────────────────────────────────────────────────────────
        self.t2_exec_btn = QtWidgets.QPushButton('Execute on Selected Meshes')
        self.t2_exec_btn.setFixedHeight(36)
        self.t2_exec_btn.setStyleSheet('font-weight: bold; font-size: 13px;')
        self.t2_exec_btn.setEnabled(False)
        self.t2_exec_btn.clicked.connect(self._t2_execute)
        layout.addWidget(self.t2_exec_btn)

        return tab

    # ── Tab 3 builder ──────────────────────────────────────────────────────────

    def _build_tab3(self):
        """Build the Facial Muscle Joints tab."""
        # State
        self._t3_guide_grp      = None
        self._t3_joints_grp     = None
        self._t3_face_root_jnt  = None
        self._t3_append_local_t = None
        self._t3_append_local_r = None
        self._t3_muscle_data        = {}
        self._t3_group_checkboxes   = {}
        self._t3_anchor_checkboxes  = {}
        self._t3_anchor_widgets     = {}

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 8, 0, 0)

        # ── Section 1: Setup ─────────────────────────────────────────────────
        setup_box = _CollapsibleSection('Setup', self)
        setup_form = QtWidgets.QFormLayout(setup_box.body())
        setup_form.setSpacing(6)

        geo_row = QtWidgets.QHBoxLayout()
        self.t3_geo_field = QtWidgets.QLineEdit()
        self.t3_geo_field.setPlaceholderText('Select or type mesh name...')
        t3_geo_btn = QtWidgets.QPushButton('<<')
        t3_geo_btn.setFixedWidth(32)
        t3_geo_btn.setToolTip('Load selected mesh from viewport')
        t3_geo_btn.clicked.connect(self._t3_load_face_geo)
        geo_row.addWidget(self.t3_geo_field)
        geo_row.addWidget(t3_geo_btn)
        setup_form.addRow('Face Mesh:', geo_row)

        jnt_row = QtWidgets.QHBoxLayout()
        self.t3_jnt_field = QtWidgets.QLineEdit()
        self.t3_jnt_field.setPlaceholderText('Select or type joint name...')
        t3_jnt_btn = QtWidgets.QPushButton('<<')
        t3_jnt_btn.setFixedWidth(32)
        t3_jnt_btn.setToolTip('Load selected joint from viewport')
        t3_jnt_btn.clicked.connect(self._t3_load_head_jnt)
        jnt_row.addWidget(self.t3_jnt_field)
        jnt_row.addWidget(t3_jnt_btn)
        setup_form.addRow('Head Joint:', jnt_row)

        self.t3_prefix_field = QtWidgets.QLineEdit()
        self.t3_prefix_field.setPlaceholderText('e.g. CharName  (optional)')
        setup_form.addRow('Prefix:', self.t3_prefix_field)

        json_row = QtWidgets.QHBoxLayout()
        self.t3_json_field = QtWidgets.QLineEdit()
        self.t3_json_field.setPlaceholderText('Path to FacialMuscleJoints.json...')
        t3_json_browse = QtWidgets.QPushButton('Browse\u2026')
        t3_json_browse.setFixedWidth(72)
        t3_json_browse.clicked.connect(self._t3_browse_json)
        t3_load_json_btn = QtWidgets.QPushButton('Load JSON')
        t3_load_json_btn.setFixedWidth(80)
        t3_load_json_btn.clicked.connect(
            lambda: self._t3_reload_json(self.t3_json_field.text().strip())
        )
        json_row.addWidget(self.t3_json_field)
        json_row.addWidget(t3_json_browse)
        json_row.addWidget(t3_load_json_btn)
        setup_form.addRow('JSON:', json_row)

        setup_desc = QtWidgets.QLabel(
            'Specify the face mesh for follicle attachment and the head joint that '
            'defines the local space for all guide positions.'
        )
        setup_desc.setWordWrap(True)
        setup_desc.setStyleSheet('color: gray; font-size: 11px;')
        setup_form.addRow(setup_desc)
        layout.addWidget(setup_box)

        # ── Section 2: Joint Selection ───────────────────────────────────────
        sel_box = _CollapsibleSection('Joint Selection', self)
        sel_layout = QtWidgets.QVBoxLayout(sel_box.body())
        sel_layout.setSpacing(4)

        side_row = QtWidgets.QHBoxLayout()
        self.t3_radio_both   = QtWidgets.QRadioButton('Generate both L/R')
        self.t3_radio_single = QtWidgets.QRadioButton('Single, mirror later')
        self.t3_radio_both.setChecked(True)
        side_bg = QtWidgets.QButtonGroup(self)
        side_bg.addButton(self.t3_radio_both)
        side_bg.addButton(self.t3_radio_single)
        side_row.addWidget(self.t3_radio_both)
        side_row.addWidget(self.t3_radio_single)
        side_row.addStretch()
        sel_layout.addLayout(side_row)

        axis_row = QtWidgets.QHBoxLayout()
        axis_lbl = QtWidgets.QLabel('Mirror plane:')
        axis_lbl.setFixedWidth(80)
        self.t3_radio_plane_yz = QtWidgets.QRadioButton('YZ')
        self.t3_radio_plane_xz = QtWidgets.QRadioButton('XZ')
        self.t3_radio_plane_xy = QtWidgets.QRadioButton('XY')
        self.t3_radio_plane_yz.setChecked(True)   # default: face centred on YZ, L/R along X
        self.t3_axis_bg = QtWidgets.QButtonGroup(self)
        self.t3_axis_bg.addButton(self.t3_radio_plane_yz, 0)  # negate world X
        self.t3_axis_bg.addButton(self.t3_radio_plane_xz, 1)  # negate world Y
        self.t3_axis_bg.addButton(self.t3_radio_plane_xy, 2)  # negate world Z
        axis_row.addWidget(axis_lbl)
        axis_row.addWidget(self.t3_radio_plane_yz)
        axis_row.addWidget(self.t3_radio_plane_xz)
        axis_row.addWidget(self.t3_radio_plane_xy)
        axis_row.addStretch()
        sel_layout.addLayout(axis_row)

        self.t3_check_uniform_x = QtWidgets.QCheckBox(
            'Same X direction on both sides  (flips R orientation 180\u00b0 on Z)'
        )
        self.t3_check_uniform_x.setChecked(False)
        self.t3_check_uniform_x.setToolTip(
            'When enabled the R-side locator is rotated an extra 180\u00b0 around its\n'
            'local Z axis so both sides\u2019 X axes point in the same world direction.\n'
            'Use this when you want controls on L and R to translate identically\n'
            'along their own X axis (e.g. both move "outward").\n\n'
            'When disabled (default) the orientations are a true mirror image,\n'
            'matching Maya\u2019s standard joint mirror behaviour.'
        )
        sel_layout.addWidget(self.t3_check_uniform_x)

        sel_bar = QtWidgets.QHBoxLayout()
        t3_sel_all  = QtWidgets.QPushButton('Select All')
        t3_sel_none = QtWidgets.QPushButton('Select None')
        t3_sel_all.setFixedHeight(22)
        t3_sel_none.setFixedHeight(22)
        t3_sel_all.clicked.connect(lambda: self._t3_set_all_groups(True))
        t3_sel_none.clicked.connect(lambda: self._t3_set_all_groups(False))
        sel_bar.addWidget(t3_sel_all)
        sel_bar.addWidget(t3_sel_none)
        sel_bar.addStretch()
        sel_layout.addLayout(sel_bar)

        self._t3_scroll = QtWidgets.QScrollArea()
        self._t3_scroll.setWidgetResizable(True)
        self._t3_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._t3_scroll.setMinimumHeight(144)
        self._t3_scroll_widget = QtWidgets.QWidget()
        self._t3_scroll_layout = QtWidgets.QVBoxLayout(self._t3_scroll_widget)
        self._t3_scroll_layout.setSpacing(2)
        self._t3_scroll_layout.setContentsMargins(4, 4, 4, 4)
        self._t3_scroll_layout.addStretch()
        self._t3_scroll.setWidget(self._t3_scroll_widget)
        sel_layout.addWidget(self._t3_scroll)

        sel_desc = QtWidgets.QLabel(
            'Select which muscle joints to create. '
            'Positions are relative to the head joint.'
        )
        sel_desc.setWordWrap(True)
        sel_desc.setStyleSheet('color: gray; font-size: 11px;')
        sel_layout.addWidget(sel_desc)
        layout.addWidget(sel_box)

        # ── Section 3: Stage 1 – Guide Locators ──────────────────────────────
        guide_box = _CollapsibleSection('Stage 1 \u2014 Guide Locators', self)
        guide_layout = QtWidgets.QVBoxLayout(guide_box.body())
        guide_layout.setSpacing(6)

        guide_desc = QtWidgets.QLabel(
            'Creates or adds locators at predefined positions (in head joint space) '
            'with Local Rotation Axes visible. Existing guides are preserved — only '
            'new entries are added. Move them to fine-tune placement before building joints.'
        )
        guide_desc.setWordWrap(True)
        guide_desc.setStyleSheet('color: gray; font-size: 11px;')
        guide_layout.addWidget(guide_desc)

        guide_btn_row = QtWidgets.QHBoxLayout()
        t3_create_guides_btn = QtWidgets.QPushButton('Create / Add Guide Locators')
        t3_clear_guides_btn  = QtWidgets.QPushButton('Clear Guides')
        t3_create_guides_btn.clicked.connect(self._t3_create_guides)
        t3_clear_guides_btn.clicked.connect(self._t3_clear_guides)
        guide_btn_row.addWidget(t3_create_guides_btn)
        guide_btn_row.addWidget(t3_clear_guides_btn)
        guide_layout.addLayout(guide_btn_row)
        layout.addWidget(guide_box)

        # ── Section 4: Stage 2 – Build Joints ────────────────────────────────
        build_box = _CollapsibleSection('Stage 2 \u2014 Build Joints', self)
        build_layout = QtWidgets.QVBoxLayout(build_box.body())
        build_layout.setSpacing(6)

        build_desc = QtWidgets.QLabel(
            'Reads current guide locator positions, creates joints with controls '
            'and follicles. Each offset group is follicle-pinned to the face mesh '
            'so controls follow blendshape deformation.'
        )
        build_desc.setWordWrap(True)
        build_desc.setStyleSheet('color: gray; font-size: 11px;')
        build_layout.addWidget(build_desc)

        build_btn_row = QtWidgets.QHBoxLayout()
        t3_build_btn   = QtWidgets.QPushButton('Build from Guides')
        t3_rebuild_btn = QtWidgets.QPushButton('Rebuild')
        t3_build_btn.clicked.connect(self._t3_build_joints)
        t3_rebuild_btn.clicked.connect(self._t3_rebuild)
        build_btn_row.addWidget(t3_build_btn)
        build_btn_row.addWidget(t3_rebuild_btn)
        build_layout.addLayout(build_btn_row)
        layout.addWidget(build_box)

        # ── Section 5: View Switch ────────────────────────────────────────────
        view_box = _CollapsibleSection('View', self)
        view_layout = QtWidgets.QHBoxLayout(view_box.body())
        t3_show_guides_btn = QtWidgets.QPushButton('Show Guides')
        t3_show_joints_btn = QtWidgets.QPushButton('Show Joints')
        t3_show_guides_btn.clicked.connect(self._t3_show_guides)
        t3_show_joints_btn.clicked.connect(self._t3_show_joints)
        view_layout.addWidget(t3_show_guides_btn)
        view_layout.addWidget(t3_show_joints_btn)
        layout.addWidget(view_box)

        # ── Section 6: Append to JSON ─────────────────────────────────────────
        append_box = _CollapsibleSection('Append to JSON', self, expanded=False)
        append_form = QtWidgets.QFormLayout(append_box.body())
        append_form.setSpacing(6)

        append_desc = QtWidgets.QLabel(
            'Place a locator on the face, position it, then save it as a new joint '
            'definition. Positions are automatically converted to head-joint local '
            'space before writing.'
        )
        append_desc.setWordWrap(True)
        append_desc.setStyleSheet('color: gray; font-size: 11px;')
        append_form.addRow(append_desc)

        self.t3_append_name_field = QtWidgets.QLineEdit()
        self.t3_append_name_field.setPlaceholderText('e.g. browOuter_DIR_  or  noseTip')
        append_form.addRow('Name:', self.t3_append_name_field)

        group_row = QtWidgets.QHBoxLayout()
        self.t3_append_group_combo = QtWidgets.QComboBox()
        self.t3_append_group_combo.addItem('\u2014 choose group \u2014')
        self.t3_append_group_combo.addItem('New group\u2026')
        self.t3_append_newgroup_field = QtWidgets.QLineEdit()
        self.t3_append_newgroup_field.setPlaceholderText('New group name\u2026')
        self.t3_append_newgroup_field.setVisible(False)
        self.t3_append_group_combo.currentTextChanged.connect(
            self._t3_on_group_combo_changed
        )
        group_row.addWidget(self.t3_append_group_combo)
        group_row.addWidget(self.t3_append_newgroup_field)
        append_form.addRow('Group:', group_row)

        self.t3_append_local_t_lbl = QtWidgets.QLabel('\u2014')
        self.t3_append_local_r_lbl = QtWidgets.QLabel('\u2014')
        append_form.addRow('Local Translate:', self.t3_append_local_t_lbl)
        append_form.addRow('Local Rotate:',    self.t3_append_local_r_lbl)

        action_row = QtWidgets.QHBoxLayout()
        t3_get_btn   = QtWidgets.QPushButton('Get from Selection')
        t3_write_btn = QtWidgets.QPushButton('Write to JSON')
        t3_get_btn.clicked.connect(self._t3_get_from_selection)
        t3_write_btn.clicked.connect(self._t3_write_to_json)
        action_row.addWidget(t3_get_btn)
        action_row.addWidget(t3_write_btn)
        append_form.addRow(action_row)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        append_form.addRow(sep)

        loc_row = QtWidgets.QHBoxLayout()
        t3_loc_origin_btn = QtWidgets.QPushButton('Locator at World Origin')
        t3_loc_vert_btn   = QtWidgets.QPushButton('Locator at Selected Vertex')
        t3_loc_origin_btn.clicked.connect(self._t3_locator_at_origin)
        t3_loc_vert_btn.clicked.connect(self._t3_locator_at_vertex)
        loc_row.addWidget(t3_loc_origin_btn)
        loc_row.addWidget(t3_loc_vert_btn)
        append_form.addRow(loc_row)
        layout.addWidget(append_box)

        layout.addStretch()

        # Populate checkboxes and group combo from default JSON
        self.t3_json_field.setText(_muscle_json_default)
        self._t3_reload_json(_muscle_json_default)

        return tab

    def _build_t3_joint_group(self, parent_layout, group_name, entry_names):
        """One collapsible group for the Tab 3 joint checkbox area."""
        container = QtWidgets.QWidget()
        c_layout  = QtWidgets.QVBoxLayout(container)
        c_layout.setContentsMargins(0, 2, 0, 0)
        c_layout.setSpacing(1)

        group_cb = QtWidgets.QCheckBox(group_name)
        group_cb.setChecked(True)
        font = group_cb.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        group_cb.setFont(font)
        self._t3_group_checkboxes[group_name] = group_cb
        c_layout.addWidget(group_cb)

        anchor_container = QtWidgets.QWidget()
        a_layout = QtWidgets.QVBoxLayout(anchor_container)
        a_layout.setContentsMargins(28, 0, 0, 4)
        a_layout.setSpacing(1)
        self._t3_anchor_checkboxes[group_name] = {}

        for name in entry_names:
            display = name.replace('_DIR_', '  \u2194  (L / R)')
            cb = QtWidgets.QCheckBox(display)
            cb.setChecked(True)
            cb.setProperty('anchor_name', name)
            self._t3_anchor_checkboxes[group_name][name] = cb
            a_layout.addWidget(cb)

        self._t3_anchor_widgets[group_name] = anchor_container
        c_layout.addWidget(anchor_container)

        group_cb.toggled.connect(
            lambda checked, w=anchor_container: w.setEnabled(checked)
        )
        parent_layout.addWidget(container)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        parent_layout.addWidget(line)

    # ── Tab 3 slots ────────────────────────────────────────────────────────────

    def _t3_load_face_geo(self):
        sel = cmds.ls(selection=True, long=False)
        if sel:
            self.t3_geo_field.setText(sel[0])
        else:
            cmds.warning('Muscle Joints: nothing selected.')

    def _t3_load_head_jnt(self):
        sel = cmds.ls(selection=True, long=False)
        if sel:
            self.t3_jnt_field.setText(sel[0])
        else:
            cmds.warning('Muscle Joints: nothing selected.')

    def _t3_browse_json(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select Muscle Joint JSON', '', 'JSON Files (*.json)'
        )
        if file_path:
            self.t3_json_field.setText(file_path)
            self._t3_reload_json(file_path)

    def _t3_reload_json(self, json_path):
        if not json_path or not os.path.isfile(json_path):
            return
        try:
            with open(json_path, 'r') as f:
                raw = json.load(f)
            self._t3_muscle_data = raw.get('FacialMuscleJoints', {})
        except Exception as e:
            cmds.warning(f'Muscle Joints: failed to load JSON — {e}')
            return

        # Clear and rebuild checkbox area
        self._t3_group_checkboxes  = {}
        self._t3_anchor_checkboxes = {}
        self._t3_anchor_widgets    = {}
        while self._t3_scroll_layout.count():
            item = self._t3_scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for group, entries in self._t3_muscle_data.items():
            names = [e['name'] for e in entries]
            self._build_t3_joint_group(self._t3_scroll_layout, group, names)
        self._t3_scroll_layout.addStretch()

        # Refresh group combo (guard for first call before combo exists)
        if not hasattr(self, 't3_append_group_combo'):
            return
        self.t3_append_group_combo.blockSignals(True)
        current = self.t3_append_group_combo.currentText()
        self.t3_append_group_combo.clear()
        self.t3_append_group_combo.addItem('\u2014 choose group \u2014')
        for g in self._t3_muscle_data.keys():
            self.t3_append_group_combo.addItem(g)
        self.t3_append_group_combo.addItem('New group\u2026')
        idx = self.t3_append_group_combo.findText(current)
        if idx >= 0:
            self.t3_append_group_combo.setCurrentIndex(idx)
        self.t3_append_group_combo.blockSignals(False)

    def _t3_set_all_groups(self, state):
        for cb in self._t3_group_checkboxes.values():
            cb.setChecked(state)

    def _t3_get_selected_joints(self):
        """Return {group: [name, ...]} for all checked joints."""
        result = {}
        for group, group_cb in self._t3_group_checkboxes.items():
            if not group_cb.isChecked():
                continue
            selected = [
                name for name, cb in self._t3_anchor_checkboxes[group].items()
                if cb.isChecked()
            ]
            if selected:
                result[group] = selected
        return result

    def _t3_validate_inputs(self):
        """Validate shared inputs. Returns (face_geo, head_jnt, prefix) or (None,None,None)."""
        face_geo = self.t3_geo_field.text().strip()
        head_jnt = self.t3_jnt_field.text().strip()
        prefix   = self.t3_prefix_field.text().strip()

        if not face_geo or not cmds.objExists(face_geo):
            QtWidgets.QMessageBox.warning(
                self, 'Missing Input', 'Please specify a valid face mesh.'
            )
            return None, None, None
        if not head_jnt or not cmds.objExists(head_jnt):
            QtWidgets.QMessageBox.warning(
                self, 'Missing Input', 'Please specify a valid head joint.'
            )
            return None, None, None
        return face_geo, head_jnt, prefix

    def _t3_create_guides(self):
        face_geo, head_jnt, prefix = self._t3_validate_inputs()
        if face_geo is None:
            return

        selected = self._t3_get_selected_joints()
        if not selected:
            QtWidgets.QMessageBox.warning(
                self, 'Nothing Selected',
                'Please select at least one muscle joint.'
            )
            return

        json_path = self.t3_json_field.text().strip()
        if not json_path or not os.path.isfile(json_path):
            QtWidgets.QMessageBox.warning(
                self, 'No JSON', 'Please provide a valid JSON path.'
            )
            return

        # Resolve any pre-existing guide group so new locators are added to it
        existing_grp = (
            self._t3_guide_grp
            if self._t3_guide_grp and cmds.objExists(self._t3_guide_grp)
            else None
        )
        if existing_grp is None:
            p     = f'{prefix}_' if prefix else ''
            exact = f'{p}muscle_guides_grp'
            if cmds.objExists(exact):
                existing_grp = exact
            else:
                candidates = cmds.ls('*muscle_guides_grp', type='transform') or []
                if candidates:
                    existing_grp = candidates[0]
                    if len(candidates) > 1:
                        cmds.warning(
                            f'Multiple guide groups found: {candidates}. '
                            f'Adding to "{existing_grp}".'
                        )

        generate_side = self.t3_radio_both.isChecked()
        lateral_axis  = self.t3_axis_bg.checkedId()          # 0=YZ, 1=XZ, 2=XY
        uniform_x     = self.t3_check_uniform_x.isChecked()
        cmds.undoInfo(openChunk=True, chunkName='MuscleJoints_createGuides')
        try:
            builder = MuscleJointBuilder(json_path)
            builder.load_joints(filter_groups=selected)
            top_grp = builder.create_guides(
                head_jnt, prefix, generate_side,
                existing_top_grp=existing_grp,
                lateral_axis=lateral_axis,
                uniform_x=uniform_x
            )
            self._t3_guide_grp = top_grp
        finally:
            cmds.undoInfo(closeChunk=True)

        cmds.inViewMessage(
            amg='<hl>Done!</hl>  Guide locators created.',
            pos='midCenter', fade=True
        )

    def _t3_clear_guides(self):
        if self._t3_guide_grp and cmds.objExists(self._t3_guide_grp):
            cmds.delete(self._t3_guide_grp)
        self._t3_guide_grp = None

    def _t3_build_joints(self):
        face_geo, head_jnt, prefix = self._t3_validate_inputs()
        if face_geo is None:
            return

        # Resolve guide group: use stored reference, then auto-detect from scene
        guide_grp = (
            self._t3_guide_grp
            if self._t3_guide_grp and cmds.objExists(self._t3_guide_grp)
            else None
        )

        if guide_grp is None:
            # Try exact prefixed name first
            p         = f'{prefix}_' if prefix else ''
            exact     = f'{p}muscle_guides_grp'
            if cmds.objExists(exact):
                guide_grp = exact
            else:
                # Fall back to any *muscle_guides_grp transform in the scene
                candidates = cmds.ls('*muscle_guides_grp', type='transform') or []
                if candidates:
                    guide_grp = candidates[0]
                    if len(candidates) > 1:
                        cmds.warning(
                            f'Multiple guide groups found: {candidates}. '
                            f'Using "{guide_grp}".'
                        )

        if guide_grp is None:
            QtWidgets.QMessageBox.warning(
                self, 'No Guides',
                'No guide locators found in the scene.\n'
                'Please run Stage 1 to create them first.'
            )
            return

        # Keep reference in sync so view-switch and rebuild work correctly
        self._t3_guide_grp = guide_grp

        cmds.undoInfo(openChunk=True, chunkName='MuscleJoints_buildJoints')
        try:
            builder = MuscleJointBuilder(self.t3_json_field.text().strip())
            master_grp, face_root_jnt = builder.build_joints(
                face_geo, head_jnt, prefix, self._t3_guide_grp
            )
            self._t3_joints_grp    = master_grp
            self._t3_face_root_jnt = face_root_jnt
        finally:
            cmds.undoInfo(closeChunk=True)

        cmds.inViewMessage(
            amg='<hl>Done!</hl>  Muscle joints built.',
            pos='midCenter', fade=True
        )

    def _t3_rebuild(self):
        for node_attr in ('_t3_joints_grp', '_t3_face_root_jnt'):
            node = getattr(self, node_attr, None)
            if node and cmds.objExists(node):
                cmds.delete(node)
            setattr(self, node_attr, None)
        self._t3_build_joints()

    def _t3_show_guides(self):
        if self._t3_guide_grp and cmds.objExists(self._t3_guide_grp):
            cmds.setAttr(f'{self._t3_guide_grp}.visibility', True)
        for node in (self._t3_joints_grp, self._t3_face_root_jnt):
            if node and cmds.objExists(node):
                cmds.setAttr(f'{node}.visibility', False)

    def _t3_show_joints(self):
        for node in (self._t3_joints_grp, self._t3_face_root_jnt):
            if node and cmds.objExists(node):
                cmds.setAttr(f'{node}.visibility', True)
        if self._t3_guide_grp and cmds.objExists(self._t3_guide_grp):
            cmds.setAttr(f'{self._t3_guide_grp}.visibility', False)

    def _t3_on_group_combo_changed(self, text):
        self.t3_append_newgroup_field.setVisible(text == 'New group\u2026')

    def _t3_get_from_selection(self):
        sel = cmds.ls(selection=True, long=False)
        if not sel:
            QtWidgets.QMessageBox.warning(
                self, 'Nothing Selected', 'Please select a locator.'
            )
            return
        head_jnt = self.t3_jnt_field.text().strip()
        if not head_jnt or not cmds.objExists(head_jnt):
            QtWidgets.QMessageBox.warning(
                self, 'No Head Joint', 'Please specify the head joint first.'
            )
            return

        loc    = sel[0]
        world_m = cmds.xform(loc, q=True, ws=True, matrix=True)

        # Convert world matrix → head-joint local via temp child locator
        tmp = cmds.spaceLocator(name='_tmp_local_convert')[0]
        cmds.parent(tmp, head_jnt)
        cmds.xform(tmp, ws=True, matrix=world_m)
        local_t = list(cmds.getAttr(f'{tmp}.translate')[0])
        local_r = list(cmds.getAttr(f'{tmp}.rotate')[0])
        cmds.delete(tmp)

        self._t3_append_local_t = local_t
        self._t3_append_local_r = local_r

        self.t3_append_local_t_lbl.setText(
            f'[{local_t[0]:.4f}, {local_t[1]:.4f}, {local_t[2]:.4f}]'
        )
        self.t3_append_local_r_lbl.setText(
            f'[{local_r[0]:.4f}, {local_r[1]:.4f}, {local_r[2]:.4f}]'
        )

    def _t3_write_to_json(self):
        if self._t3_append_local_t is None:
            QtWidgets.QMessageBox.warning(
                self, 'No Data',
                'Please click "Get from Selection" first to capture local coordinates.'
            )
            return

        name = self.t3_append_name_field.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, 'No Name', 'Please enter a muscle name.')
            return

        combo_text = self.t3_append_group_combo.currentText()
        if combo_text == 'New group\u2026':
            group = self.t3_append_newgroup_field.text().strip()
        elif combo_text == '\u2014 choose group \u2014':
            group = None
        else:
            group = combo_text

        if not group:
            QtWidgets.QMessageBox.warning(
                self, 'No Group', 'Please choose or create a group.'
            )
            return

        json_path = self.t3_json_field.text().strip()
        if not json_path:
            QtWidgets.QMessageBox.warning(self, 'No JSON Path', 'Please specify a JSON path.')
            return

        data = {'FacialMuscleJoints': {}}
        if os.path.isfile(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
            except Exception:
                pass

        jd       = data.setdefault('FacialMuscleJoints', {})
        grp_list = jd.setdefault(group, [])
        t = [round(v, 4) for v in self._t3_append_local_t]
        r = [round(v, 4) for v in self._t3_append_local_r]
        grp_list.append({'name': name, 'translate': t, 'rotate': r})

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

        cmds.inViewMessage(
            amg=f'<hl>Written!</hl>  {name} \u2192 {group} in JSON.',
            pos='midCenter', fade=True
        )
        self._t3_reload_json(json_path)

    def _t3_locator_at_origin(self):
        loc = cmds.spaceLocator(name='muscle_guide_loc')[0]
        cmds.xform(loc, ws=True, translation=[0, 0, 0])
        cmds.select(loc)

    def _t3_locator_at_vertex(self):
        sel   = cmds.ls(selection=True, flatten=True)
        verts = [s for s in sel if '.vtx[' in s]
        if not verts:
            QtWidgets.QMessageBox.warning(
                self, 'No Vertex Selected', 'Please select one or more vertices first.'
            )
            return
        positions = [cmds.xform(v, q=True, ws=True, translation=True) for v in verts]
        n   = len(positions)
        avg = [sum(p[i] for p in positions) / n for i in range(3)]
        loc = cmds.spaceLocator(name='muscle_guide_loc')[0]
        cmds.xform(loc, ws=True, translation=avg)
        cmds.select(loc)

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

    # ── Tab 2 slots ────────────────────────────────────────────────────────────

    def _t2_load_src(self):
        sel = cmds.ls(selection=True, long=False)
        if sel:
            self.t2_src_field.setText(sel[0])
            # Reset symmetry state whenever the mesh changes
            self._is_symmetric = None
            self._midline_edges = []
            self._midline_indices = []
            self.t2_sym_label.setText('—')
            self.t2_sym_label.setStyleSheet('')
            self.t2_midline_widget.setVisible(False)
            self.t2_mode_box.setEnabled(False)
            self.t2_exec_btn.setEnabled(False)
        else:
            cmds.warning('ARKit BS Builder: nothing selected.')

    def _t2_check_symmetry(self):
        mesh = self.t2_src_field.text().strip()
        if not mesh or not cmds.objExists(mesh):
            QtWidgets.QMessageBox.warning(
                self, 'No Mesh', 'Please specify a valid base mesh.'
            )
            return

        axis = ('X' if self.t2_axis_x.isChecked() else
                'Y' if self.t2_axis_y.isChecked() else 'Z')

        is_sym, mid_idx = check_symmetry(mesh, axis)
        self._is_symmetric = is_sym

        if is_sym:
            self._midline_indices = mid_idx  # auto-detected — ready to use
            self.t2_sym_label.setText('✓  Symmetric')
            self.t2_sym_label.setStyleSheet('color: #4CAF50; font-weight: bold;')
            self.t2_midline_widget.setVisible(False)
            self.t2_mode_box.setEnabled(True)
            self.t2_exec_btn.setEnabled(True)
        else:
            self._midline_edges   = []       # must be confirmed manually
            self._midline_indices = []
            self.t2_sym_label.setText('✗  Asymmetric — confirm midline to continue')
            self.t2_sym_label.setStyleSheet('color: #E74C3C; font-weight: bold;')
            self.t2_midline_widget.setVisible(True)
            self.t2_mid_count_lbl.setText('0 edges stored')
            self.t2_mode_box.setEnabled(False)
            self.t2_exec_btn.setEnabled(False)

    def _t2_enter_midline_select(self):
        """Put Maya into edge-select mode on the base mesh."""
        mesh = self.t2_src_field.text().strip()
        if mesh and cmds.objExists(mesh):
            cmds.select(mesh)
            cmds.selectMode(component=True)
            cmds.selectType(edge=True)

    def _t2_confirm_midline(self):
        """Store the currently selected edges as the midline.

        Edge indices are stored for flipTarget's symmetryEdge.
        Vertex indices are derived from those edges for split_by_weight_mask.
        """
        edges = [s for s in cmds.ls(selection=True, flatten=True) if '.e[' in s]
        if not edges:
            QtWidgets.QMessageBox.warning(
                self, 'No Edges Selected',
                'Please select the midline edges on the base mesh first.'
            )
            return

        self._midline_edges = [int(e.split('[')[1].rstrip(']')) for e in edges]

        # Convert edges → vertices for weight masking use
        cmds.select(edges)
        cmds.select(cmds.polyListComponentConversion(toVertex=True))
        vert_list = cmds.ls(selection=True, flatten=True)
        self._midline_indices = [int(v.split('[')[1].rstrip(']')) for v in vert_list]

        self.t2_mid_count_lbl.setText(f'{len(self._midline_edges)} edges stored')
        cmds.selectMode(object=True)
        # Midline confirmed — unlock mode and execute
        self.t2_mode_box.setEnabled(True)
        self.t2_exec_btn.setEnabled(True)

    def _t2_execute(self):
        base = self.t2_src_field.text().strip()
        if not base or not cmds.objExists(base):
            QtWidgets.QMessageBox.warning(
                self, 'No Base Mesh', 'Please specify a valid base mesh.'
            )
            return

        targets = cmds.ls(selection=True, long=False)
        if not targets:
            QtWidgets.QMessageBox.warning(
                self, 'Nothing Selected',
                'Please select the target mesh(es) to process in the viewport.'
            )
            return

        axis    = ('X' if self.t2_axis_x.isChecked() else
                   'Y' if self.t2_axis_y.isChecked() else 'Z')
        midline_verts = self._midline_indices if self._midline_indices else None
        midline_edges = self._midline_edges   if self._midline_edges   else None

        cmds.undoInfo(openChunk=True, chunkName='BSBuilder_flipSplit')
        try:
            if self.t2_mode_flip.isChecked():
                results = flip_target(
                    base, targets, axis,
                    find_str=self.t2_find_field.text(),
                    orig_replace=self.t2_repl_orig_field.text(),
                    flip_replace=self.t2_repl_flip_field.text(),
                    midline_edges=midline_edges,
                )
            else:
                results = split_by_weight_mask(base, targets, axis, midline_verts)
        finally:
            cmds.undoInfo(closeChunk=True)

        cmds.inViewMessage(
            amg=f'<hl>Done!</hl>  {len(results)} mesh(es) processed.',
            pos='midCenter',
            fade=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Launch
# ─────────────────────────────────────────────────────────────────────────────

_window_instance = None


def show():
    """Open (or raise) the ARKit BlendShape Builder window.

    Call this from Maya's Script Editor::

        import ui
        ui.show()

    Or via the shim::

        import ARKitBSBuilder
        ARKitBSBuilder.show()
    """
    global _window_instance
    try:
        _window_instance.close()
        _window_instance.deleteLater()
    except Exception:
        pass
    _window_instance = BSBuilderUI()
    _window_instance.show()
