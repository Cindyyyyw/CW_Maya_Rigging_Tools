import maya.cmds as cmds


class spineBuilder():
    def __init__(self, rootJnt = cmds.ls(sl=1)[0]):
        self.rootJnt = rootJnt
        childrenCount = len(cmds.listRelatives(rootJnt, ad=1, type="joint"))
        jntLis = [rootJnt]
        
        for i in range(childrenCount):
            children = cmds.listRelatives(jntLis[i], children=1, type='joint')
            if children == None:
                break
            elif len(children)>1:
                raise ValueError("The input root joint has branched children joints.")
            else:
                jntLis.append(children[0])
        self.jntLis = jntLis

        
    def create_ik_fk_joints(self):
        # creates and renames three duplicates of the spine joint with the same hierarchy
        # self.ikProxyJntLis
        # self.ikJntLis
        # self.fkJntLis
        pass
        
    def create_ik_spline_handle(self):
        # takes ikJntLis and selects the first and second last joint to create a spline ik
        # creates three joints that are skin binded to the curve
        # self.ikCtrlJntLis
        # self.ikSpineCurveCurr
        pass
        
    def create_ik_spine_ctrl(self):
        # creates and places the controls according to the positions of the joints
        # sorts them into hierarchy, and constrains them
        # includes root ctrl, hip ctrl, waist ctrl, and chest ctrl
        # self.ikCtrlLis
        pass
    
    def create_ik_stretch_sys(self):
        # bind all ikJntLis joints to ikProxyJntLis joints (parent constraint)

        # add two sttributes to root control: SquashFactor and SquashWeight

        # duplicates ikSpineCurveCurr as ikSpineCurveOrig
        
        # extract curve info by curveinfo node from both curve
        
        # calculate [lengthScale] by currLength / origLength using multiplyDivide node
        
        # plug lengthScale.output to .scaleX of all joints in ikProxyJntLis
        
        # calculate [invertLengthScale] by lengthScale * -1 using multiplyDivide node
        
        # calculate [invertLengthScale] by lengthScale * -1 using multiplyDivide node
        
        # remap squashFactor from input min -1 max 1 to output min 0.5 max 1.5

        # calculate [squashFactorMultiplier] by invertLengthScale * squashFactorRemap using multiplyDivide node

        # calculate [square] by squashFactorMultiplier * squashFactorMultiplier using multiplyDivide node
        # - output to X
        
        # calculate [cube] by square * squashFactorMultiplier using multiplyDivide node
        # - output to Y

        # calculate [quad] by cube * squashFactorMultiplier using multiplyDivide node
        # - output to Z
        
        # calculate [differenceWithOne] by [square, cube, quad] - [1,1,1] using PlusMinusAverage node
        
        # calculate [weightedDifference] by differenceWithOne * SquashWeight using multiplyDivide node
        
        # calculate [weightedScale] by weightedDifference + 1 using plusMinusAverage node

        # connect the output of weightedScale to ikJntLis joints's scaleY and scaleZ
        pass
        
        
        
        
test = spineBuilder()
print(test.jntLis)
