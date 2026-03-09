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
        self.blendShape_grp_keys = []
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
        self.blendShape_grp_keys = []
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
                    self.blendShape_grp_keys.append(group)
                else:
                    self.blendShape_names.extend(name_array)
                    self.blendShape_grp.append(name_array)
                    self.blendShape_grp_keys.append(group)

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
            # Top-level container for all anchor groups
            top_grp_name = f'{prefix}BS_grp'
            top_grp = cmds.group(empty=True, name=top_grp_name)

            for i, (group_key, group) in enumerate(
                zip(self.blendShape_grp_keys, self.blendShape_grp)
            ):
                # One Maya group per anchor group, spaced along X, parented under top group
                grp_name = f'{prefix}{group_key}_grp'
                grp = cmds.group(empty=True, name=grp_name)
                cmds.parent(grp, top_grp)
                cmds.setAttr(f'{grp}.translate', i * 5 * self.transform_step, 0, 0,
                             type='double3')

                for j, anchor in enumerate(group):
                    # Local position inside the group: 3-column grid in XY, Z for right side
                    lx = self.transform_step * (j % 3)
                    ly = self.transform_step * math.floor(j / 3)

                    if self.generate_side and anchor.endswith('_DIR_'):
                        left_name = prefix + anchor[:-5] + 'Left'
                        right_name = prefix + anchor[:-5] + 'Right'

                        geo_left = cmds.duplicate(source, n=left_name)[0]
                        cmds.parent(geo_left, grp)
                        cmds.setAttr(f'{geo_left}.translate', lx, ly, 0, type='double3')

                        geo_right = cmds.duplicate(source, n=right_name)[0]
                        cmds.parent(geo_right, grp)
                        cmds.setAttr(f'{geo_right}.translate', lx, ly,
                                     -self.transform_step * 3, type='double3')
                        continue

                    geo = cmds.duplicate(source, n=prefix + anchor)[0]
                    cmds.parent(geo, grp)
                    cmds.setAttr(f'{geo}.translate', lx, ly, 0, type='double3')
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
#  Mirror / Split utilities
# ─────────────────────────────────────────────────────────────────────────────

_AXIS_IDX = {'X': 0, 'Y': 1, 'Z': 2}


def check_symmetry(mesh, axis='X', tolerance=0.001):
    """Check whether *mesh* is symmetric about the given axis.

    Returns:
        (is_symmetric: bool, midline_vert_indices: list[int])
    """
    ai = _AXIS_IDX[axis.upper()]
    flat = cmds.xform(f'{mesh}.vtx[*]', q=True, translation=True, worldSpace=True)
    positions = [(flat[i * 3], flat[i * 3 + 1], flat[i * 3 + 2])
                 for i in range(len(flat) // 3)]

    precision = max(0, -int(math.floor(math.log10(tolerance))))
    pos_set = {tuple(round(v, precision) for v in p) for p in positions}

    midline, asymmetric = [], []
    for i, p in enumerate(positions):
        if abs(p[ai]) <= tolerance:
            midline.append(i)
            continue
        mirror = list(p)
        mirror[ai] *= -1
        if tuple(round(v, precision) for v in mirror) not in pos_set:
            asymmetric.append(i)

    return len(asymmetric) == 0, midline


def _prompt_enable_symmetry(carrier_name, edge_index):
    """Pause for the user to enable Topological Symmetry interactively.

    Uses a non-modal QDialog driven by a local QEventLoop so Maya's viewport
    stays fully interactive while the prompt is visible.

    Raises RuntimeError if the user cancels.
    """
    parent = _maya_main_window()

    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle('Enable Topological Symmetry')
    # Stay on top but NON-modal so Maya's viewport remains clickable
    dlg.setWindowFlags(
        QtCore.Qt.Dialog
        | QtCore.Qt.WindowStaysOnTopHint
    )
    dlg.setWindowModality(QtCore.Qt.NonModal)

    layout = QtWidgets.QVBoxLayout(dlg)
    layout.setSpacing(10)

    lbl = QtWidgets.QLabel(
        f'In the <b>top bar symmetry settings</b>, set the symmetry object '
        f'to <b>{carrier_name}</b> and enable <b>Topological Symmetry</b>.<br><br>'
        'Click <b>OK</b> once symmetry is active to continue.'
    )
    lbl.setWordWrap(True)
    layout.addWidget(lbl)

    btn_row = QtWidgets.QHBoxLayout()
    ok_btn     = QtWidgets.QPushButton('OK')
    cancel_btn = QtWidgets.QPushButton('Cancel')
    ok_btn.setDefault(True)
    btn_row.addStretch()
    btn_row.addWidget(ok_btn)
    btn_row.addWidget(cancel_btn)
    layout.addLayout(btn_row)

    # A local event loop lets the dialog stay visible while Maya's viewport
    # keeps processing events (menus, clicks, etc.).
    confirmed = [False]
    loop = QtCore.QEventLoop()

    ok_btn.clicked.connect(lambda: [confirmed.__setitem__(0, True), loop.quit()])
    cancel_btn.clicked.connect(loop.quit)
    dlg.rejected.connect(loop.quit)

    dlg.show()
    loop.exec_()
    dlg.close()

    if not confirmed[0]:
        raise RuntimeError('flip_target: user cancelled symmetry setup.')


def flip_target(base_mesh, target_meshes, axis='X',
                find_str='_DIR_', orig_replace='Left', flip_replace='Right',
                midline_edges=None):
    """Flip each target using blendShape flipTarget.

    For each target two meshes are produced and returned:
      - A straight duplicate of the original (pre-flip), renamed via
        find_str → orig_replace.
      - A flipped duplicate obtained by applying flipTarget on a clean
        temporary carrier, renamed via find_str → flip_replace.

    base_mesh and the original target meshes are left unmodified.

    One temp carrier is created from base_mesh before the loop and reused
    for all targets (each blendShape is deleted after evaluation, returning
    the carrier to its clean base shape).  For asymmetric meshes the seam
    edge is auto-selected and a dialog asks the user to enable Topological
    Symmetry once before any targets are processed.
    """
    results = []

    # Create the single temp carrier outside the undo queue so Ctrl+Z cannot
    # resurrect it.  It is reused for every target in the loop.
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        temp_carrier = cmds.duplicate(
            base_mesh, n=base_mesh + '_flip_tmp'
        )[0]
        cmds.delete(temp_carrier, constructionHistory=True)
        for attr in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
            cmds.setAttr(f'{temp_carrier}.{attr}', lock=False)
    finally:
        cmds.undoInfo(stateWithoutFlush=True)

    try:
        # if midline_edges:
        #     # For asymmetric meshes, topological symmetry must be enabled
        #     # interactively.  Select the seam edge and ask the user to turn it
        #     # on once — the state persists for every target in the loop below.
        #     _prompt_enable_symmetry(temp_carrier, midline_edges[0])

        for target in target_meshes:
            # Derive names from the find/replace strings
            if find_str and find_str in target:
                orig_name = target.replace(find_str, orig_replace)
                flip_name = target.replace(find_str, flip_replace)
            else:
                orig_name = f'{target}_{orig_replace}'
                flip_name = f'{target}_{flip_replace}'

            # Keep a clean copy of the pre-flip mesh, parented to world
            orig = cmds.duplicate(target, n=orig_name)[0]
            try:
                cmds.parent(orig, world=True)
            except Exception as e:
                print(e)
            # Apply the target as a blendShape on the temp carrier.
            bs = cmds.blendShape(target, temp_carrier)[0]
            cmds.setAttr(f'{bs}.weight[0]', 1.0)

            # flipTarget=[mirrorAxis, targetIndex]
            #   • First  value: mirror axis (0=X, 1=Y, 2=Z).
            #   • Second value: TARGET INDEX — always 0 since the blendShape
            #     is rebuilt from scratch each iteration.
            # symmetrySpace:
            #   • 0 (topological) — for asymmetric meshes where the user has
            #     enabled Topological Symmetry on the carrier above.
            #   • 1 (object space) — for symmetric meshes; mirrors vertex
            #     offsets across the world axis, no symmetry cache needed.
            if midline_edges:
                sym_space = 0
                _prompt_enable_symmetry(temp_carrier, midline_edges[0])
                cmds.blendShape(bs, edit=True, flipTarget=[0, 0],
                                symmetrySpace=sym_space)
            else:
                sym_space = 1
                cmds.blendShape(bs, edit=True, flipTarget=[0, 0],
                                symmetrySpace=sym_space)

            flipped = cmds.duplicate(temp_carrier, n=flip_name)[0]
            try:
                cmds.parent(flipped, world=True)
            except Exception as e:
                print(e)
            cmds.delete(flipped, constructionHistory=True)
            # Deleting the blendShape node returns temp_carrier to its clean
            # base shape, ready for the next target.
            cmds.delete(bs)
            results.extend([orig, flipped])
    finally:
        # Delete the carrier outside the undo queue for the same reason it
        # was created there.
        cmds.undoInfo(stateWithoutFlush=False)
        try:
            if cmds.objExists(temp_carrier):
                cmds.delete(temp_carrier)
        finally:
            cmds.undoInfo(stateWithoutFlush=True)

    return results


def split_by_weight_mask(base_mesh, target_meshes, axis='X',
                          midline_vert_indices=None, find_str='_DIR_', tolerance=0.001):
    """Split each target into Left (+axis) and Right (-axis) duplicates.

    Each duplicate is a copy of *base_mesh* with the target applied as a
    blendShape.  Per-vertex weights are set so that only the appropriate half
    is deformed; midline vertices receive 0.5 for a smooth seam.  The result
    is baked (construction history deleted) before being returned.

    Args:
        midline_vert_indices: explicit midline vertex indices (used when the
            mesh is asymmetric and the user has manually confirmed them).
            Pass None to auto-detect from the axis tolerance.
    """
    ai = _AXIS_IDX[axis.upper()]
    flat = cmds.xform(f'{base_mesh}.vtx[*]', q=True, translation=True, worldSpace=True)
    positions = [(flat[i * 3], flat[i * 3 + 1], flat[i * 3 + 2])
                 for i in range(len(flat) // 3)]

    if midline_vert_indices is not None:
        mid_set = set(midline_vert_indices)
    else:
        mid_set = {i for i, p in enumerate(positions) if abs(p[ai]) <= tolerance}

    pos_verts = [i for i, p in enumerate(positions) if i not in mid_set and p[ai] >  0]
    neg_verts = [i for i, p in enumerate(positions) if i not in mid_set and p[ai] <= 0]

    def _apply_weights(bs, primary, secondary):
        base_attr = f'{bs}.inputTarget[0].inputTargetGroup[0].targetWeights'
        for vi in primary:
            cmds.setAttr(f'{base_attr}[{vi}]', 1.0)
        for vi in secondary:
            cmds.setAttr(f'{base_attr}[{vi}]', 0.0)
        for vi in mid_set:
            cmds.setAttr(f'{base_attr}[{vi}]', 0.5)

    results = []
    for target in target_meshes:
        for side, primary, secondary in [
            ('Left',  pos_verts, neg_verts),
            ('Right', neg_verts, pos_verts),
        ]:
            if find_str and find_str in target:
                dup_name = target.replace(find_str, side)
            else:
                dup_name = f'{target}_{side}'
            dup = cmds.duplicate(base_mesh, n=dup_name)[0]
            bs  = cmds.blendShape(target, dup)[0]
            cmds.setAttr(f'{bs}.weight[0]', 1.0)
            _apply_weights(bs, primary, secondary)
            cmds.delete(dup, constructionHistory=True)
            results.append(dup)
    return results


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
