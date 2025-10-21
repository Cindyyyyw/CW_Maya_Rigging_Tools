import maya.cmds as cmds
import maya.mel as mel
import os
from ngSkinTools2 import api as ngst_api
from ngSkinTools2.api import InfluenceMappingConfig, VertexTransferMode
import os.path


hair_pfx_lis = ['F_', 'R_', 'B_', 'LT_', 'L_']

sl = cmds.ls(sl=1)

ik_jnt_grp = cmds.group(em=1, name="hair_ik_jnt_grp")
ik_crv_grp = cmds.group(em=1, name="hair_ik_crv_grp")
ik_hdl_grp = cmds.group(em=1, name="hair_ik_hdl_grp")
ik_hdl_lis = []
dyna_crv_lis = []
ik_crv_lis = []
'''
prerequisite:
- curves placed
- curves rebuild completed
- curves in the correct direction

1. build IK Spline joint chains
- duplicate selected curve
- use bonesOnCurve()
- rename the joints and the ikHandle
- in a ideal and clean environment, new joints would be named joint1-joint7
- ikHandle would be named ikHandle1
- group everything accordingly

2. build dynamic curves with the hair proxy
- duplicate selected curve
- 

'''

for i in range(len(sl)):
    # Build bones on curve: 6 bones, rebuild curve OFF, spline IK ON
    ik_crv = cmds.duplicate(sl[i], name=sl[i].replace("start", "ik"))[0]
    ik_crv_lis.append(ik_crv)
    cmds.select(ik_crv, replace=1)
    mel.eval('bonesOnCurve(6, 0, 1);')
    
    for j in range(1,8):
        cmds.rename('joint'+str(j), ik_crv.replace("crv", 'jnt_')+str(j))
    ik_handle = cmds.rename('ikHandle1', ik_crv.replace("crv", 'ikHandle'))
    
    ik_hdl_lis.append(ik_handle)
    
    cmds.parent(ik_crv.replace("crv", 'jnt_1'), ik_jnt_grp)
    cmds.parent(ik_handle, ik_hdl_grp)
    cmds.parent(ik_crv, ik_crv_grp)
    
    dyna_crv = cmds.duplicate(sl[i], name=sl[i].replace("start", "dyna"))[0]
    cmds.parent(dyna_crv,w=1)
    dyna_crv_lis.append(dyna_crv)

cmds.select(dyna_crv_lis ,replace=1)
cmds.select('hair_base_proxy', add=1)

mel.eval('makeCurvesDynamic 2 { "1", "0", "1", "1", "0"};')
for i in range(len(dyna_crv_lis)):
    output_crv = cmds.rename(f'curve{i+1}', dyna_crv_lis[i].replace("dyna", 'output'))
    flc = cmds.rename(f'follicle{i+1}', dyna_crv_lis[i].replace("_dyna_", '_').replace("crv", "flc"))
    cmds.setAttr(f"{flc}.restPose", 1)
    cmds.setAttr(f"{flc}.startDirection", 1)
    cmds.setAttr(f"{flc}.pointLock", 1)
    # # create blendshape
    cmds.blendShape(output_crv, ik_crv_lis[i], w=[(0,1)])
    
cmds.setAttr('hairSystemShape1.stiffnessScale[0].stiffnessScale_FloatValue', 0.5)

cmds.setAttr('hairSystemShape1.attractionScale[1].attractionScale_FloatValue', 0.1)

cmds.setAttr('hairSystemShape1.attractionScale[2].attractionScale_Position', 0.5)
cmds.setAttr('hairSystemShape1.attractionScale[2].attractionScale_FloatValue', 0.3)
cmds.setAttr('hairSystemShape1.attractionScale[2].attractionScale_Interp', 3)

cmds.setAttr('hairSystemShape1.startCurveAttract', 1)

for ikHandle in ik_hdl_lis:
    cmds.setAttr(f"{ikHandle}.dTwistControlEnable", 1)
    cmds.setAttr(f"{ikHandle}.dWorldUpType", 1)
    cmds.connectAttr('temp_hair_jnt.worldMatrix[0]', f"{ikHandle}.dWorldUpMatrix")


directory_path = "/Volumes/CINDY/Rigging/projects/adult_james/data/ngSkinData"

def find_latest_ngskin_file(directory, prefix):
    """
    Find the newest .json file in the given directory.

    :param str directory: Path to search for .json files.
    :return: Path to the newest .ngskin file or None if none found.
    """
    ngskin_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.json')]
    i=0
    if not ngskin_files:
        return None
    # Sort files by modification time, newest first
    ngskin_files.sort(key=os.path.getmtime, reverse=True)
    result = ''
    for x in ngskin_files:
        if prefix in x:
            result=x
    return result
    
def import_latest_ngskin(mesh_name, directory, prefix):
    """
    Find the newest .ngskin file in the provided directory and import it to the provided mesh.

    :param str mesh_name: Name of the mesh or skin cluster to import layers to.
    :param str directory: Path to search for the .ngskin files.
    """
    latest_file = find_latest_ngskin_file(directory, prefix)
    if not latest_file:
        print("No .json files found in the provided directory.")
        return

    print("Importing {} into {}...".format(latest_file, mesh_name))
    # Set up influence mapping and transfer mode
    config = InfluenceMappingConfig()
    config.use_distance_matching = True
    config.use_name_matching = False
    
    # run the import
    ngst_api.import_json(
    mesh_name,
    file=latest_file,
    vertex_transfer_mode=VertexTransferMode.closestPoint,
    influences_mapping_config=config
)

for i in range(len(hair_pfx_lis)):
    compatible_jnt_lis = cmds.ls(f'{hair_pfx_lis[i]}Hair_ik_*_jnt_*')
    compatible_jnt_lis.append('temp_hair_jnt')
    
    try:
        cmds.skinCluster(f"{hair_pfx_lis[i]}Hair_skinCluster", ub=1,e=1)
    except:
        print(f"{hair_pfx_lis[i]}Hair_skinCluster does not exist")
    
    curr_skinCluster = str(cmds.skinCluster(f"{hair_pfx_lis[i]}Hair", compatible_jnt_lis, tsb=1, n=f"{hair_pfx_lis[i]}Hair_skinCluster")[0])
    import_latest_ngskin(f"{hair_pfx_lis[i]}Hair", directory_path, hair_pfx_lis[i])

