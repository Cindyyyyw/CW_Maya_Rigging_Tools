"""Facial muscle joint builder — follicle utilities and MuscleJointBuilder class.

This module is standalone (no imports from other project files).
"""

import maya.cmds as cmds
import json
import os

try:
    _muscle_json_default = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'FacialMuscleJoints.json'
    )
except NameError:
    _muscle_json_default = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/facialRig/FacialMuscleJoints.json'


# ─────────────────────────────────────────────────────────────────────────────
#  Follicle utilities
# ─────────────────────────────────────────────────────────────────────────────

def _closest_uv_on_mesh(mesh, world_pos):
    """Return (u, v) on *mesh* closest to *world_pos*. Falls back to (0.5, 0.5)."""
    try:
        import maya.api.OpenMaya as om2
        sel = om2.MSelectionList()
        sel.add(mesh)
        dag = sel.getDagPath(0)
        fn = om2.MFnMesh(dag)
        pt = om2.MPoint(world_pos[0], world_pos[1], world_pos[2])
        closest, _ = fn.getClosestPoint(pt, om2.MSpace.kWorld)
        u, v = fn.getUVAtPoint(closest, om2.MSpace.kWorld)
        return u, v
    except Exception:
        return 0.5, 0.5


def _create_follicle(mesh, u, v, name):
    """Create a follicle on *mesh* at UV *(u, v)*. Returns the follicle transform name."""
    shapes = cmds.listRelatives(mesh, shapes=True, noIntermediate=True) or []
    mesh_shape = shapes[0] if shapes else mesh

    foll_shape = cmds.createNode('follicle', name=f'{name}Shape')
    foll_xform = cmds.listRelatives(foll_shape, parent=True)[0]
    foll_xform = cmds.rename(foll_xform, name)

    cmds.connectAttr(f'{mesh_shape}.outMesh',        f'{foll_shape}.inputMesh')
    cmds.connectAttr(f'{mesh}.worldMatrix[0]',       f'{foll_shape}.inputWorldMatrix')
    cmds.connectAttr(f'{foll_shape}.outTranslate',   f'{foll_xform}.translate')
    cmds.connectAttr(f'{foll_shape}.outRotate',      f'{foll_xform}.rotate')

    cmds.setAttr(f'{foll_shape}.parameterU', u)
    cmds.setAttr(f'{foll_shape}.parameterV', v)
    return foll_xform


# ─────────────────────────────────────────────────────────────────────────────
#  Muscle joint builder
# ─────────────────────────────────────────────────────────────────────────────

class MuscleJointBuilder:
    """Two-stage facial muscle joint setup driven by a JSON guide definition.

    Stage 1 — create_guides(): places locators in world space by converting
    head-joint-local positions stored in the JSON.

    Stage 2 — build_joints(): reads guide positions and builds a hierarchy of
    follicle → offset_grp → (ctrl + joint) under a master group that inherits
    the head joint's world matrix via offsetParentMatrix.
    """

    def __init__(self, json_path):
        self.json_path   = json_path
        self._raw_data   = {}
        self.joint_grp      = []   # list of lists of entry dicts
        self.joint_grp_keys = []   # parallel list of group name strings

    def load_joints(self, filter_groups=None):
        """Load joint data from JSON.

        Args:
            filter_groups (dict | None): {group_name: [entry_name, ...]}
                Pass None to load everything.
        """
        self.joint_grp      = []
        self.joint_grp_keys = []

        with open(self.json_path, 'r') as f:
            raw = json.load(f)
        self._raw_data = raw.get('FacialMuscleJoints', {})

        for group, entries in self._raw_data.items():
            if filter_groups is not None:
                if group not in filter_groups:
                    continue
                allowed = set(filter_groups[group])
                entries = [e for e in entries if e['name'] in allowed]
                if not entries:
                    continue
            self.joint_grp.append(list(entries))
            self.joint_grp_keys.append(group)

    def create_guides(self, head_jnt, prefix, generate_side=True,
                      existing_top_grp=None, lateral_axis=0, uniform_x=False):
        """Create or add guide locators converted from head-joint-local space to world.

        If *existing_top_grp* is supplied (and exists in the scene) the new
        locators are placed inside that group.  Per-group sub-groups are also
        reused when they already exist.  Any individual locator whose name is
        already present in the scene is skipped, so the call is safe to run
        multiple times with different joint selections.

        Args:
            lateral_axis (int): Identifies the scene mirror plane for bilateral
                joints — 0=YZ plane (default, negate world X), 1=XZ plane
                (negate world Y), 2=XY plane (negate world Z).
                Position: the component at *lateral_axis* is negated.
                Rotation: all components *except* lateral_axis are negated,
                preserving the X-primary roll of the locator on both sides.
            uniform_x (bool): When True the R-side locator is given an extra
                180° rotation around its local Z axis after mirroring.  This
                makes both sides' local X axes point in the same world
                direction so a +X translation on L and R both move "outward".
                When False (default) the orientations are a true mirror image.

        Returns:
            str: top guide group name.
        """
        p            = f'{prefix}_' if prefix else ''
        top_grp_name = f'{p}muscle_guides_grp'

        # Reuse an existing top group or create a fresh one
        if existing_top_grp and cmds.objExists(existing_top_grp):
            top_grp = existing_top_grp
        elif cmds.objExists(top_grp_name):
            top_grp = top_grp_name
        else:
            top_grp = cmds.group(empty=True, name=top_grp_name)

        for group_key, entries in zip(self.joint_grp_keys, self.joint_grp):
            grp_name = f'{p}{group_key}_guides_grp'
            if cmds.objExists(grp_name):
                grp = grp_name
            else:
                grp = cmds.group(empty=True, name=grp_name)
                cmds.parent(grp, top_grp)

            for entry in entries:
                name    = entry['name']
                local_t = entry['translate']
                local_r = entry['rotate']
                is_dir  = name.endswith('_DIR_')
                base    = name[:-5] if is_dir else name

                # Resolve the L-side (or single) world transform once via a
                # temp locator parented under head_jnt.
                tmp = cmds.spaceLocator(name='_tmp_guide_resolve')[0]
                cmds.parent(tmp, head_jnt)
                cmds.setAttr(f'{tmp}.translate',
                             local_t[0], local_t[1], local_t[2], type='double3')
                cmds.setAttr(f'{tmp}.rotate',
                             local_r[0], local_r[1], local_r[2], type='double3')
                wt_l = cmds.xform(tmp, q=True, ws=True, translation=True)
                wr_l = cmds.xform(tmp, q=True, ws=True, rotation=True)
                cmds.delete(tmp)

                if is_dir and generate_side:
                    # Position: negate the mirror-plane normal component.
                    wt_r = list(wt_l)
                    wt_r[lateral_axis] = -wt_r[lateral_axis]

                    if uniform_x:
                        # Replicates Maya's "parent inside a group whose
                        # lateral axis is scaled by -1" technique, which the
                        # user confirmed produces correct results.
                        #
                        # Reverse-engineered from empirical data:
                        #   L rot = [22.269, 13.927, 100.158]
                        #   R rot = [157.731, 13.927,  79.842]
                        # Rule: keep component (lateral_axis+1)%3 unchanged;
                        #       apply (180 - value) to the other two.
                        #
                        # For YZ plane (lateral_axis=0): keep ry, 180-rx, 180-rz
                        # For XZ plane (lateral_axis=1): keep rz, 180-rx, 180-ry
                        # For XY plane (lateral_axis=2): keep rx, 180-ry, 180-rz
                        keep = (lateral_axis + 1) % 3
                        wr_r = [
                            wr_l[i] if i == keep else (180.0 - wr_l[i])
                            for i in range(3)
                        ]
                    else:
                        # True orientation mirror: negate every rotation
                        # component except the one along the plane normal.
                        wr_r = list(wr_l)
                        for i in range(3):
                            if i != lateral_axis:
                                wr_r[i] = -wr_r[i]

                    sides = [('L', wt_l, wr_l), ('R', wt_r, wr_r)]
                elif is_dir:
                    sides = [('L', wt_l, wr_l)]
                else:
                    sides = [(None, wt_l, wr_l)]

                for side, wt, wr in sides:
                    loc_name = (f'{p}{base}_{side}_guide' if side
                                else f'{p}{base}_guide')

                    # Skip locators that already exist in the scene
                    if cmds.objExists(loc_name):
                        continue

                    loc = cmds.spaceLocator(name=loc_name)[0]
                    cmds.xform(loc, ws=True, translation=wt)
                    cmds.xform(loc, ws=True, rotation=wr)
                    cmds.setAttr(f'{loc}.displayLocalAxis', True)
                    cmds.parent(loc, grp)

        return top_grp

    def build_joints(self, face_geo, head_jnt, prefix, guides_grp):
        """Build joints/controls/follicles from current guide positions.

        Hierarchy per guide:
            {p}face_muscles_master_grp  [offsetParentMatrix ← headJnt.worldMatrix[0]]
              └── {base}_foll
                    └── {base}_offset_grp  (oriented to guide world rotation)
                          ├── {base}_ctrl  (NURBS sphere r=0.3)
                          └── {base}_jnt   (ctrl.t/r/s → jnt.t/r/s)

            {p}face_root_jnt  [offsetParentMatrix ← headJnt.worldMatrix[0]]

        Returns:
            (str, str): (master_grp_name, face_root_jnt_name)
        """
        p = f'{prefix}_' if prefix else ''

        # Gather *_guide locators
        descendants = (
            cmds.listRelatives(guides_grp, allDescendents=True, type='transform') or []
        )
        guides = [g for g in descendants if g.endswith('_guide')]
        if not guides:
            cmds.warning('MuscleJointBuilder: no *_guide locators found under ' + guides_grp)
            return None, None

        # Master group — inherits head joint world matrix via offsetParentMatrix
        master_grp = cmds.group(empty=True, name=f'{p}face_muscles_master_grp')
        cmds.connectAttr(f'{head_jnt}.worldMatrix[0]', f'{master_grp}.offsetParentMatrix')

        # Face root joint — same matrix inheritance; all muscle joints live under it
        cmds.select(clear=True)
        face_root_jnt = cmds.joint(name=f'{p}face_root_jnt')
        cmds.connectAttr(f'{head_jnt}.worldMatrix[0]', f'{face_root_jnt}.offsetParentMatrix')

        for guide in guides:
            base      = guide.replace('_guide', '')
            world_pos = cmds.xform(guide, q=True, ws=True, translation=True)
            world_rot = cmds.xform(guide, q=True, ws=True, rotation=True)

            # Follicle pinned to face mesh
            u, v = _closest_uv_on_mesh(face_geo, world_pos)
            foll = _create_follicle(face_geo, u, v, f'{base}_foll')
            cmds.parent(foll, master_grp)

            # Offset group at guide world position/rotation, parented under follicle
            offset_grp = cmds.group(empty=True, name=f'{base}_offset_grp')
            cmds.xform(offset_grp, ws=True, translation=world_pos, rotation=world_rot)
            cmds.parent(offset_grp, foll)
            # Re-assert world transform (Maya parent can shift values slightly)
            cmds.xform(offset_grp, ws=True, translation=world_pos, rotation=world_rot)

            # NURBS sphere control sits inside offset_grp
            ctrl = cmds.sphere(radius=0.3, name=f'{base}_ctrl')[0]
            cmds.delete(ctrl, constructionHistory=True)
            cmds.parent(ctrl, offset_grp)
            cmds.setAttr(f'{ctrl}.translate', 0, 0, 0, type='double3')
            cmds.setAttr(f'{ctrl}.rotate',    0, 0, 0, type='double3')

            # Joint lives under face_root_jnt.
            # Use a temp locator parented under face_root_jnt to bake the guide's
            # world transform into the joint's offsetParentMatrix so that at rest
            # the joint sits exactly at the guide with zero local t/r/s.
            tmp = cmds.spaceLocator(name='_tmp_opm_resolve')[0]
            cmds.parent(tmp, face_root_jnt)
            cmds.xform(tmp, ws=True, translation=world_pos, rotation=world_rot)
            local_m = cmds.getAttr(f'{tmp}.matrix')        # flat list of 16 floats
            cmds.delete(tmp)

            cmds.select(clear=True)
            jnt = cmds.joint(name=f'{base}_jnt')
            cmds.parent(jnt, face_root_jnt)
            # offsetParentMatrix = guide transform in face_root_jnt local space
            cmds.setAttr(f'{jnt}.offsetParentMatrix', *local_m, type='matrix')
            cmds.setAttr(f'{jnt}.translate',   0, 0, 0, type='double3')
            cmds.setAttr(f'{jnt}.rotate',      0, 0, 0, type='double3')
            cmds.setAttr(f'{jnt}.jointOrient', 0, 0, 0, type='double3')

            # ctrl drives jnt — local t/r/s from ctrl, position from offsetParentMatrix
            for attr in ('translate', 'rotate', 'scale'):
                cmds.connectAttr(f'{ctrl}.{attr}', f'{jnt}.{attr}', force=True)

        return master_grp, face_root_jnt
