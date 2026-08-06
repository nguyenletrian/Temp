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
    name = "Spline Rig"
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
    # Duplicate cả chain
    root = cmds.duplicate(
        joints[0],
        rr=True,
        rc=True
    )[0]

    # Lấy toàn bộ joint theo hierarchy
    newJoints = [root]
    children = cmds.listRelatives(
        root,
        ad=True,
        type="joint",
        f=False
    ) or []

    # listRelatives(ad=True) trả ngược thứ tự
    newJoints.extend(reversed(children))

    # Rename
    result = []

    for joint in newJoints:
        result.append(
            cmds.rename(joint,joint+"_"+suffix)
        )

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
        # ----------------------------------------------------
        # Positions
        # ----------------------------------------------------
        pts = []
        for obj in objects:
            p = cmds.xform(obj, q=True, ws=True, t=True)
            pts.append(om.MVector(p))
        A, B, C = pts

        # ----------------------------------------------------
        # Plane normal
        # ----------------------------------------------------
        normal = ((B - A) ^ (C - B))
        if normal.length() < 0.0001:
            cmds.warning("Objects are collinear.")
            continue
        normal.normalize()

        # ----------------------------------------------------
        # Create joints
        # ----------------------------------------------------
        joints = []
        for obj, pos in zip(objects, pts):
            jnt = cmds.createNode("joint",n=obj + "_Jnt")
            cmds.xform(jnt,ws=True,t=(pos.x, pos.y, pos.z))
            joints.append(jnt)

        # ----------------------------------------------------
        # Build matrices
        # ----------------------------------------------------
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
        # ----------------------------------------------------
        # Parent chain
        # ----------------------------------------------------
        cmds.parent(joints[2], joints[1])
        cmds.parent(joints[1], joints[0])
        if cmds.objExists(parent):
            cmds.parent(joints[0], parent)
        cmds.makeIdentity(joints[0],apply=True,rotate=True)

        # ----------------------------------------------------
        # Pole Vector Position
        # ----------------------------------------------------

        mid = (A + C) * 0.5

        # Đối xứng midpoint qua B
        polePos = B + (B - mid)

        # ----------------------------------------------------
        # Create Pole Vector Control
        # ----------------------------------------------------

        poleCtrl = cmds.circle(
            n="PoleVector_Ctrl",
            nr=(1, 0, 0),
            r=2.0,
            ch=False
        )[0]

        # Thêm 2 vòng để nhìn giống sphere
        shape2 = cmds.circle(
            nr=(0, 1, 0),
            r=2.0,
            ch=False
        )[0]

        shape3 = cmds.circle(
            nr=(0, 0, 1),
            r=2.0,
            ch=False
        )[0]

        # Parent shape vào poleCtrl
        for s in cmds.listRelatives(shape2, s=True, f=True):
            cmds.parent(s, poleCtrl, r=True, s=True)

        for s in cmds.listRelatives(shape3, s=True, f=True):
            cmds.parent(s, poleCtrl, r=True, s=True)

        cmds.delete(shape2, shape3)

        # Move tới vị trí pole vector
        cmds.xform(
            poleCtrl,
            ws=True,
            t=(polePos.x, polePos.y, polePos.z)
        )


        fkCtrls = []
        fkOffsets = []
        for joint in joints:
            cltrName = ""
            ctrlOffset = ""
            ctrl = CreateCircleCtrl(
                joint.replace("_Jnt","_Ctrl"),
                radius=2
            )

            matrix = cmds.xform(
                joint,
                q=True,
                ws=True,
                matrix=True
            )

            cmds.xform(
                ctrl,
                ws=True,
                matrix=matrix
            )
            fkCtrls.append(ctrl)

        endCtrl = CreateCubeCtrl(
            joints[-1].replace("_Jnt","End_Ctrl"),
            size=4
        )

        matrix = cmds.xform(
            joints[-1],
            q=True,
            ws=True,
            matrix=True
        )

        cmds.xform(
            endCtrl,
            ws=True,
            matrix=matrix
        )

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










