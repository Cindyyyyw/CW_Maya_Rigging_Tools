"""ARKit BlendShape builder backend — BSBuilder class and mirror/split utilities.

This module is standalone (no imports from other project files).
Qt is imported here because _prompt_enable_symmetry presents an interactive
dialog, and _maya_main_window is needed by both that function and the UI.
"""

import maya.cmds as cmds
import json
import math
import os

try:
    from PySide2 import QtWidgets, QtCore
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtWidgets, QtCore
    from shiboken6 import wrapInstance

import maya.OpenMayaUI as omui


# Path to the ARFaceAnchor JSON — resolved relative to this file when possible.
try:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ARFaceAnchor.json')
except NameError:
    path = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/facialRig/ARFaceAnchor.json'


# ─────────────────────────────────────────────────────────────────────────────
#  UI helper (shared with the UI module)
# ─────────────────────────────────────────────────────────────────────────────

def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    try:
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    except Exception:
        return None


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
