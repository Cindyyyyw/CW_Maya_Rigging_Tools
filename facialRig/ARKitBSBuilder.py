import maya.cmds as cmds
import json 
import math


path = '/Volumes/CINDY/Rigging/CW_Maya_Rigging_Tools/facialRig/ARFaceAnchor.json'

class BSBuilder:
    def __init__(self, face_geo):
        self.face_geo = face_geo
        self.blendShape_names=[]
        self.blendShape_grp=[]
        self.transform_step = 200
        self.generate_side = True
        self.default_side = 'Left'
        self.loadFaceAnchor()
        
    def loadFaceAnchor(self):
        self.blendShape_names = []
        with open(path, 'r') as f:
            self.blendShapeData = json.load(f)
            for group, name_array in blendShapeData['ARFaceAnchor'].items():
                self.blendShape_names.extend(name_array)
                self.blendShape_grp.append(name_array)

        
    def generateBSMesh(self):
        for i in range(len(self.blendShape_grp)):
            for j in range(len(self.blendShape_grp[i])):
                new_blendshapeName = self.blendShape_grp[i][j]
                if self.generate_side:
                    print(new_blendshapeName[-5:])
                    if new_blendshapeName[-5:] == '_DIR_':
                        new_blendshape_geo_left = cmds.duplicate(self.face_geo, n=new_blendshapeName[:-5]+"Left")
                        cmds.xform(new_blendshape_geo_left, translation = (self.transform_step*(j%3)+i*5*self.transform_step, self.transform_step*(math.floor(j/3)),0))
                        new_blendshape_geo_right = cmds.duplicate(self.face_geo, n=new_blendshapeName[:-5]+"Right")
                        cmds.xform(new_blendshape_geo_right, translation = (self.transform_step*(j%3)+i*5*self.transform_step, self.transform_step*(math.floor(j/3)),-self.transform_step*3))
                        continue
                new_blendshape_geo = cmds.duplicate(self.face_geo, n=new_blendshapeName)
                cmds.xform(new_blendshape_geo, translation = (self.transform_step*(j%3)+i*5*self.transform_step, self.transform_step*(math.floor(j/3)),0))

a = BSBuilder('head')
# a.generateBSMesh()
