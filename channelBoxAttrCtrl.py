# import maya.cmds as cmds

# # create a job that deletes things when they are seleted
# jobNum = cmds.scriptJob( ct= ["SomethingSelected","cmds.delete()"], protected=True)

# # Now display the job
# jobs = cmds.scriptJob( listJobs=True )

# # Now kill it (need to use -force flag since it's protected)
# cmds.scriptJob( kill=jobNum, force=True)

# # create a sphere, but print a warning the next time it
# # is raised over 10 units high
# def warn():
#     height = cmds.getAttr( 'mySphere.ty' )
#     if height > 10.0:
#         print 'Sphere is too high!'
# cmds.sphere( n='mySphere' )

# cmds.scriptJob( runOnce=True, attributeChange=['mySphere.ty', warn] )

# # create a job to detect a new attribute named "tag"
# #
# def detectNewTagAttr():
#     print "New tag attribute was added"

# cmds.scriptJob( runOnce=True, attributeAdded=['mySphere.tag',detectNewTagAttr] )
# cmds.addAttr( 'mySphere', ln='tag', sn='tg', dt='string')

# # list all the existing conditions and print them
# # nicely
# conds2 = cmds.scriptJob( listConditions=True )
# for cond in sorted(conds2):
#     print cond

  

def update_attr_visibility(ctrlName):
    if(ctrlName+".Method"==1):
        cmds.setAttr(ctrlName+'.Local',channelBox=True)
        cmds.setAttr(ctrlName+'.Hip',channelBox=True)
        cmds.setAttr(ctrlName+'.Cog',channelBox=True)
        
        cmds.setAttr(ctrlName+'.Space',keyable=False)
        cmds.setAttr(ctrlName+'.Space',channelBox=False)

    else:
        cmds.setAttr(ctrlName+'.Local',keyable=False)
        cmds.setAttr(ctrlName+'.Hip',keyable=False)
        cmds.setAttr(ctrlName+'.Cog',keyable=False)
        cmds.setAttr(ctrlName+'.Local',channelBox=False)
        cmds.setAttr(ctrlName+'.Hip',channelBox=False)
        cmds.setAttr(ctrlName+'.Cog',channelBox=False)
        cmds.setAttr(ctrlName+'.Space',channelBox=True)
    
  
cmds.scriptJob(attributeChange = ['r_leg_ik_ctrl.Method', update_attr_visibility('r_leg_ik_ctrl')])