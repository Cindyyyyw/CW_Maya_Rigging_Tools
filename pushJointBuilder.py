import maya.cmds as cmds

def isPointedAt(child, axis=None):
    
    zeroChannel = 0
    translateValue = list(cmds.getAttr(f'{child}.translate')[0])
    print(translateValue)
    
    skip = ['x','y','z']
    skip_index = -1
    if axis in skip:
        skip_index = skip.index(axis)

    
    for i in range(3):
        if i == skip_index:
            continue
        if translateValue[i]<=0.10:
            zeroChannel +=1
    print(zeroChannel)
    if zeroChannel>=2:
        return True
    return False

'''
this function has two modes:
    1 is for creating under the parent of the target (sibling)
    2 is for creating under the target itself
'''

def createPartialJoint(target_jnt, support_jnt, mode=1):
    
    partialBM = cmds.createNode('blendMatrix', n = f'{partial_jnt}_BM')
    if mode==1:
        cmds.select(support_jnt, r=1)
        partial_jnt = cmds.joint(n=f'{target_jnt}_partial_{mode}')
        cmds.connectAttr(f'{target_jnt}.dagLocalMatrix',f'{partialBM}.target[0].targetMatrix')
        cmds.setAttr(f'{partialBM}.translateWeight', 0.75)
        if not isPointedAt(target, 'x'):
            temp_aim = cmds.aimConstraint(target_jnt, partial_jnt, mo=False, aim = [-1, 0,0], u= [0, 1, 0], wut='Vector', wu = [0,1,0] )
            cmds.delete(temp_aim)
            cmds.makeIdentity(partial_jnt, r=1, apply=1)
    elif mode==2:
        cmds.select(target_jnt, r=1)
        partial_jnt = cmds.joint(n=f'{target_jnt}_partial_{mode}')
        cmds.connectAttr(f'{support_jnt}.dagLocalMatrix',f'{partialBM}.target[0].targetMatrix')
        cmds.setAttr(f'{partialBM}.translateWeight', 0.25)
        
    cmds.setAttr(f'{partialBM}.rotateWeight', 0)

    
        
    
    
    
    

sel = cmds.ls(sl=1)
cmds.select(cl=1)
POSITIVE = 1
NEGATIVE = -1
ZERO = 0

main_axis = 'x'
input_jnt = 'l_knee_jnt'
x_direction = POSITIVE
up_direction = POSITIVE
x_dist = 3
yz_dist = 5


remap_max = x_direction*30
push_intensity = 5
skip = [0, 2, 3]

# create a partial joint based on joint selected,
# if up joint chain, find the parent and create the partial joint as the selected joint's sibling
# if down joint chain, make selected joint the parent
# the joint should be 25% or user defined away from selected joint
# if selected joint have more than two children, the user should be able to select the entire joint chain instead (in parent - target joint - child order)
if len(sel)==1:
    parent_jnt_lis = cmds.listRelatives(sel, p=1, type='joint')
    child_jnt_lis = cmds.listRelatives(sel, c=1, type='joint')
    # print(f'the parent of {sel} is {parent}, child of {sel} is {child}')
    if len(child_jnt_lis)!=1 or len(parent_jnt_lis)!=1:
        cmds.error('Cannot locate a chain from selected joint, please select in [parent - target - child] order instead')
    else:
        parent_jnt = parent_jnt_lis[0]
        target_jnt = sel[0]
        child_jnt = child_jnt_lis[0]
elif len(sel)==3:
    parent_jnt = sel[0]
    target_jnt = sel[1]
    child_jnt = sel[2]
else:
    cmds.error('Invalid input. Please either select one joint or select in [parent - target - child] order.')

cmds.select(parent_jnt, r=1)
partial_jnt_1 = cmds.joint(n=f'{target_jnt}_partial_1')
cmds.select(target_jnt, r=1)
partial_jnt_2 = cmds.joint(n=f'{target_jnt}_partial_1')


# for i in range(4):
#     if i in skip:
#         continue
#     y_value = ZERO
#     z_value = ZERO
#     if i>1:
#         y_value = ZERO
#         z_value = NEGATIVE
#         if i%2 == 0: z_value = POSITIVE
#     else:
#         z_value = ZERO
#         y_value = NEGATIVE
#         if i%2 == 0: y_value = POSITIVE
    
#     push_jnt = cmds.joint(n=f'{sel}_push_{i}_0')
#     cmds.parent(push_jnt, sel)
#     cmds.makeIdentity(push_jnt)
#     cmds.setAttr(f'{push_jnt}.translate', up_direction*x_dist , y_value*yz_dist, z_value*yz_dist)
#     aim_cons = cmds.aimConstraint(sel,push_jnt, mo=False, aim = [-1, 0,0], u= [0, 1, 0], wut='Vector', wu = [0,1,0] )
#     cmds.delete(aim_cons)
#     cmds.makeIdentity(push_jnt, apply=1, rotate=1)
#     cmds.select(push_jnt,r=1)
#     push_child = cmds.joint(n=f'{sel}_push_{i}_1')
    
#     remap_node = cmds.createNode('remapValue', n=f'{push_child}_remap')
#     # if x = positive
#     #  -y pushes out when rot z decreases
#     #   y pushes out when rot z increases
#     #   z pushes out when rot y decreases
#     #  -z pushes out when rot y increases
#     if y_value == ZERO:
#         cmds.connectAttr(f'{input_jnt}.rotateY', f'{remap_node}.inputValue')
#         orientY = cmds.getAttr(f'{input_jnt}.rotateY')
#         cmds.setAttr(f'{remap_node}.inputMin', orientY)
#         if z_value == POSITIVE:
#             cmds.setAttr(f'{remap_node}.inputMax', orientY - remap_max)
#         else:
#             cmds.setAttr(f'{remap_node}.inputMax', orientY + remap_max)
#     else:
#         cmds.connectAttr(f'{input_jnt}.rotateZ', f'{remap_node}.inputValue')
#         orientZ = cmds.getAttr(f'{input_jnt}.rotateZ')
#         cmds.setAttr(f'{remap_node}.inputMin', orientZ)
#         if y_value == POSITIVE:
#             cmds.setAttr(f'{remap_node}.inputMax', orientZ + remap_max)
#         else:
#             cmds.setAttr(f'{remap_node}.inputMax', orientZ - remap_max)
    
#     mult_node = cmds.createNode('floatMath', n=f'{push_child}_mult')
#     cmds.setAttr(f'{mult_node}.floatB', push_intensity)
#     cmds.setAttr(f'{mult_node}.operation', 2)

#     cmds.connectAttr(f'{remap_node}.outValue', f'{mult_node}.floatA')
#     cmds.connectAttr(f'{mult_node}.outFloat', f'{push_child}.translateX')
    
    
    
    
    
    
    
    