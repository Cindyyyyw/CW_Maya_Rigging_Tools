"""ARKit BlendShape Builder — backward-compatible entry point.

This shim re-exports everything from the split modules so that existing
code using ``import ARKitBSBuilder`` continues to work without changes.

To open the tool from Maya's Script Editor::

    import ARKitBSBuilder
    ARKitBSBuilder.show()

Module layout
─────────────
    bs_builder.py    — BSBuilder class, symmetry check, flip/split utilities
    muscle_joints.py — MuscleJointBuilder class, follicle helpers
    ui.py            — BSBuilderUI dialog, _CollapsibleSection, show()
"""

import sys
import os

# Ensure this file's directory (facialRig/) is on sys.path so the sibling
# modules can be imported even if they have not been added to MAYA_SCRIPT_PATH.
try:
    _PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback for the rare case where __file__ is unavailable (e.g. execfile)
    _PACKAGE_DIR = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/facialRig'

if _PACKAGE_DIR not in sys.path:
    sys.path.insert(0, _PACKAGE_DIR)

# ── Backend re-exports ────────────────────────────────────────────────────────
from bs_builder import (           # noqa: E402
    BSBuilder,
    check_symmetry,
    flip_target,
    split_by_weight_mask,
    path,
    _maya_main_window,
    _AXIS_IDX,
)

# ── Muscle joint re-exports ───────────────────────────────────────────────────
from muscle_joints import (        # noqa: E402
    MuscleJointBuilder,
    _muscle_json_default,
    _closest_uv_on_mesh,
    _create_follicle,
)

# ── UI re-exports ─────────────────────────────────────────────────────────────
from ui import (                   # noqa: E402
    _CollapsibleSection,
    BSBuilderUI,
    show,
)

__all__ = [
    # Backend
    'BSBuilder',
    'check_symmetry',
    'flip_target',
    'split_by_weight_mask',
    'path',
    # Muscle joints
    'MuscleJointBuilder',
    '_muscle_json_default',
    # UI
    'BSBuilderUI',
    'show',
]
