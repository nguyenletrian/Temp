import os
import maya.cmds as cmds
import pymel.core as pm
from functools import partial
from datetime import datetime

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
    name = "BS Sequel From Sculpt"
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



def Run(data, *arr):
    newestData = NLTA_General.JsonGetByID({
        "path": data["sceneDataPath"] + "/ScenePatternData.json",
        "id": data["id"]
    })
    datas = NLTA_General.readJsonFile(newestData["path"])
    if not datas:
        return
    for i in range(len(datas)):
        data = datas[i]
        mesh = data["mesh"]
        sculpt = data["sculpt"]
        attrHolders = [ holder for holder in data["attrHolder"].split("\n") if holder and cmds.objExists(holder)]
        mainAttrHolder = attrHolders[0]
        jointHolder = data["jointHolder"]
        attr = data["attr"]
        bsParent = data["bsParent"]

        transformAttrs = ["tx", "ty", "tz","rx", "ry", "rz","sx", "sy", "sz"]
        keyframes = set()
        for transformAttr in transformAttrs:
            plug = "{}.{}".format(sculpt,transformAttr)
            if not cmds.objExists(plug):
                continue
            frames = cmds.keyframe(plug,query=True,timeChange=True) or []
            keyframes.update(frames)
        keyframes = sorted(frame for frame in keyframes if frame != 0)
        meshShapes = cmds.listRelatives(mesh,shapes=True,noIntermediate=True) or []
        meshShape = meshShapes[0]
        connections = cmds.listConnections(meshShape + ".inMesh",source=True,destination=False,plugs=True) or []
        sculptOutput = connections[0]
        currentFrame = cmds.currentTime(query=True)
        generatedMeshes = []
        for frame in keyframes:
            cmds.currentTime(0,edit=True)
            duplicate = cmds.duplicate(mesh,rr=True,inputConnections=False,upstreamNodes=False)[0]
            duplicate = cmds.rename(duplicate,"{}_Shoot_{:g}".format(mesh,frame))
            cmds.delete(duplicate,constructionHistory=True)
            duplicateShapes = cmds.listRelatives(duplicate,shapes=True,noIntermediate=True) or []
            if not duplicateShapes:
                cmds.warning("Cannot find duplicate shape: {}".format(duplicate))
                cmds.delete(duplicate)
                continue
            duplicateShape = duplicateShapes[0]
            duplicateInput = duplicateShape + ".inMesh"
            cmds.connectAttr(sculptOutput,duplicateInput,force=True)
            cmds.currentTime(frame,edit=True)
            cmds.disconnectAttr(sculptOutput,duplicateInput)
            cmds.delete(duplicate,constructionHistory=True)
            generatedMeshes.append(duplicate)

        bsGroup = "{}_BSs".format(mesh)
        if cmds.objExists(bsGroup):
            cmds.delete(bsGroup)
        bsGroup = cmds.group(generatedMeshes,name=bsGroup)
        if bsParent and cmds.objExists(bsParent):
            cmds.parent(bsGroup,bsParent)


        cmds.currentTime(currentFrame,edit=True)
        blendShapeName = "{}_{}_BS".format(mesh,attr)

        blendShape = cmds.blendShape(generatedMeshes,mesh,name=blendShapeName)[0]

        #####
        mainAttr = "{}.{}".format(mainAttrHolder,attr)
        if not cmds.attributeQuery(attr,node=mainAttrHolder,exists=True):
            cmds.addAttr(mainAttrHolder,longName=attr,attributeType="double",minValue=0,maxValue=10,defaultValue=0)
        cmds.setAttr(mainAttr,edit=True,keyable=True)

        for holder in attrHolders[1:]:
            if not cmds.attributeQuery(attr,node=holder,exists=True):
                cmds.addAttr(holder,longName=attr,attributeType="double",proxy=mainAttr)
            cmds.setAttr("{}.{}".format(holder, attr),edit=True,keyable=True)

        if not cmds.attributeQuery(attr, node=jointHolder, exists=True):
            cmds.addAttr(jointHolder,longName=attr,attributeType="double",minValue=0,maxValue=10,defaultValue=0)
        cmds.setAttr("{}.{}".format(jointHolder, attr),edit=True,keyable=True)

        cmds.connectAttr("{}.{}".format(mainAttrHolder, attr),"{}.{}".format(jointHolder, attr),force=True)



        driver = mainAttr
        numShapes = len(generatedMeshes)
        segment = 10.0 / numShapes

        cmds.setAttr(driver, 0)
        for index in range(numShapes):
            blendAttr = "{}.w[{}]".format(blendShape,index)
            cmds.setAttr(blendAttr, 0)
            cmds.setDrivenKeyframe(blendAttr,currentDriver=driver)


        for step in range(numShapes):
            shootValue = segment * (step + 1)
            if step == numShapes - 1:
                shootValue -= segment * 0.5
            cmds.setAttr(driver,shootValue)
            for index in range(numShapes):
                blendAttr = "{}.w[{}]".format(blendShape,index)
                if index == step:
                    value = 1.0
                elif index == step - 1:
                    value = 0.5
                elif index == step + 1:
                    value = 0.5
                else:
                    value = 0.0
                cmds.setAttr(blendAttr,value)
                cmds.setDrivenKeyframe(blendAttr,currentDriver=driver)


        cmds.setAttr(driver,10)
        for index in range(numShapes):
            blendAttr = "{}.w[{}]".format(blendShape,index)
            cmds.setAttr(blendAttr,0)
            cmds.setDrivenKeyframe(blendAttr,currentDriver=driver)

        showAttr = "{}ShowBS".format(attr)
        mainShowAttr = "{}.{}".format(attrHolders[0],showAttr)
        if not cmds.attributeQuery(showAttr,node=attrHolders[0],exists=True):
            cmds.addAttr(attrHolders[0],longName=showAttr,attributeType="bool",defaultValue=False)
        cmds.setAttr(mainShowAttr,edit=True,keyable=True)
        for holder in attrHolders[1:]:
            proxyShowAttr = "{}.{}".format(holder,showAttr)
            if not cmds.attributeQuery(showAttr,node=holder,exists=True):
                cmds.addAttr(holder,longName=showAttr,attributeType="bool",proxy=mainShowAttr)
            cmds.setAttr(proxyShowAttr,edit=True,keyable=True)
        cmds.connectAttr(
            mainShowAttr,
            bsGroup + ".visibility",
            force=True
        )        

        cmds.setAttr(driver,0)
        cmds.currentTime(currentFrame,edit=True)



def Add(listUI,data,*arr):
    global ITEMS
    def Delete(ui,*arr):
        global ITEMS
        cmds.deleteUI(ui)
        del ITEMS['items'][ui]
        ITEMS['order'].remove(ui)

    itemData = {}   
    itemUI = cmds.rowColumnLayout(numberOfColumns=1,parent=listUI,backgroundColor=(0.15, 0.15, 0.15))

    cmds.rowColumnLayout(numberOfColumns=1)

    cmds.rowColumnLayout( numberOfColumns=3,columnWidth=[(1,80),(2,265),(3,32)]) #--


    cmds.textField(text='Mesh',editable=False)
    itemData['mesh'] = cmds.textField(text=data.get('mesh', ""))
    cmds.button(label="->",w=30,c=partial(NLTA_UI.PickObject,itemData['mesh']))

    cmds.textField(text='Sculpt',editable=False)
    itemData['sculpt'] = cmds.textField(text=data.get('sculpt', ""))
    cmds.button(label="->",w=30,c=partial(NLTA_UI.PickObject,itemData['sculpt']))

    cmds.textField(text='BS Parent',editable=False)
    itemData['bsParent'] = cmds.textField(text=data.get('bsParent', ""))
    cmds.button(label="->",w=30,c=partial(NLTA_UI.PickObject,itemData['bsParent']))


    cmds.textField(text='Attr Holder',editable=False)
    itemData['attrHolder'] = cmds.textField(text=data.get('attrHolder', ""))
    cmds.button(label="->",w=30,c=partial(NLTA_UI.PickObject,itemData['attrHolder']))

    cmds.textField(text='Joint Holder',editable=False)
    itemData['jointHolder'] = cmds.textField(text=data.get('jointHolder', ""))
    cmds.button(label="->",w=30,c=partial(NLTA_UI.PickObject,itemData['jointHolder']))

    cmds.textField(text='Attr',editable=False)
    itemData['attr'] = cmds.textField(text=data.get('attr', ""))
    cmds.text("..")

    cmds.setParent("..") #--

    cmds.button(label="X",w=35,backgroundColor=(.5,.2,.2),c=partial(Delete,itemUI))
    cmds.separator(height=10, style='none')

    cmds.setParent("..")    
    cmds.setParent("..")

    ITEMS['items'][itemUI] = itemData
    ITEMS['order'].append(itemUI)










