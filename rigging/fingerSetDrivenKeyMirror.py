import maya.cmds as cmds

sl = cmds.ls(sl=1)

for x in sl:
    l_v = x.replace("r_finger", "l_finger")
    print("%s's rz: %s"%(l_v, cmds.getAttr("%s.rz" %l_v)))
    cmds.setAttr("%s.rx" %x, cmds.getAttr("%s.rx" %l_v))
    cmds.setAttr("%s.ry" %x, cmds.getAttr("%s.ry" %l_v))
    cmds.setAttr("%s.rz" %x, cmds.getAttr("%s.rz" %l_v))
    print("setted %s"%x)
print("done")