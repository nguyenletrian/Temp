import os
import maya.cmds as cmds
import pymel.core as pm
from functools import partial
from datetime import datetime
import maya.api.OpenMaya as om

import NLTA_General,NLTA_UI
for module in [NLTA_General,NLTA_UI]:
    try:
        importlib.reload(module)
    except:
        from importlib import reload
        reload(module)

ITEMS = {
    "items":{},
    "order":[]
}

def DefaultSetting(path,*arr):
    moduleName = os.path.basename(__file__).replace(".py","")
    ext = "json"
    name = "Create IK"
    return({
        "ext":ext,
        "path":path+moduleName+"."+ext,
        "moduleName":moduleName,
        "order":0,
        "title":name,
        "name":name,
        "id":datetime.now().strftime("%Y%m%d%H%M%S")
    })


def Load(data,listUI,*arr):
    newestData = NLTA_General.JsonGetByID({
        "path":data["sceneDataPath"]+"/ScenePatternData.json",
        "id":data["id"]
    })
    path = newestData["path"]
    if ".json" in path:
        children = cmds.layout(listUI,q=True, ca=True) or []
        for child in children:
            if cmds.control(child, exists=True):
                cmds.deleteUI(child)        
        itemDatas = NLTA_General.readJsonFile(path)
        if itemDatas:
            for i in range(len(itemDatas)):
                Add(listUI,itemDatas[i])

def Form(data,*arr):
    def Save(data, *arr):
        itemData = NLTA_General.JsonGetByID({
            "path":data["sceneDataPath"]+"/ScenePatternData.json",
            "id":data["id"]
        })          
        returnData = NLTA_UI.GetData(ITEMS['items'])
        NLTA_General.writeJsonFile(itemData["path"],returnData)

    mainForm = NLTA_General.LoadModule("Scene_Form")
    dataBack = mainForm.Create(data)
    buttonUI = dataBack["buttonUI"]
    listUI = dataBack["listUI"]

    cmds.rowColumnLayout(numberOfColumns=3,parent=buttonUI)
    cmds.button(label="Add",width=130,c=partial(Add,listUI,{}))
    cmds.button(label="Save", width=130,c=partial(Save,data))
    cmds.button(label="Run",width=130, c=partial(Run,data))
    cmds.setParent("..")
    Load(data,listUI)

def CreateCircleCtrl(name, radius=2):
    ctrl = cmds.circle(n=name,nr=(1,0,0),r=radius,ch=False)[0]
    for axis in [(0,1,0),(0,0,1)]:
        temp = cmds.circle(nr=axis,r=radius,ch=False)[0]
        shapes = cmds.listRelatives(temp, s=True, f=True)
        for shape in shapes:
            cmds.parent(shape, ctrl, r=True, s=True)
        cmds.delete(temp)
    return ctrl

def CreateCubeCtrl(name, size=2):
    s = size * 0.5
    points = [
        (-s,-s,-s),( s,-s,-s),( s, s,-s),(-s, s,-s),(-s,-s,-s),
        (-s,-s, s),( s,-s, s),( s, s, s),(-s, s, s),(-s,-s, s),
        ( s,-s, s),( s,-s,-s),
        ( s, s,-s),( s, s, s),
        (-s, s, s),(-s, s,-s)
    ]
    return cmds.curve(d=1,p=points,n=name)

def DuplicateChain(joints, suffix):
    root = cmds.duplicate(joints[0],rr=True,rc=True)[0]
    newJoints = [root]
    children = cmds.listRelatives(root,ad=True,type="joint",f=False) or []
    newJoints.extend(reversed(children))
    result = []
    for joint in newJoints:
        result.append(cmds.rename(joint,joint+"_"+suffix))
    return result


def Run(data, *arr):
    newestData = NLTA_General.JsonGetByID({
        "path": data["sceneDataPath"] + "/ScenePatternData.json",
        "id": data["id"]
    })
    datas = NLTA_General.readJsonFile(newestData["path"])
    if not datas:
        return
    for data in datas:
        parent = data["parent"]
        objects = [x for x in data["objects"].splitlines() if x.strip()]

        if len(objects) != 3:
            cmds.warning("This tool currently requires exactly 3 objects.")
            continue

        
        

        ### CREATE JOINTS ###
        
        # Find pos
        pts = []
        for obj in objects:
            p = cmds.xform(obj, q=True, ws=True, t=True)
            pts.append(om.MVector(p))
        A, B, C = pts

        # Get Normal plane
        normal = ((B - A) ^ (C - B))
        if normal.length() < 0.0001:
            cmds.warning("Objects are collinear.")
            continue
        normal.normalize()

        # Create Joint
        joints = []
        connectGrps = []
        for obj, pos in zip(objects, pts):
            jnt = cmds.createNode("joint",n=obj + "_ConnectJoint")
            cmds.xform(jnt,ws=True,t=(pos.x, pos.y, pos.z))
            joints.append(jnt)
            connectGrp = NLTA_General.GroupMatchObject(obj,obj+"_ConnectGroup")
            connectGrps.append(connectGrp)
            

        # Match to plane
        forwards = [(B - A).normal(),(C - B).normal(),(C - B).normal()]
        for jnt, pos, x in zip(joints, pts, forwards):
            z = (x ^ normal).normal()
            y = (z ^ x).normal()
            matrix = [
                x.x, x.y, x.z, 0,
                y.x, y.y, y.z, 0,
                z.x, z.y, z.z, 0,
                pos.x,pos.y,pos.z,1
            ]
            cmds.xform(jnt,ws=True,matrix=matrix)

        # Parent joint
        cmds.parent(joints[2], joints[1])
        cmds.parent(joints[1], joints[0])
        if cmds.objExists(parent):
            cmds.parent(joints[0], parent)
        cmds.makeIdentity(joints[0],apply=True,rotate=True)

        # Parent ConnectGrp to joint:
        for stt in range(len(connectGrps)):
            cmds.parent(connectGrps[stt],joints[stt])


        ### CREATE POLE VECTOR ###

        poleVectorName = objects[1]+"_PoleVector"
        # Find postion
        mid = (A + C) * 0.5
        polePos = B + (B - mid)

        # Create Pole Vector
        poleCtrl = cmds.circle(n=poleVectorName,nr=(1, 0, 0),r=2.0,ch=False)[0] #Shape 1
        shape2 = cmds.circle(nr=(0, 1, 0),r=2.0,ch=False)[0] #Shape 2
        shape3 = cmds.circle(nr=(0, 0, 1),r=2.0,ch=False)[0]
        for s in cmds.listRelatives(shape2, s=True, f=True):
            cmds.parent(s, poleCtrl, r=True, s=True)
        for s in cmds.listRelatives(shape3, s=True, f=True):
            cmds.parent(s, poleCtrl, r=True, s=True)
        cmds.delete(shape2, shape3)

        # Create Offset
        poleOffset = NLTA_General.CreateOffsetGroup(poleCtrl,poleCtrl+"_GrpOffset")

        # Match to pole Vector position
        cmds.xform(poleOffset,ws=True,t=(polePos.x, polePos.y, polePos.z))


        ### CREATE IK
        IKName = objects[2]+"_IK"
        IKCtrl = CreateCubeCtrl(IKName,size=4)
        matrix = cmds.xform(joints[-1],q=True,ws=True, matrix=True)
        cmds.xform(IKCtrl,ws=True,matrix=matrix)


        ### CREATE FKS
        FKCtrls = []
        FKOffsets = []
        for joint in joints:
            FKName = joint+"_FKCtrl"
            FKOffset = joint+"_FKOffset"
            FKCtrl = CreateCircleCtrl(FKName,radius=2)
            NLTA_General.CreateOffsetGroup(FKCtrl,FKOffset)
            matrix = cmds.xform(joint,q=True,ws=True,matrix=True)
            cmds.xform(FKOffset,ws=True,matrix=matrix)
            FKCtrls.append(FKName)
            FKOffsets.append(FKOffset)


        """



        #####

        ikJoints = DuplicateChain(joints,"_IK")
        fkJoints = DuplicateChain(joints,"_FK")

        ikHandle, effector = cmds.ikHandle(
            sj=ikJoints[0],
            ee=ikJoints[-1],
            sol="ikRPsolver",
            n=ikJoints[0].replace("_Jnt", "_IKHandle")
        )
        cmds.parent(
            ikHandle,
            endCtrl
        )
        cmds.poleVectorConstraint(
            poleCtrl,
            ikHandle
        )

        ##FK constraint
        cmds.parentConstraint(
            ctrl,
            joint,
            mo=False
        )

        for i in range(1, len(ctrlOffsets)):
            cmds.parent(
                ctrlOffsets[i],
                ctrlCtrls[i - 1]
            )
        """

def Add(listUI,data,*arr):
    global ITEMS
    def Delete(ui,*arr):
        global ITEMS
        cmds.deleteUI(ui)
        del ITEMS['items'][ui]
        ITEMS['order'].remove(ui)

    def PickChild(ui,*arr):
        NLTA_UI.PickObject(ui)
        offsetGroup = cmds.textField(itemData["Child"],query=True,text=True)+"_Offset"
        cmds.textField(itemData["OffsetName"],edit=True,text=offsetGroup)

    itemData = {}   
    itemUI = cmds.rowColumnLayout(numberOfColumns=1,parent=listUI,backgroundColor=(0.15, 0.15, 0.15))

    cmds.rowColumnLayout(numberOfColumns=1)

    cmds.rowColumnLayout( numberOfColumns=3,columnWidth=[(1,80),(2,265),(3,32)]) #--
 
    cmds.textField(text='Parent',editable=False)
    itemData['parent'] = cmds.textField(text=data.get('parent', ""))
    cmds.button(label="->",w=30,c=partial(NLTA_UI.PickObject,itemData['parent']))

    cmds.textField(text='Objects',editable=False)
    itemData['objects'] = cmds.scrollField(text=data.get('objects', ""),height=70)
    cmds.button(label="->",w=30,c=partial(NLTA_UI.PickObject,itemData['objects']))

    cmds.setParent("..") #--
    cmds.button(label="X",w=35,backgroundColor=(.5,.2,.2),c=partial(Delete,itemUI))
    cmds.separator(height=10, style='none')

    cmds.setParent("..")    
    cmds.setParent("..")

    ITEMS['items'][itemUI] = itemData
    ITEMS['order'].append(itemUI)










