import maya.cmds as cmds

def updateUVFromFile(fileName = 'DannyUV__2_'):
    # update_file_name ='adultJames_uvUpdate'
    source_lis =[x for x in cmds.ls(f'{fileName}:*',type='transform') if cmds.listRelatives(x, shapes=True, type='mesh')]

    target_lis = []
    for source in source_lis:
        target = source.replace(f'{fileName}:','')
        target_lis.append(target)
        
        cmds.select(source, target, replace=1)
        try:
            cmds.transferAttributes(uvs=2)
            print(f'{source} UV is updated')
        except Exception as e:
            cmds.warning(f"Skipped {source} because {e}")
            
        # print(f'{source} UV is updated')
    cmds.delete(target_lis, ch=1)
    
def updateUVFromSelection(prefix = 'DannyUV__2_'):
    sl_lis = cmds.ls(sl=1)
    
    for sl in sl_lis:
        source = f'{prefix}:{sl}'
        
        cmds.select(source, sl, replace=1)
        try:
            cmds.transferAttributes(uvs=2)
            print(f'{sl} UV is updated')
        except Exception as e:
            cmds.warning(f"Skipped {sl} because {e}")
            
    
updateUVFromSelection()