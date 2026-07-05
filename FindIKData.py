import maya.cmds as cmds

def GetIKsData(*arr):
    IKs = cmds.ls(type="ikHandle")
    returnData = []
    for IK in IKs:
        IKData = {}
        IKData["startJoint"] = cmds.ikHandle(IK, q=True, sj=True)
        IKData["endEffector"] = cmds.ikHandle(IK, q=True, ee=True)
        IKData["jointMiddle"] = cmds.listRelatives(IKData["endEffector"], parent=True, type="joint")[0]
        IKData["jointEnd"] = cmds.listConnections(IKData["endEffector"] + ".translateX",source=True,destination=False)[0]
        pv = cmds.listConnections(IK, type="poleVectorConstraint")
        if pv:
            IKData["poleVector"] = cmds.poleVectorConstraint(pv[0], q=True, tl=True)[0]
        else:
            IKData["poleVector"] = None
        returnData.append(IKData)        
    returnData.append(IKData)
    return(returnData)
    
def GetDrivenJoints(startJoint,type):
    constraintTypes = (
        "parentConstraint","pointConstraint","orientConstraint","scaleConstraint",
        "aimConstraint","poleVectorConstraint","geometryConstraint","normalConstraint","tangentConstraint")
    driven = set()
    constraints = []
    for constraintType in constraintTypes:
        constraints.extend(cmds.listConnections(startJoint,source=False,destination=True,type=constraintType) or [])
    constraints = list(set(constraints))
    for constraint in constraints:
        targets = cmds.listConnections(constraint,source=False,destination=True) or []
        for target in targets:
            if target != constraint and cmds.objectType(target)==type:
                driven.add(target)
    sorted(driven)
    return driven

def GetDriverObjects(obj, nodeType=None):
    constraintTypes = (
        "parentConstraint", "pointConstraint", "orientConstraint", "scaleConstraint",
        "aimConstraint", "poleVectorConstraint", "geometryConstraint","normalConstraint", "tangentConstraint")
    drivers = set()
    constraints = []
    for constraintType in constraintTypes:
        constraints.extend(cmds.listConnections(obj,source=True,destination=False,type=constraintType) or [])
    constraints = list(set(constraints))
    for constraint in constraints:
        sources = cmds.listConnections(constraint,source=True,destination=False) or []
        for source in sources:
            if source == constraint:
                continue
            if nodeType and cmds.objectType(source) != nodeType:
                continue
            drivers.add(source)
    return sorted(drivers)

