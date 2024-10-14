import maya.cmds as cmds

# this needs the joint to have a upper hierarchy
# that is producing all the motion that this joint need at the moment
# so the new control group can be parented to it and become the parent of
# the joint

jnt_lis = cmds.ls(sl=1)

for jnt in jnt_lis:
    ctrlGrp = cmds.group(em=1,w=1)
    cmds.matchTransform(ctrlGrp, jnt)
    