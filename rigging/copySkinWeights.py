import maya.cmds as cmds

geo_grp = "body_geo_grp"

all_geo_lis = cmds.listRelatives(geo_grp, ad=1, type="mesh")
all_geo =[]

for geo in all_geo_lis:

    if "ShapeDeformed" not in geo:
        all_geo.append(geo)

new_geo = []

for i in range(len(all_geo)):
    new_geo.append(all_geo[i].encode("utf-8"))
    new_geo[i] = new_geo[i].replace("Shape", "_newer")
    
print(all_geo)
print(new_geo)
# print(new_geo)
for i in range(len(new_geo)):
    print("trying: "+new_geo[i])
    geo_jnt = "root_jnt"
    try:
        sourceSkin = cmds.listConnections(all_geo[i]+"Deformed", s=1,d=0, type="skinCluster")[0]
        print("sourceSkin = "+ sourceSkin)
    except:
        print("sourceSkin list connection failed:" + all_geo[i])
        continue
    # cmds.select(new_geo[i])
    # cmds.select(geo_jnt, add=1)
    # print(new_geo[i])
    cmds.select(cl=1)
    print("binding:"+new_geo[i])
    cmds.skinCluster(new_geo[i], geo_jnt )
    # try:
    destinationSkin = cmds.listConnections(new_geo[i]+"ShapeDeformed", s=1,d=0, type="skinCluster")[0]
    print("destinationSkin = "+ destinationSkin)

    # except:
    #     print("destination list connection failed:" + new_geo[i])
    #     continue
    print("copying:"+new_geo[i])
    cmds.copySkinWeights(ss = sourceSkin, ds = destinationSkin, ia="oneToOne")
print("done")

