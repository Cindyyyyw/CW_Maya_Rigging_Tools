import sys
_dir = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/facialRig'
if _dir not in sys.path:
    sys.path.insert(0, _dir)
import ui
ui.show()
# Switch straight to the Muscle Joints tab (index 2)
ui._window_instance.findChild(ui.QtWidgets.QTabWidget).setCurrentIndex(2)
