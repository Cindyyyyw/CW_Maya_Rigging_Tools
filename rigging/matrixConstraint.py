import maya.cmds as cmds
import maya.api.OpenMaya as om
'''
    This is a script to build custom constraint in maya by matrices.
    Currently features:
        - Single parent parent constraint
        - Multiple parent parent constraint
'''

'''
    The idea behind parent constraint is to:
        1. obtain the offset between the parent and the child
        2. calculate the offset parent matrix by parentWorldMatrix*offset
'''
def omMtxToLis(matrix):
    '''
        Returns the om Matrices in a list format
    '''
    converted_list = []
    for i in range(4):
        for j in range(4):
            converted_list.append(matrix.getElement(i, j))
    return converted_list

def parentConstraint(parent, child, selector=None, parentName=None, offset=True, offsetLoc=None):
    '''
        Takes minimum 1 parent, and exactly 1 child. 
        If offset == False, output offset parent matrix as equivlent to parent's world matrix
        Elif offset == True and offsetLoc == None, calculate the offset based on the current location of the child
        Elif offset == True and offsetLoc == a list containing locators of desired positions for each constraint space, calculate the offset based on the current location of the locator
    '''
    # parentConstraint_MM = cmds.createNode('multMatrix', n=f'{child}_parentConstraint_MM')
    # matrixInCount = 0
    parentLen = len(parent)
    # locLen = len(offsetLoc)
    
    if parentLen<1: return cmds.error('Please select at least one parent.')
    
    #   1. one parent
    if parentLen ==1:
        matrixInCount = 0
        parentConstraint_MM = cmds.createNode('multMatrix', n=f'{child}_parentConstraint_MM')
        if offset:
            childWorldMatrix = om.MMatrix(cmds.getAttr(f'{child}.worldMatrix[0]'))
            parentWorldInvMatrix = om.MMatrix(cmds.getAttr(f'{parent[0]}.worldMatrix[0]')).inverse() 
            offsetMatrix = omMtxToLis(childWorldMatrix * parentWorldInvMatrix)
            
            cmds.setAttr(f'{parentConstraint_MM}.matrixIn[{matrixInCount}]', offsetMatrix, type='matrix')
            matrixInCount += 1
        cmds.connectAttr(f'{parent[0]}.worldMatrix[0]', f'{parentConstraint_MM}.matrixIn[{matrixInCount}]')
    else:
        parentChoice = cmds.createNode('choice', n=f'{child}_parentConstraint_choice')
        choiceInputCount = 0
        if selector:
            if parentName:
                cmds.addAttr(selector, longName='parent', attributeType='enum', en= ':'.join(parentName))
            else:
                cmds.addAttr(selector, longName='parent', attributeType='enum', en= ':'.join(parent))
            cmds.setAttr(f'{selector}.parent',k=1, cb=1, l=0)
            cmds.connectAttr(f'{selector}.parent', f'{parentChoice}.selector' )
        for i in range(parentLen):
            matrixInCount = 0
            parentConstraint_MM = cmds.createNode('multMatrix', n=f'{parent[i]}_{child}_parentConstraint_MM')
            if offset:
                if offsetLoc:
                    childWorldMatrix = om.MMatrix(cmds.getAttr(f'{offsetLoc[i]}.worldMatrix[0]'))
                else:
                    childWorldMatrix = om.MMatrix(cmds.getAttr(f'{child}.worldMatrix[0]'))
                parentWorldInvMatrix = om.MMatrix(cmds.getAttr(f'{parent[i]}.worldMatrix[0]')).inverse() 
                offsetMatrix = omMtxToLis(childWorldMatrix * parentWorldInvMatrix)
                
                cmds.setAttr(f'{parentConstraint_MM}.matrixIn[{matrixInCount}]', offsetMatrix, type='matrix')
                matrixInCount += 1
            cmds.connectAttr(f'{parent[i]}.worldMatrix[0]', f'{parentConstraint_MM}.matrixIn[{matrixInCount}]')
            cmds.connectAttr(f'{parentConstraint_MM}.matrixSum', f'{parentChoice}.input[{i}]')
        cmds.connectAttr(f'{parentChoice}.output', f'{child}.offsetParentMatrix')
            
# parentConstraint(['spine_3_jnt', 'r_wrist_pos_jnt'], 'test', selector = 'test', parentName = ['waist', 'R_hand'], offset=True, offsetLoc = ['locator1', 'locator2'])
    
    
    