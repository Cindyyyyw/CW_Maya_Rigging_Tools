"""
hairRigSetup.py
───────────────────────────────────────────────────────────────────────────────
UI-driven hair rigging tool for Maya.

WORKFLOW  (follow phases in order)
──────────────────────────────────
  PREP      Generate start curves from poly edges, rebuild & reverse utilities.
  PHASE 1   Build IK-spline joint chains from selected start curves.
  ── PAUSE ── Simulate, review, return to frame 1.
  PHASE 2   Make dyna curves dynamic; build dual blendShapes (output_crv +
            start_crv) and a nucleus condition node to switch between them.
  PHASE 3   Wire the temp joint rig — blendMatrix/multMatrix so the joint
            tracks the 'Main' controller when simulation is active.
  PHASE 4   (Optional) Create skinCluster + import ngSkinTools2 weight data.
  PHASE 5   Build FK controller layer on top of the IK joint chains.

HARD PREREQUISITES (scene must have these before running)
──────────────────────────────────────────────────────────
  • bonesOnCurve MEL proc available (ships with Maya Rigging tools).
  • A clean, single-sided proxy mesh for follicle attachment (named in UI).
  • A controller named 'Main' in the scene (required for Phase 3).
  • Optional: a joint for IK-twist world-up (set in Global Settings).
  • Optional: ngSkinTools2 plugin loaded (for Phase 4 weight import).

NAMING CONVENTION (auto-generated from the Base Name UI field)
──────────────────────────────────────────────────────────────
  Full name = Base Name  (e.g.  "Hair"  or  "F_Hair"  or  "Tail")

  Start curves must contain "start" in their name, e.g.:
      hair_start_crv_1
      F_Hair_01_start_crv

  The tool derives all other names by replacing the "start" token:
      *_ik_*     IK curves
      *_dyna_*   Dynamic input curves
      *_output_* Output curves (from hair system)
      *_flc      Follicle transform nodes
      *_jnt_N    IK spline joints (N = 1-7)
      *_ikHandle IK spline handles
"""

import maya.cmds as cmds
import maya.mel as mel
import os
import os.path

# ── Optional ngSkinTools2 ─────────────────────────────────────────────────────
try:
    from ngSkinTools2 import api as ngst_api
    from ngSkinTools2.api import InfluenceMappingConfig, VertexTransferMode
    _HAS_NGSKIN = True
except ImportError:
    _HAS_NGSKIN = False

# ── UI constants ──────────────────────────────────────────────────────────────
_WIN_ID   = 'hairRigSetupWin'
_WIN_W    = 430
_LBL_W    = 138   # label column width
_FLD_W    = 230   # field column width
_BTN_W    = 55    # small button width
_BTN_H    = 28    # standard action-button height
_BTN_H_LG = 36   # large phase-button height

# Colour palette (R, G, B  floats 0-1)
_COL_GREEN  = (0.25, 0.48, 0.25)
_COL_BLUE   = (0.18, 0.36, 0.58)
_COL_WARN   = (0.30, 0.24, 0.04)
_COL_MUTE   = (0.32, 0.32, 0.38)
_COL_RED    = (0.48, 0.28, 0.28)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_name(base_ctrl):
    """Read the Base Name UI field and return the hair identifier."""
    return cmds.textFieldGrp(base_ctrl, q=True, text=True).strip() or 'Hair'


def _latest_hair_system_shape():
    """Return the highest-numbered hairSystemShape node in the scene."""
    shapes = cmds.ls('hairSystemShape*', shapes=True) or []
    if not shapes:
        cmds.warning('[Hair Rig] No hairSystem found in scene.')
        return None

    def _sort_key(name):
        suffix = name.replace('hairSystemShape', '')
        return int(suffix) if suffix.isdigit() else float('inf')

    shapes.sort(key=_sort_key)
    return shapes[-1]


def _store(key, lst):
    """Persist a string list across phases via optionVar."""
    cmds.optionVar(sv=(key, ','.join(lst)))


def _load(key):
    """Retrieve a stored string list. Returns [] if missing/empty."""
    if not cmds.optionVar(exists=key):
        return []
    raw = cmds.optionVar(q=key)
    return [v for v in raw.split(',') if v]


def _msg(text, pos='midCenter'):
    """Show a brief in-viewport message."""
    cmds.inViewMessage(amg=text, pos=pos, fade=True, fst=3500)


def _get_matrix(attr):
    """Return a matrix attribute as a flat list of 16 floats.

    cmds.getAttr on matrix-type attributes returns a list containing
    one tuple of 16 elements: [(m00, m01, ..., m33)].
    """
    val = cmds.getAttr(attr)
    if val and hasattr(val[0], '__iter__'):
        return list(val[0])
    return list(val)


def _mat4_mult(a, b):
    """Multiply two 4×4 matrices stored as 16-element flat lists (row-major).

    Compatible with the output of _get_matrix().
    """
    result = [0.0] * 16
    for row in range(4):
        for col in range(4):
            for k in range(4):
                result[row * 4 + col] += a[row * 4 + k] * b[k * 4 + col]
    return result


# ══════════════════════════════════════════════════════════════════════════════
# PREP  —  CURVE GENERATION & CLEANUP
# ══════════════════════════════════════════════════════════════════════════════

def generate_curve_from_edge(spans):
    """
    Convert selected poly edges to a cubic NURBS start-curve.

    Steps:
      1. polyToCurve (degree 3, open)
      2. Rebuild to `spans` spans, degree 3
      3. Delete history
      4. Rename to hair_start_crv_# (Maya auto-increments #)
    """
    sl = cmds.ls(sl=True, flatten=True)
    if not sl:
        cmds.warning('[Hair Rig] Nothing selected. Select poly edges first.')
        return

    if not any('.e[' in s for s in sl):
        cmds.warning('[Hair Rig] Selection contains non-edge components. '
                     'Select only poly edges.')
        return

    result  = cmds.polyToCurve(form=2, degree=3, conformToSmoothMeshPreview=0)
    new_crv = result[0]

    cmds.rebuildCurve(new_crv, s=spans, d=3, ch=0, rpo=1, end=1, kr=0, kt=0)
    cmds.delete(new_crv, ch=True)

    renamed = cmds.rename(new_crv, 'hair_start_crv_#')
    cmds.select(renamed)
    _msg(f'<hl>Curve created:</hl>  {renamed}  ({spans} spans, degree 3)')
    print(f'[Hair Rig] Generated: {renamed}')


def rebuild_curves(spans):
    """Rebuild each selected curve to `spans` spans, degree 3, in-place."""
    sl = cmds.ls(sl=True)
    if not sl:
        cmds.warning('[Hair Rig] Nothing selected.')
        return
    for crv in sl:
        cmds.rebuildCurve(crv, s=spans, d=3, ch=0, rpo=1, end=1, kr=0, kt=0)
    _msg(f'<hl>Rebuilt</hl>  {len(sl)} curve(s)  →  {spans} spans')
    print(f'[Hair Rig] Rebuilt {len(sl)} curve(s) to {spans} spans.')


def reverse_curves():
    """Reverse direction of each selected curve in-place."""
    sl = cmds.ls(sl=True)
    if not sl:
        cmds.warning('[Hair Rig] Nothing selected.')
        return
    for crv in sl:
        cmds.reverseCurve(crv, ch=0, rpo=1)
    _msg(f'<hl>Reversed</hl>  {len(sl)} curve(s)')
    print(f'[Hair Rig] Reversed {len(sl)} curve(s).')


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1  —  IK SPLINE JOINT CHAINS
# ══════════════════════════════════════════════════════════════════════════════

def run_phase1(full_name, head_joint=''):
    """
    Build an IK-spline joint chain for every selected start-curve.

    Per curve:
      • Duplicate  → ik_crv  (drives IK handle)
      • bonesOnCurve(6)  →  7 joints + spline IK handle
      • Rename joints  {base}_jnt_1 … _jnt_7  and  {base}_ikHandle
      • Duplicate original  → dyna_crv  (left at world root for Phase 2)

    IK joint group positioning
    ───────────────────────────
    If head_joint is supplied a blendMatrix node ({full_name}_ik_jnt_grp_bm)
    drives the group's offsetParentMatrix:
      • inputMatrix  = static snapshot of head_joint.worldMatrix at build time
      • target[0].targetMatrix  ← live head_joint.worldMatrix[0]
      • target[0].weight  = 0 at build time (connected to nucleus_cond.outColorR
                             by Phase 2 once the condition node exists)
    When weight=0 (sim OFF): group sits at the static captured position.
    When weight=1 (sim ON):  group tracks head_joint live.

    Persists ik_hdl_lis / ik_crv_lis / dyna_crv_lis via optionVars.
    """
    sl = cmds.ls(sl=True)
    if not sl:
        cmds.error('[Hair Rig] Nothing selected. Select all start curves first.')
        return

    # ── IK joint group + optional blendMatrix positioning ─────────────────────
    jnt_grp = cmds.group(em=True, w=True, name=f'{full_name}_ik_jnt_grp')

    if head_joint and cmds.objExists(head_joint):
        # Snapshot head joint's current world matrix (static, not a live conn)
        static_mtx = _get_matrix(f'{head_joint}.worldMatrix[0]')

        bm_name = f'{full_name}_ik_jnt_grp_bm'
        if cmds.objExists(bm_name):
            cmds.delete(bm_name)
        bm = cmds.createNode('blendMatrix', name=bm_name)

        # inputMatrix = static rest position
        cmds.setAttr(f'{bm}.inputMatrix', *static_mtx, type='matrix')
        # target[0].targetMatrix = live feed from head joint
        cmds.connectAttr(f'{head_joint}.worldMatrix[0]',
                         f'{bm}.target[0].targetMatrix')
        # weight left at 0 (default) — Phase 2 will wire nucleus_cond.outColorR

        # Drive jnt_grp's offsetParentMatrix; local TRS stays at identity
        cmds.connectAttr(f'{bm}.outputMatrix', f'{jnt_grp}.offsetParentMatrix')

    elif head_joint:
        cmds.warning(f'[Hair Rig] Head joint "{head_joint}" not found — '
                     'IK joint group left at world origin.')

    crv_grp = cmds.group(em=True, w=True, name=f'{full_name}_ik_crv_grp')
    hdl_grp = cmds.group(em=True, w=True, name=f'{full_name}_ik_hdl_grp')

    ik_hdl_lis, ik_crv_lis, dyna_crv_lis = [], [], []

    for crv in sl:
        # ── IK curve ──────────────────────────────────────────────────────────
        ik_crv = cmds.duplicate(crv, name=crv.replace('start', 'ik'))[0]
        ik_crv_lis.append(ik_crv)

        cmds.select(ik_crv, replace=True)
        try:
            # bonesOnCurve(numBones=6, rebuild=0, createSplineIK=1)
            # Creates 7 joints (joint1…joint7) + ikHandle1
            mel.eval('bonesOnCurve(6, 0, 1);')
        except Exception as exc:
            cmds.error(
                f'[Hair Rig] bonesOnCurve failed on "{crv}". '
                f'Ensure the Maya Rigging tools MEL procs are loaded.\n{exc}')
            return

        # Rename joints and handle
        base = ik_crv.replace('_crv', '')   # e.g.  F_Hair_01_ik
        for j in range(1, 8):
            cmds.rename(f'joint{j}', f'{base}_jnt_{j}')
        ik_handle = cmds.rename('ikHandle1', f'{base}_ikHandle')
        ik_hdl_lis.append(ik_handle)

        # Parent into groups
        cmds.parent(f'{base}_jnt_1', jnt_grp)
        cmds.parent(ik_handle,       hdl_grp)
        cmds.parent(ik_crv,          crv_grp)

        # ── Dyna curve (stays at world root — needed by makeCurvesDynamic) ───
        dyna_crv = cmds.duplicate(crv, name=crv.replace('start', 'dyna'))[0]
        # Only re-parent to world if it's currently inside a group.
        # If the original start curve was already at world root, the duplicate
        # is too — calling parent(w=True) on it would raise a RuntimeError.
        if cmds.listRelatives(dyna_crv, parent=True):
            cmds.parent(dyna_crv, w=True)
        dyna_crv_lis.append(dyna_crv)

    # Persist for Phase 2
    _store('_hairRig_ik_hdl',   ik_hdl_lis)
    _store('_hairRig_ik_crv',   ik_crv_lis)
    _store('_hairRig_dyna_crv', dyna_crv_lis)

    _msg('<hl>Phase 1 complete!</hl>  '
         'Now simulate, review, return to frame 1, then run Phase 2.')
    print(f'[Hair Rig] Phase 1 complete — {len(sl)} chain(s) built.')


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2  —  DYNAMIC HAIR + FOLLICLE SETUP
# ══════════════════════════════════════════════════════════════════════════════

def run_phase2(proxy_mesh, full_name, temp_jnt=''):
    """
    Make dyna curves dynamic, rename outputs + follicles, build dual blendShapes
    (output_crv + start_crv), create a nucleus condition node, configure hair
    system attributes, and wire IK twist control.

    BlendShape layout (per IK curve)
    ─────────────────────────────────
      Target 0  output_crv  ←  weight[0]  driven by  nucleus_cond.outColorR
      Target 1  start_crv   ←  weight[1]  driven by  nucleus_cond.outColorG

    Nucleus condition logic
    ────────────────────────
      nucleus.enable == 0  (sim OFF)  →  outColorR=0, outColorG=1
                                         → start_crv drives IK curve (static pose)
      nucleus.enable == 1  (sim ON)   →  outColorR=1, outColorG=0
                                         → output_crv drives IK curve (dynamic pose)

    Reads the curve / handle lists stored by Phase 1.
    Stores the condition node name for Phase 3 via optionVar.
    """
    ik_hdl_lis   = _load('_hairRig_ik_hdl')
    ik_crv_lis   = _load('_hairRig_ik_crv')
    dyna_crv_lis = _load('_hairRig_dyna_crv')

    if not dyna_crv_lis:
        cmds.error('[Hair Rig] No Phase 1 data found. Run Phase 1 first.')
        return

    if not cmds.objExists(proxy_mesh):
        cmds.error(
            f'[Hair Rig] Proxy mesh "{proxy_mesh}" not found in scene. '
            'Check the Hair Base Proxy field in Global Settings.')
        return

    # ── makeCurvesDynamic ─────────────────────────────────────────────────────
    cmds.select(dyna_crv_lis, replace=True)
    cmds.select(proxy_mesh, add=True)
    mel.eval('makeCurvesDynamic 2 { "1", "0", "1", "1", "0"};')

    # ── Rename outputs / follicles, build blendShapes ─────────────────────────
    # Each entry in bs_lis is (blendShape_node, has_start_crv_flag)
    bs_lis = []

    for i, dyna_crv in enumerate(dyna_crv_lis):
        output_crv = cmds.rename(f'curve{i + 1}',
                                 dyna_crv.replace('dyna', 'output'))
        flc_name   = dyna_crv.replace('_dyna_', '_').replace('crv', 'flc')
        flc        = cmds.rename(f'follicle{i + 1}', flc_name)

        cmds.setAttr(f'{flc}.restPose',       1)   # rest on surface
        cmds.setAttr(f'{flc}.startDirection', 1)   # start from curve
        cmds.setAttr(f'{flc}.pointLock',      1)   # lock root to surface

        # Build blendShape with output_crv and start_crv both as targets
        start_crv  = dyna_crv.replace('dyna', 'start')
        has_start  = cmds.objExists(start_crv)

        if has_start:
            # Target 0 = output_crv (weight 1), Target 1 = start_crv (weight 0)
            bs = cmds.blendShape(
                output_crv, start_crv, ik_crv_lis[i],
                w=[(0, 1), (1, 0)])[0]
        else:
            cmds.warning(
                f'[Hair Rig] Start curve "{start_crv}" not found — '
                'using output curve only for this chain.')
            bs = cmds.blendShape(output_crv, ik_crv_lis[i], w=[(0, 1)])[0]

        bs_lis.append((bs, has_start))

    # ── Hair system defaults ──────────────────────────────────────────────────
    hss = _latest_hair_system_shape()
    if hss:
        cmds.setAttr(f'{hss}.stiffnessScale[0].stiffnessScale_FloatValue',   0.5)
        cmds.setAttr(f'{hss}.attractionScale[1].attractionScale_FloatValue',  0.1)
        cmds.setAttr(f'{hss}.attractionScale[2].attractionScale_Position',    0.5)
        cmds.setAttr(f'{hss}.attractionScale[2].attractionScale_FloatValue',  0.3)
        cmds.setAttr(f'{hss}.attractionScale[2].attractionScale_Interp',      3)
        cmds.setAttr(f'{hss}.startCurveAttract', 1)

        # ── Nucleus condition node ────────────────────────────────────────────
        nucleus_list = cmds.listConnections(hss, type='nucleus') or []
        if nucleus_list:
            nucleus   = nucleus_list[0]
            cond_name = f'{full_name}_nucleus_cond'

            if not cmds.objExists(cond_name):
                cond = cmds.createNode('condition', name=cond_name)
            else:
                cond = cond_name

            # operation=0 → Equal: firstTerm == secondTerm → colorIfTrue
            cmds.setAttr(f'{cond}.operation',     0)   # Equal
            cmds.setAttr(f'{cond}.secondTerm',    0.0)

            # nucleus.enable == 0 (sim OFF) → colorIfTrue → outR=0, outG=1
            cmds.setAttr(f'{cond}.colorIfTrueR',  0.0)
            cmds.setAttr(f'{cond}.colorIfTrueG',  1.0)
            cmds.setAttr(f'{cond}.colorIfTrueB',  0.0)

            # nucleus.enable == 1 (sim ON)  → colorIfFalse → outR=1, outG=0
            cmds.setAttr(f'{cond}.colorIfFalseR', 1.0)
            cmds.setAttr(f'{cond}.colorIfFalseG', 0.0)
            cmds.setAttr(f'{cond}.colorIfFalseB', 1.0)

            cmds.connectAttr(f'{nucleus}.enable', f'{cond}.firstTerm',
                             force=True)

            # Persist condition node name for Phase 3
            cmds.optionVar(sv=('_hairRig_cond_node', cond_name))

            # Wire condition outputs to every blendShape
            for bs, has_start in bs_lis:
                cmds.connectAttr(f'{cond}.outColorR', f'{bs}.weight[0]',
                                 force=True)
                if has_start:
                    cmds.connectAttr(f'{cond}.outColorG', f'{bs}.weight[1]',
                                     force=True)

            # Also wire IK joint group blendMatrix (created in Phase 1)
            # so the group tracks head_joint live when physics is active.
            ik_jnt_grp_bm = f'{full_name}_ik_jnt_grp_bm'
            if cmds.objExists(ik_jnt_grp_bm):
                cmds.connectAttr(f'{cond}.outColorR',
                                 f'{ik_jnt_grp_bm}.target[0].weight',
                                 force=True)
                print(f'[Hair Rig] IK joint group blendMatrix weight wired: '
                      f'{ik_jnt_grp_bm}')

            print(f'[Hair Rig] Nucleus condition node created: {cond_name}')
        else:
            cmds.warning(
                '[Hair Rig] No nucleus found connected to hair system — '
                'condition node skipped.')

    # ── IK twist control ──────────────────────────────────────────────────────
    if temp_jnt and cmds.objExists(temp_jnt):
        for hdl in ik_hdl_lis:
            cmds.setAttr(f'{hdl}.dTwistControlEnable', 1)
            cmds.setAttr(f'{hdl}.dWorldUpType',        1)
            cmds.connectAttr(f'{temp_jnt}.worldMatrix[0]',
                             f'{hdl}.dWorldUpMatrix', force=True)
    elif temp_jnt:
        cmds.warning(
            f'[Hair Rig] Temp joint "{temp_jnt}" not found — '
            'IK twist control skipped. Run Phase 3 after creating the joint, '
            'or wire it manually.')

    _msg('<hl>Phase 2 complete!</hl>  '
         'Dynamic hair is live.  Run Phase 3 to wire the temp joint rig.')
    print('[Hair Rig] Phase 2 complete.')


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3  —  TEMP JOINT RIG
# ══════════════════════════════════════════════════════════════════════════════

def build_temp_jnt_rig(temp_jnt, full_name):
    """
    Wire the temp joint (IK-twist world-up object) so it tracks the 'Main'
    controller when the nucleus simulation is active.

    Node network
    ─────────────
    blendMatrix  ({full_name}_temp_jnt_bm)
      .inputMatrix              = static relative matrix  (rest / sim-off pose)
      .target[0].targetMatrix  ←  multMatrix.matrixSum
      .target[0].weight        ←  {full_name}_nucleus_cond.outColorR
      .outputMatrix            →  temp_jnt.offsetParentMatrix

    multMatrix  ({full_name}_temp_jnt_mm)
      .matrixIn[0]   = static relative matrix  (same value as bm.inputMatrix)
      .matrixIn[1]  ←  Main.worldMatrix[0]
      .matrixSum    →  bm.target[0].targetMatrix

    Relative matrix
    ───────────────
      relative_mtx = temp_jnt.worldMatrix × Main.worldInverseMatrix
      This stores temp_jnt's position in Main's local space.

    Condition logic (created in Phase 2)
    ──────────────────────────────────────
      nucleus.enable == 0  →  outColorR = 0  →  bm weight = 0
                               →  offsetParentMatrix = static relative_mtx
      nucleus.enable == 1  →  outColorR = 1  →  bm weight = 1
                               →  offsetParentMatrix = relative_mtx × Main.wm
                               →  temp_jnt tracks Main's current world position
    """
    if not cmds.objExists(temp_jnt):
        cmds.error(f'[Hair Rig] Temp joint "{temp_jnt}" not found in scene.')
        return

    if not cmds.objExists('Main'):
        cmds.error(
            '[Hair Rig] Controller "Main" not found in scene. '
            'Phase 3 requires a controller named exactly "Main".')
        return

    # ── Parent temp_jnt to world if needed ────────────────────────────────────
    if cmds.listRelatives(temp_jnt, parent=True):
        cmds.parent(temp_jnt, w=True)

    # ── Compute relative matrix ───────────────────────────────────────────────
    jnt_world    = _get_matrix(f'{temp_jnt}.worldMatrix[0]')
    main_inv     = _get_matrix('Main.worldInverseMatrix[0]')
    relative_mtx = _mat4_mult(jnt_world, main_inv)

    # ── blendMatrix ───────────────────────────────────────────────────────────
    bm_name = f'{full_name}_temp_jnt_bm'
    if cmds.objExists(bm_name):
        cmds.delete(bm_name)
    bm = cmds.createNode('blendMatrix', name=bm_name)
    cmds.setAttr(f'{bm}.inputMatrix', *relative_mtx, type='matrix')

    # ── multMatrix ────────────────────────────────────────────────────────────
    mm_name = f'{full_name}_temp_jnt_mm'
    if cmds.objExists(mm_name):
        cmds.delete(mm_name)
    mm = cmds.createNode('multMatrix', name=mm_name)
    cmds.setAttr(f'{mm}.matrixIn[0]', *relative_mtx, type='matrix')
    cmds.connectAttr('Main.worldMatrix[0]', f'{mm}.matrixIn[1]')

    # multMatrix output → blendMatrix target
    cmds.connectAttr(f'{mm}.matrixSum', f'{bm}.target[0].targetMatrix')

    # ── Connect condition outColorR → blend weight ────────────────────────────
    cond_node = ''
    if cmds.optionVar(exists='_hairRig_cond_node'):
        cond_node = cmds.optionVar(q='_hairRig_cond_node')

    if cond_node and cmds.objExists(cond_node):
        cmds.connectAttr(f'{cond_node}.outColorR',
                         f'{bm}.target[0].weight', force=True)
    else:
        cmds.warning(
            '[Hair Rig] Nucleus condition node not found — '
            'blendMatrix weight not connected. Run Phase 2 first.')

    # ── Zero local transform; drive from blendMatrix output ───────────────────
    cmds.setAttr(f'{temp_jnt}.translate', 0.0, 0.0, 0.0, type='double3')
    cmds.setAttr(f'{temp_jnt}.rotate',    0.0, 0.0, 0.0, type='double3')
    cmds.connectAttr(f'{bm}.outputMatrix',
                     f'{temp_jnt}.offsetParentMatrix', force=True)

    _msg('<hl>Phase 3 complete!</hl>  '
         'Temp joint rig wired.  Run Phase 4 for skin weights.')
    print('[Hair Rig] Phase 3 (Temp Joint Rig) complete.')


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4  —  SKIN WEIGHTS  (optional)
# ══════════════════════════════════════════════════════════════════════════════

def _find_latest_ngskin_file(directory, prefix):
    """
    Scan `directory` for .json files whose name contains `prefix`.
    Returns the path of the most recently modified match, or None.
    """
    if not os.path.isdir(directory):
        return None
    matches = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith('.json') and prefix in f
    ]
    if not matches:
        return None
    matches.sort(key=os.path.getmtime, reverse=True)
    return matches[0]


def run_phase4(full_name, use_ngskin, ngskin_path, temp_jnt=''):
    """
    Create a skinCluster on the hair mesh using IK joints from Phase 1.
    If temp_jnt is provided and exists, it is added as an influence.
    Optionally imports the newest matching ngSkinTools2 .json weight file.
    """
    hair_mesh = full_name   # e.g. 'F_Hair'  or  'Hair'

    if not cmds.objExists(hair_mesh):
        cmds.warning(
            f'[Hair Rig] Hair mesh "{hair_mesh}" not found. '
            'Check Base Name in Global Settings.')
        return

    # Gather IK joints
    jnt_lis = cmds.ls(f'{full_name}_ik_*_jnt_*') or []
    if temp_jnt and cmds.objExists(temp_jnt):
        jnt_lis.append(temp_jnt)

    if not jnt_lis:
        cmds.warning(
            f'[Hair Rig] No IK joints found for "{full_name}". '
            'Run Phase 1 first.')
        return

    # Unbind existing skinCluster, then rebind
    sc_name = f'{full_name}_skinCluster'
    try:
        cmds.skinCluster(sc_name, ub=True, e=True)
        print(f'[Hair Rig] Removed existing skinCluster: {sc_name}')
    except Exception:
        pass   # no existing cluster — that's fine

    cmds.skinCluster(hair_mesh, jnt_lis, tsb=True, n=sc_name)
    print(f'[Hair Rig] Created skinCluster: {sc_name}')

    # ── Optional ngSkin import ────────────────────────────────────────────────
    if use_ngskin:
        if not _HAS_NGSKIN:
            cmds.warning('[Hair Rig] ngSkinTools2 not loaded — weight import skipped.')
        elif not ngskin_path:
            cmds.warning('[Hair Rig] No ngSkin data path set — weight import skipped.')
        else:
            latest = _find_latest_ngskin_file(ngskin_path, full_name)
            if latest:
                config = InfluenceMappingConfig()
                config.use_distance_matching = True
                config.use_name_matching     = False
                ngst_api.import_json(
                    hair_mesh,
                    file=latest,
                    vertex_transfer_mode=VertexTransferMode.closestPoint,
                    influences_mapping_config=config,
                )
                print(f'[Hair Rig] Imported ngSkin weights: {latest}')
            else:
                cmds.warning(
                    f'[Hair Rig] No matching .json found in "{ngskin_path}" '
                    f'for "{full_name}".')

    _msg('<hl>Phase 4 complete!</hl>  Skin weights applied.')
    print('[Hair Rig] Phase 4 complete.')


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5  —  FK CONTROLLER LAYER
# ══════════════════════════════════════════════════════════════════════════════

def build_fk_layer(full_name, head_joint, ctrl_scale):
    """
    Build a layer of FK nurbsCircle controllers on top of the IK joint chains
    produced by Phase 1.

    Hierarchy per IK chain
    ──────────────────────
    {full_name}_fk_master_grp          (matched to head_joint, then live
    │                                   parentConstraint ← head_joint)
      └─ {chain}_fk_offset_1_grp      position: matchTransform to IK jnt 1
           │                           rotate:   decomposeMatrix ← IK_jnt_1.matrix
           └─ {chain}_fk_ctrl_1       (nurbsCircle, add FK offsets here)
                └─ {chain}_fk_offset_2_grp
                     └─ {chain}_fk_ctrl_2
                          └─ ...

    FK joints live in a separate chain under {full_name}_fk_jnt_grp.
    Each FK joint is parent-constrained (mo=True) to its FK controller.

    FK master group tracking
    ─────────────────────────
    master_grp is first matched to head_joint (zero offset), then a
    parentConstraint(head_joint, master_grp, mo=True) is applied so the
    entire FK layer follows the character's head movement live.

    Rotation via decomposeMatrix
    ─────────────────────────────
    Each FK offset group's rotation is driven by a decomposeMatrix node that
    reads the corresponding IK joint's DAG local matrix (.matrix).  The position
    is baked at build time via matchTransform so no offsetParentMatrix is needed.
    """
    # ── Validate ──────────────────────────────────────────────────────────────
    if not cmds.objExists(head_joint):
        cmds.error(f'[Hair Rig] Head joint "{head_joint}" not found in scene.')
        return

    ik_crv_lis = _load('_hairRig_ik_crv')
    if not ik_crv_lis:
        cmds.error('[Hair Rig] No Phase 1 data found. Run Phase 1 first.')
        return

    # ── Master FK group ───────────────────────────────────────────────────────
    master_name = f'{full_name}_fk_master_grp'
    if cmds.objExists(master_name):
        cmds.delete(master_name)
    master_grp = cmds.group(em=True, w=True, name=master_name)
    # Match first so the constraint has zero offset, then constrain live
    cmds.matchTransform(master_grp, head_joint, pos=True, rot=True, scl=False)
    cmds.parentConstraint(head_joint, master_grp, mo=True)

    # ── FK joint group ────────────────────────────────────────────────────────
    fk_jnt_grp_name = f'{full_name}_fk_jnt_grp'
    if cmds.objExists(fk_jnt_grp_name):
        cmds.delete(fk_jnt_grp_name)
    fk_jnt_grp = cmds.group(em=True, w=True, name=fk_jnt_grp_name)

    total_chains = 0

    for ik_crv in ik_crv_lis:
        ik_base = ik_crv.replace('_crv', '')       # e.g.  F_Hair_01_ik
        fk_base = ik_base.replace('_ik', '_fk')    # e.g.  F_Hair_01_fk

        # Collect the IK joints that actually exist for this chain
        valid_joints = []
        for j in range(1, 8):
            ik_jnt = f'{ik_base}_jnt_{j}'
            if cmds.objExists(ik_jnt):
                valid_joints.append((j, ik_jnt))

        if not valid_joints:
            cmds.warning(f'[Hair Rig] No IK joints for "{ik_base}" — skipping chain.')
            continue

        # ── Create FK joints matched to IK joints ─────────────────────────────
        fk_jnt_list = []
        for j, ik_jnt in valid_joints:
            ws_pos = cmds.xform(ik_jnt, q=True, ws=True, t=True)
            ws_rot = cmds.xform(ik_jnt, q=True, ws=True, ro=True)
            cmds.select(clear=True)
            fk_jnt = cmds.joint(name=f'{fk_base}_jnt_{j}', position=ws_pos)
            cmds.xform(fk_jnt, ws=True, ro=ws_rot)
            fk_jnt_list.append(fk_jnt)

        # Parent FK joints into a chain, root under fk_jnt_grp
        for i in range(1, len(fk_jnt_list)):
            cmds.parent(fk_jnt_list[i], fk_jnt_list[i - 1])
        cmds.parent(fk_jnt_list[0], fk_jnt_grp)

        # ── Build FK controller + offset group nested chain ───────────────────
        parent_node = master_grp   # offset group 1 lives directly under master

        for j, ik_jnt in valid_joints:
            fk_jnt          = f'{fk_base}_jnt_{j}'
            offset_grp_name = f'{fk_base}_offset_{j}_grp'
            ctrl_name       = f'{fk_base}_ctrl_{j}'
            dm_name         = f'{fk_base}_offset_{j}_dm'

            # FK offset group — match world position to IK joint, then parent.
            # Using default (non-relative) parent so world position is preserved
            # as local translate within parent_node.
            offset_grp = cmds.group(em=True, w=True, name=offset_grp_name)
            cmds.matchTransform(offset_grp, ik_jnt, pos=True, rot=False, scl=False)
            cmds.parent(offset_grp, parent_node)

            # Wire rotation via decomposeMatrix reading the IK joint's local
            # matrix (.matrix = transform relative to its own IK parent).
            # Zero the local rotate first so the decomposeMatrix drives cleanly.
            if cmds.objExists(dm_name):
                cmds.delete(dm_name)
            dm = cmds.createNode('decomposeMatrix', name=dm_name)
            cmds.connectAttr(f'{ik_jnt}.matrix', f'{dm}.inputMatrix')
            cmds.setAttr(f'{offset_grp}.rotate', 0.0, 0.0, 0.0, type='double3')
            cmds.connectAttr(f'{dm}.outputRotate', f'{offset_grp}.rotate')

            # FK controller — default nurbsCircle, no construction history.
            cmds.select(clear=True)
            ctrl = cmds.circle(name=ctrl_name, r=ctrl_scale, ch=False)[0]
            cmds.parent(ctrl, offset_grp, relative=True)

            # Parent constraint: FK controller → FK joint (maintain offset)
            cmds.parentConstraint(ctrl, fk_jnt, mo=True)

            # The NEXT offset group will be a child of this controller,
            # creating the cascading:  offset → ctrl → offset → ctrl → ...
            parent_node = ctrl

        total_chains += 1

    _msg(f'<hl>Phase 5 complete!</hl>  FK layer built for {total_chains} chain(s).')
    print(f'[Hair Rig] Phase 5 (FK Layer) complete — {total_chains} chain(s).')


# ══════════════════════════════════════════════════════════════════════════════
# UI  —  BUILD
# ══════════════════════════════════════════════════════════════════════════════

def _lbl(text, bold=False, indent=0):
    """Convenience: add a left-aligned text label."""
    prefix = ' ' * indent
    fn     = 'smallBoldLabelFont' if bold else 'smallPlainLabelFont'
    cmds.text(label=prefix + text, align='left', fn=fn)


def _sep(height=8, style='in'):
    cmds.separator(height=height, style=style)


def _browse_folder(field_ctrl):
    """Open a folder browser and write the result into `field_ctrl`."""
    result = cmds.fileDialog2(fileMode=3, caption='Select Folder', okCaption='Select')
    if result:
        cmds.textFieldButtonGrp(field_ctrl, e=True, text=result[0])


def build_ui():
    if cmds.window(_WIN_ID, exists=True):
        cmds.deleteUI(_WIN_ID)

    win = cmds.window(
        _WIN_ID,
        title='Hair Rig Setup',
        widthHeight=(_WIN_W, 1200),
        sizeable=True,
    )

    cmds.scrollLayout(horizontalScrollBarThickness=0, childResizable=True)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    # ── HEADER ────────────────────────────────────────────────────────────────
    _sep(6, 'none')
    cmds.text(label='Hair Rig Setup', font='boldLabelFont', align='center')
    cmds.text(
        label='Follow PREP → Phase 1 → PAUSE → Phase 2 → Phase 3 → Phase 4.',
        align='center', fn='smallPlainLabelFont')
    _sep(8, 'in')

    # ══════════════════════════════════════════════════════════════════════════
    # GLOBAL SETTINGS
    # ══════════════════════════════════════════════════════════════════════════
    cmds.frameLayout(
        label='  ⚙  Global Settings',
        collapsable=True, collapse=False,
        marginHeight=8, marginWidth=8, borderStyle='etchedIn')
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    _lbl('These values are shared across all phases.')
    _sep(4, 'none')

    base_ctrl = cmds.textFieldGrp(
        label='Base Name:',
        text='Hair',
        columnWidth2=(_LBL_W, _FLD_W),
        annotation=(
            'Root identifier for this hair group.\n'
            'e.g.  Hair  |  F_Hair  |  Tail  |  Braid\n'
            'This becomes the full name used for all generated nodes.'))

    _sep(4, 'none')

    proxy_ctrl = cmds.textFieldButtonGrp(
        label='Hair Base Proxy:',
        text='hair_base_proxy',
        buttonLabel='Pick ←',
        columnWidth3=(_LBL_W, _FLD_W - _BTN_W, _BTN_W),
        annotation=(
            'Name of the clean, single-sided proxy mesh.\n'
            'Follicles will be attached to this surface.\n'
            'Select the mesh then click "Pick ←" to fill automatically.'))
    cmds.textFieldButtonGrp(
        proxy_ctrl, e=True,
        bc=lambda: cmds.textFieldButtonGrp(
            proxy_ctrl, e=True,
            text=(cmds.ls(sl=True, objectsOnly=True) or [''])[0]))

    _sep(4, 'none')

    head_jnt_ctrl = cmds.textFieldButtonGrp(
        label='Head Joint (FK):',
        text='',
        buttonLabel='Pick ←',
        columnWidth3=(_LBL_W, _FLD_W - _BTN_W, _BTN_W),
        annotation=(
            'Character skull / head joint.\n'
            'The FK master group and IK joint group are both matched to this\n'
            'joint in Phase 1 and Phase 5.  Select the joint then click "Pick ←".'))
    cmds.textFieldButtonGrp(
        head_jnt_ctrl, e=True,
        bc=lambda: cmds.textFieldButtonGrp(
            head_jnt_ctrl, e=True,
            text=(cmds.ls(sl=True, objectsOnly=True) or [''])[0]))

    _sep(4, 'none')

    temp_jnt_ctrl = cmds.textFieldButtonGrp(
        label='Temp Hair Joint:',
        text='temp_hair_jnt',
        buttonLabel='Pick ←',
        columnWidth3=(_LBL_W, _FLD_W - _BTN_W, _BTN_W),
        annotation=(
            'Joint used as the IK-twist world-up object (Phase 2) and\n'
            'wired to track the "Main" controller via blendMatrix (Phase 3).\n'
            'Select the joint then click "Pick ←".'))
    cmds.textFieldButtonGrp(
        temp_jnt_ctrl, e=True,
        bc=lambda: cmds.textFieldButtonGrp(
            temp_jnt_ctrl, e=True,
            text=(cmds.ls(sl=True, objectsOnly=True) or [''])[0]))

    cmds.setParent('..')   # columnLayout
    cmds.setParent('..')   # frameLayout

    # ══════════════════════════════════════════════════════════════════════════
    # PREP  —  CURVE TOOLS
    # ══════════════════════════════════════════════════════════════════════════
    cmds.frameLayout(
        label='  PREP  —  Curve Generation & Cleanup',
        collapsable=True, collapse=False,
        marginHeight=8, marginWidth=8, borderStyle='etchedIn')
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    _lbl('① Generate a start curve from selected poly edges:', bold=True)
    _lbl('   Select a continuous edge loop along the hair strand length.', indent=0)
    _lbl('   The curve will be rebuilt to degree 3 with the span count below.', indent=0)
    _sep(6, 'in')

    gen_spans_ctrl = cmds.intSliderGrp(
        label='Curve Spans:',
        field=True,
        value=6, minValue=2, maxValue=20,
        fieldMinValue=2, fieldMaxValue=50,
        columnWidth3=(_LBL_W, 50, _FLD_W),
        annotation='Number of spans (CV sections) for the generated curve.')

    cmds.button(
        label='  Generate Curve from Selected Edge(s)  ',
        height=_BTN_H,
        backgroundColor=_COL_GREEN,
        command=lambda _: generate_curve_from_edge(
            cmds.intSliderGrp(gen_spans_ctrl, q=True, value=True)))

    _sep(10, 'in')
    _lbl('② Edit existing curves:', bold=True)

    rebuild_spans_ctrl = cmds.intSliderGrp(
        label='Rebuild Spans:',
        field=True,
        value=6, minValue=2, maxValue=20,
        fieldMinValue=2, fieldMaxValue=50,
        columnWidth3=(_LBL_W, 50, _FLD_W),
        annotation='Number of spans for the Rebuild operation.')

    cmds.rowLayout(numberOfColumns=2, columnWidth2=((_WIN_W - 32) // 2,
                                                    (_WIN_W - 32) // 2))
    cmds.button(
        label='Rebuild Selected Curves',
        height=_BTN_H,
        backgroundColor=_COL_MUTE,
        command=lambda _: rebuild_curves(
            cmds.intSliderGrp(rebuild_spans_ctrl, q=True, value=True)))
    cmds.button(
        label='Reverse Selected Curves',
        height=_BTN_H,
        backgroundColor=_COL_RED,
        command=lambda _: reverse_curves())
    cmds.setParent('..')

    cmds.setParent('..')   # columnLayout
    cmds.setParent('..')   # frameLayout

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 1
    # ══════════════════════════════════════════════════════════════════════════
    cmds.frameLayout(
        label='  PHASE 1  —  IK Spline Joint Chains',
        collapsable=True, collapse=False,
        marginHeight=8, marginWidth=8, borderStyle='etchedIn')
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    _lbl('Before running Phase 1:', bold=True)
    _lbl('  • All start curves must contain "start" in their name.')
    _lbl('      e.g.  hair_start_crv_1   or   F_Hair_01_start_crv')
    _lbl('  • The scene should have no stray joints named "joint1"–"joint7",')
    _lbl('    as bonesOnCurve will create joints with those default names.')
    _lbl('  • Select ALL start curves in the viewport, then click Run.')
    _sep(6, 'in')

    cmds.button(
        label='Run Phase 1  ▶  Build IK Spline Joints',
        height=_BTN_H_LG,
        backgroundColor=_COL_BLUE,
        command=lambda _: run_phase1(
            _get_name(base_ctrl),
            cmds.textFieldButtonGrp(head_jnt_ctrl, q=True, text=True)))

    cmds.setParent('..')
    cmds.setParent('..')

    # ══════════════════════════════════════════════════════════════════════════
    # PAUSE CARD
    # ══════════════════════════════════════════════════════════════════════════
    cmds.frameLayout(
        label='  ⏸  PAUSE  —  Simulate & Review  (required before Phase 2)',
        collapsable=True, collapse=False,
        marginHeight=8, marginWidth=8, borderStyle='etchedIn',
        backgroundColor=_COL_WARN)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=3)

    cmds.text(label='  ⚠  Do NOT run Phase 2 yet.', align='left',
              font='boldLabelFont')
    _sep(4, 'none')
    _lbl('  After Phase 1 completes, do the following:')
    _lbl('  1.  Press Play (▶) to run the simulation forward several frames.')
    _lbl('  2.  Observe the dyna curves — check that motion looks natural.')
    _lbl('  3.  Adjust the Hair System stiffness / attraction values if needed.')
    _lbl('  4.  Reshape any dyna curves via their CVs if the sim still looks off.')
    _lbl('  5.  Scrub the timeline back to frame 1.')
    _lbl('  6.  Return here and click Run Phase 2 when satisfied.')

    cmds.setParent('..')
    cmds.setParent('..')

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 2
    # ══════════════════════════════════════════════════════════════════════════
    cmds.frameLayout(
        label='  PHASE 2  —  Dynamic Hair & Follicle Setup',
        collapsable=True, collapse=False,
        marginHeight=8, marginWidth=8, borderStyle='etchedIn')
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    _lbl('Before running Phase 2:', bold=True)
    _lbl('  • Timeline must be at frame 1.')
    _lbl('  • The proxy mesh name in Global Settings must match a mesh in the scene.')
    _lbl('  • Set "Temp Hair Joint" in Global Settings for IK twist control.')
    _sep(4, 'none')
    _lbl('What Phase 2 creates:', bold=True)
    _lbl('  • Follicles + output curves attached to proxy mesh.')
    _lbl('  • BlendShape per IK curve: output_crv (target 0) + start_crv (target 1).')
    _lbl('  • Nucleus condition node to switch between output and start curves.')
    _sep(6, 'in')

    cmds.button(
        label='Run Phase 2  ▶  Make Dynamic + Attach Follicles',
        height=_BTN_H_LG,
        backgroundColor=_COL_BLUE,
        command=lambda _: run_phase2(
            cmds.textFieldButtonGrp(proxy_ctrl,    q=True, text=True),
            _get_name(base_ctrl),
            cmds.textFieldButtonGrp(temp_jnt_ctrl, q=True, text=True)))

    cmds.setParent('..')
    cmds.setParent('..')

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 3  —  TEMP JOINT RIG
    # ══════════════════════════════════════════════════════════════════════════
    cmds.frameLayout(
        label='  PHASE 3  —  Temp Joint Rig',
        collapsable=True, collapse=False,
        marginHeight=8, marginWidth=8, borderStyle='etchedIn')
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    _lbl('Wires the Temp Hair Joint to track the "Main" controller.', bold=True)
    _sep(4, 'none')
    _lbl('  The temp joint provides a stable world-up axis for the IK twist')
    _lbl('  control set up in Phase 2.  A blendMatrix + multMatrix network')
    _lbl('  drives its offsetParentMatrix so it follows "Main" when the nucleus')
    _lbl('  simulation is active, and rests at a fixed position when sim is off.')
    _sep(6, 'in')
    _lbl('Before running Phase 3:', bold=True)
    _lbl('  • Phase 2 must have been run (nucleus condition node must exist).')
    _lbl('  • A controller named exactly "Main" must exist in the scene.')
    _lbl('  • The Temp Hair Joint must be set in Global Settings.')
    _sep(6, 'in')

    cmds.button(
        label='Run Phase 3  ▶  Wire Temp Joint Rig',
        height=_BTN_H_LG,
        backgroundColor=_COL_BLUE,
        command=lambda _: build_temp_jnt_rig(
            cmds.textFieldButtonGrp(temp_jnt_ctrl, q=True, text=True),
            _get_name(base_ctrl)))

    cmds.setParent('..')
    cmds.setParent('..')

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 4  —  SKIN WEIGHTS
    # ══════════════════════════════════════════════════════════════════════════
    cmds.frameLayout(
        label='  PHASE 4  —  Skin Weights  (optional)',
        collapsable=True, collapse=False,
        marginHeight=8, marginWidth=8, borderStyle='etchedIn')
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    _lbl('Creates a skinCluster on the hair mesh using the IK joints from Phase 1.')
    _lbl('Any existing skinCluster on that mesh will be replaced.')
    _lbl('Optionally imports the newest ngSkinTools2 .json for this hair section.')
    _sep(6, 'in')

    ng_check_ctrl = cmds.checkBoxGrp(
        label='Import ngSkin Weights:',
        value1=False,
        enable=_HAS_NGSKIN,
        columnWidth2=(_LBL_W, 20),
        annotation=(
            'Requires the ngSkinTools2 plugin to be loaded.'
            if not _HAS_NGSKIN else
            'Import the newest matching .json weight file for this hair section.'))

    ngskin_path_ctrl = cmds.textFieldButtonGrp(
        label='ngSkin Data Path:',
        text='',
        buttonLabel='Browse',
        enable=_HAS_NGSKIN,
        columnWidth3=(_LBL_W, _FLD_W - _BTN_W, _BTN_W),
        annotation='Folder containing .json ngSkinTools2 weight files.')
    cmds.textFieldButtonGrp(
        ngskin_path_ctrl, e=True,
        bc=lambda: _browse_folder(ngskin_path_ctrl))

    if not _HAS_NGSKIN:
        cmds.text(
            label='  ⚠  ngSkinTools2 is not loaded — weight import disabled.',
            align='left', font='smallBoldLabelFont')

    _sep(6, 'in')

    cmds.button(
        label='Run Phase 4  ▶  Apply Skin Weights',
        height=_BTN_H_LG,
        backgroundColor=_COL_BLUE,
        command=lambda _: run_phase4(
            _get_name(base_ctrl),
            cmds.checkBoxGrp(ng_check_ctrl,       q=True, value1=True),
            cmds.textFieldButtonGrp(ngskin_path_ctrl, q=True, text=True),
            cmds.textFieldButtonGrp(temp_jnt_ctrl, q=True, text=True)))

    cmds.setParent('..')
    cmds.setParent('..')

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 5  —  FK CONTROLLER LAYER
    # ══════════════════════════════════════════════════════════════════════════
    cmds.frameLayout(
        label='  PHASE 5  —  FK Controller Layer',
        collapsable=True, collapse=False,
        marginHeight=8, marginWidth=8, borderStyle='etchedIn')
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    _lbl('Builds nurbsCircle FK controllers on top of every IK joint chain', bold=True)
    _lbl('built in Phase 1.  Run Phase 1 before using this phase.')
    _sep(6, 'in')

    _lbl('What gets created:', bold=True)
    _lbl('  {name}_fk_master_grp          matched to Head Joint, then live')
    _lbl('  │                             parentConstraint ← Head Joint')
    _lbl('    └─  {chain}_fk_offset_1_grp   pos: matchTransform to IK jnt 1')
    _lbl('    │                              rot: decomposeMatrix ← IK_jnt_1.matrix')
    _lbl('          └─  {chain}_fk_ctrl_1   nurbsCircle  (add FK offsets here)')
    _lbl('                └─  {chain}_fk_offset_2_grp   ← IK_jnt_2.matrix')
    _lbl('                      └─  {chain}_fk_ctrl_2  …  (repeats for all 7 joints)')
    _lbl('  {name}_fk_jnt_grp             chain of FK joints, each parent-constrained')
    _lbl('                               to its corresponding FK controller.')
    _sep(6, 'in')

    _lbl('Before running Phase 5:', bold=True)
    _lbl('  • Phase 1 must have been run (IK joints must exist in the scene).')
    _lbl('  • "Head Joint (FK)" in Global Settings must name a valid joint.')
    _sep(6, 'in')

    fk_scale_ctrl = cmds.floatSliderGrp(
        label='Controller Scale:',
        field=True,
        value=1.0, minValue=0.1, maxValue=10.0,
        fieldMinValue=0.01, fieldMaxValue=100.0,
        columnWidth3=(_LBL_W, 55, _FLD_W - 25),
        annotation='Radius of each nurbsCircle FK controller.')

    _sep(6, 'in')

    cmds.button(
        label='Run Phase 5  ▶  Build FK Layer',
        height=_BTN_H_LG,
        backgroundColor=_COL_BLUE,
        command=lambda _: build_fk_layer(
            _get_name(base_ctrl),
            cmds.textFieldButtonGrp(head_jnt_ctrl, q=True, text=True),
            cmds.floatSliderGrp(fk_scale_ctrl,     q=True, value=True)))

    cmds.setParent('..')
    cmds.setParent('..')

    # ── FOOTER ────────────────────────────────────────────────────────────────
    _sep(6, 'in')
    cmds.text(
        label='Hair Rig Setup  |  CW Maya Rigging Tools',
        align='center', fn='smallPlainLabelFont')
    _sep(8, 'none')

    cmds.showWindow(win)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

build_ui()
