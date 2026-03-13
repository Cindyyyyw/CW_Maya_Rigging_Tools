import sys
_dir = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/facialRig'
if _dir not in sys.path:
    sys.path.insert(0, _dir)
import ARKitBSBuilder
ARKitBSBuilder.show()
