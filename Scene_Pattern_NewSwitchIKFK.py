import os
import sys
import json
import copy
import maya.cmds as cmds
import pymel.core as pm
import maya.api.OpenMaya as om
from functools import partial
from datetime import datetime


import NLTA_General,NLTA_UI,NLTA_ScriptJob
for module in [NLTA_General,NLTA_UI,NLTA_ScriptJob]:
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
    name = "New Switch IK FK"
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

def Form(data,*args):
    def Save(data,*args):
        itemData = NLTA_General.JsonGetByID({
            "path": data["sceneDataPath"]+"/ScenePatternData.json",
            "id": data["id"]
        })
        saveData = NLTA_UI.GetData(ITEMS["items"])
        NLTA_General.writeJsonFile(itemData["path"],saveData)

    def AddAS(listUI,*arr):
        ASDatas = [
            {
                "controlParent": "MainExtra1",
                "switchControl": "FKIKLeg_R",
                "switchAttr": "FKIKBlend",
                "valueActive": "0",
                "refObjects": "IKLeg_R\nPoleLeg_R",
                "sources": "FKHip_R\nFKKnee_R\nFKAnkle_R",
                "targets": "Hip_R\nKnee_R\nAnkle_R",
                "mirror": True
            },
            {
                "controlParent":"MainExtra1",
                "switchControl":"FKIKLeg_R",
                "switchAttr":"FKIKBlend",
                "valueActive":"10",
                "refObjects":"FKHip_R\nFKKnee_R\nFKAnkle_R",
                "sources":"PoleLeg_R\nIKLeg_R",
                "targets":"Knee_R\nAnkle_R",
                "mirror": True
            },
            {
                "controlParent":"MainExtra1",
                "switchControl":"FKIKArm_R",
                "switchAttr":"FKIKBlend",
                "valueActive":"0",
                "refObjects":"IKArm_R\nPoleArm_R",
                "sources":"FKShoulder_R\nFKElbow_R\nFKWrist_R",
                "targets":"Shoulder_R\nElbow_R\nWrist_R",
                "mirror": True
            },
            {
                "controlParent": "MainExtra1",
                "switchControl": "FKIKArm_R",
                "switchAttr": "FKIKBlend",
                "valueActive": "10",
                "refObjects": "FKShoulder_R\nFKElbow_R\nFKWrist_R",
                "sources": "PoleArm_R\nIKArm_R",
                "targets": "Elbow_R\nWrist_R",
                "mirror": True
            }
        ]
        for ASData in ASDatas:
            Add(listUI,ASData)

    mainForm = NLTA_General.LoadModule("Scene_Form")
    dataBack = mainForm.Create(data)
    buttonUI = dataBack["buttonUI"]
    listUI = dataBack["listUI"]
    cmds.rowColumnLayout(numberOfColumns=3,parent=buttonUI)
    cmds.button(label="Add",width=130,c=partial(Add,listUI,{}))
    cmds.button(label="Save", width=130,c=partial(Save,data))
    cmds.button(label="Run",width=130, c=partial(Run,data))
    cmds.button(label="Add AS",width=100,c=partial(AddAS,listUI))
    cmds.setParent("..")
    Load(data,listUI)


def Run(data,*args):

    def CtrlUI(*arr):
        if cmds.objExists("Rig_UI"):
            return "Rig_UI"
        curve = cmds.curve(n='Rig_UI',d=1,
            p=[
                (-1,0,-1),(-1,0,-3),(1,0,-3),(1,0,-1),(3,0,-1),(3,0,1),
                (1,0,1),(1,0,3),(-1,0,3),(-1,0,1),(-3,0,1),(-3,0,-1),(-1,0,-1)
            ]
        )
        shape = cmds.listRelatives(curve, shapes=True)[0]
        cmds.setAttr(shape + ".isHistoricallyInteresting", 0)
        cmds.setAttr(shape + ".overrideEnabled", 1)
        cmds.setAttr(shape + ".overrideColor", 17)
        for attr in ["tx", "ty", "tz","rx", "ry", "rz","sx", "sy", "sz","v"]:
            cmds.setAttr(curve + "." + attr,lock=True,keyable=False,channelBox=False)
        # Add Snap IK/FK attribute
        if not cmds.attributeQuery("snapIKFK", node=curve, exists=True):
            cmds.addAttr(curve,ln="snapIKFK",at="bool",dv=0,keyable=True)
        return curve

    def CreateDataNode(nodeName):
        rigUI = "Rig_UI"
        if cmds.objExists(nodeName):
            cmds.delete(nodeName)
        node = cmds.createNode("network", n=nodeName)
        if not cmds.attributeQuery("rigUI", node=nodeName, exists=True):
            cmds.addAttr(nodeName, ln="rigUI", at="message")
        cmds.connectAttr(
            "{}.message".format(rigUI),
            "{}.rigUI".format(nodeName),
            force=True
        )
        
    def AddData(data):
        jsonString = json.dumps(data, indent=2)
        node = "NLTA_DataNode"
        attr = "IKFKData"
        if not cmds.attributeQuery(attr, node=node, exists=True):
            cmds.addAttr(node, ln=attr, dt="string")
        cmds.setAttr("{}.{}".format(node, attr),jsonString,type="string")

    def CreateScriptNode(nodeName,mainControl,windowString):        
        if not cmds.attributeQuery("IKFKSnapWindow", node=nodeName, exists=True):
            cmds.addAttr(nodeName, ln="IKFKSnapWindow", dt="string")
        cmds.setAttr("{}.IKFKSnapWindow".format(nodeName),windowString,type="string")   
        if cmds.objExists("NLTA_RebuildSnapJob"):
            cmds.delete("NLTA_RebuildSnapJob")
        cmds.scriptNode(n="NLTA_RebuildSnapJob",st=2,bs="""
string $all[] = `ls`;
string $node = "";

for ($n in $all)
{
    string $parts[];
    tokenize($n, ":", $parts);

    if ($parts[size($parts)-1] == "NLTA_DataNode")
    {
        $node = $n;
        break;
    }
}

if ($node != "")
{
    string $code = `getAttr ($node + ".IKFKSnapWindow")`;
    python($code);
}
        """)

        

    mainControl = 'Rig_UI'
    nodeName = "NLTA_DataNode"
    windowString = rf'''
import json
import maya.cmds as cmds
import maya.api.OpenMaya as om

mainControl = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == "{mainControl}"][0]
mainControlAttr = mainControl+".snapIKFK"
nodeName = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == "{nodeName}"][0]

def callback():
    mainControl = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == "{mainControl}"][0]
    mainControlAttr = mainControl+".snapIKFK"
    nodeName = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == "{nodeName}"][0]
    def CreateWindow(*arr):
        def Snap(snapData,*arr):
            node = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == "{nodeName}"][0]
            switchControlName = snapData["switchControl"]
            switchControl = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == switchControlName][0]
            switchAttr = switchControl+"."+snapData["switchAttr"]
            sourcesArray = snapData["sources"].split("\n")
            targetsArray = snapData["targets"].split("\n")
            dataMatch = {{}}
            for i in range(len(sourcesArray)):
                target = targetsArray[i]
                source = sourcesArray[i]
                sourceReal = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == source][0]
                targetReal = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == target][0]
                targetMaxtrix = om.MMatrix(cmds.getAttr(targetReal + ".worldMatrix[0]"))
                offset = om.MMatrix(cmds.getAttr(node + "."+source+"_Matrix"))
                sourceMtx = offset * targetMaxtrix
                dataMatch[sourceReal] = sourceMtx
            cmds.setAttr(switchAttr,int(snapData["valueActive"]))
            cmds.setKeyframe(switchAttr)

            for sourceReal in dataMatch:
                cmds.xform(
                    sourceReal,
                    ws=True,
                    matrix=list(dataMatch[sourceReal])
                )
                attrs = ["tx", "ty", "tz", "rx", "ry", "rz"]
                cmds.setKeyframe(sourceReal, attribute=attrs)
            if len(sourcesArray) == 2:
                cmds.select([n for n in cmds.ls() if n.rsplit(":", 1)[-1] == sourcesArray[1]][0])
            else:
                cmds.select([n for n in cmds.ls() if n.rsplit(":", 1)[-1] == sourcesArray[2]][0])

        def Run(*arr):
            objs = cmds.ls(selection=True)
            if objs:
                node = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == "{nodeName}"][0]
                jsonString = cmds.getAttr(node+".IKFKData")
                snapDatas = json.loads(jsonString)
                snapWorks = []              
                for snapData in snapDatas:
                    switchControlName = snapData["switchControl"]
                    switchControl = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == switchControlName][0]
                    switchAttr = switchControl+"."+snapData["switchAttr"]
                    valueActive = int(snapData["valueActive"])
                    currentValue = int(cmds.getAttr(switchAttr))
                    for obj in objs:
                        obj = obj.split(":")[-1]
                        if obj in (snapData["refObjects"].split("\n")+[snapData["switchControl"]]) and (valueActive != currentValue):
                            snapWorks.append(snapData)
                for snapWork in snapWorks:
                    Snap(snapWork)
        mainControl = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == "{mainControl}"][0]
        mainControlAttr = mainControl+".snapIKFK"
        nodeName = [n for n in cmds.ls() if n.rsplit(":", 1)[-1] == "{nodeName}"][0]

        if cmds.window("SnapIKFK", exists=True):
            cmds.deleteUI("SnapIKFK")
        win = cmds.window("SnapIKFK", title="Snap IK/FK", widthHeight=(130,40),mxb=False,mnb=False,sizeable=False)
        cmds.columnLayout(adjustableColumn=True)
        cmds.button(label="Snap", command=Run,height=40)
        cmds.showWindow(win)

    if cmds.getAttr(mainControlAttr)==1:
        CreateWindow()
        cmds.setAttr(mainControlAttr, 0)

cmds.scriptJob(
    attributeChange=[
        mainControlAttr,
        callback
    ],
    protected=True
)

''' 
    # GET DATA
    newestData = NLTA_General.JsonGetByID({"path": data["sceneDataPath"]+"/ScenePatternData.json","id": data["id"]})
    datas = NLTA_General.readJsonFile(newestData["path"])

    expandedDatas = []
    for itemData in datas:
        sourcesArray = itemData["sources"].split("\n")
        targetsArray = itemData["targets"].split("\n")
        valid = True
        for source, target in zip(sourcesArray, targetsArray):
            if not cmds.objExists(source):
                cmds.warning("Source does not exist: {}".format(source))
                valid = False
                break
            if not cmds.objExists(target):
                cmds.warning("Target does not exist: {}".format(target))
                valid = False
                break
        if not valid:
            continue

        expandedDatas.append(itemData)
        if not itemData.get("mirror"):
            continue
        mirrorData = copy.deepcopy(itemData)
        mirrorFields = [
            "switchControl",
            "sources",
            "targets",
            "refObjects",
        ]
        for field in mirrorFields:
            if field not in mirrorData:
                continue
            value = mirrorData[field]
            if not value:
                continue
            if "\n" in str(value):
                mirrorData[field] = "\n".join(
                    NLTA_General.GetMirrorName(x)
                    for x in value.split("\n")
                    if x.strip()
                )
            else:
                mirrorData[field] = NLTA_General.GetMirrorName(value)
        expandedDatas.append(mirrorData)

    if expandedDatas:
        CtrlUI()
        CreateDataNode(nodeName)
        CreateScriptNode(nodeName,mainControl,windowString)    
        AddData(expandedDatas)
        for itemData in expandedDatas:
            if "controlParent" in itemData:
                try:
                    cmds.parent(mainControl,itemData["controlParent"])
                except:pass
            sourcesArray = itemData["sources"].split("\n")
            targetsArray = itemData["targets"].split("\n")
            for i in range(len(sourcesArray)):
                source = sourcesArray[i]
                target = targetsArray[i]
                if not cmds.attributeQuery(source+"_Matrix", node=nodeName, exists=True):
                    cmds.addAttr(nodeName, ln=source+"_Matrix", at="matrix")
                targetMtx = om.MMatrix(cmds.getAttr(target + ".worldMatrix[0]"))
                sourceMtx = om.MMatrix(cmds.getAttr(source + ".worldMatrix[0]"))
                offset = sourceMtx * targetMtx.inverse()
                cmds.setAttr(nodeName+"."+source+"_Matrix",list(offset),type="matrix")
        exec(windowString)



def Add(listUI,data,*args):
    global ITEMS
    def Delete(ui,*args):
        global ITEMS
        cmds.deleteUI(ui)
        del ITEMS["items"][ui]
        ITEMS["order"].remove(ui)

    itemData = {}
    itemUI = cmds.rowColumnLayout(numberOfColumns=1,parent=listUI,backgroundColor=(0.15,0.15,0.15))
    cmds.rowColumnLayout(numberOfColumns=1)

    cmds.rowColumnLayout(numberOfColumns=3,columnWidth=[(1,100),(2,235),(3,32)])
    cmds.textField(text="Control Parent",editable=False)
    itemData["controlParent"] = cmds.textField(text=data.get("controlParent",""))
    cmds.button(label="+",w=30,c=partial(NLTA_UI.PickObject,itemData["controlParent"]))
    cmds.setParent("..")

    cmds.rowColumnLayout(numberOfColumns=3,columnWidth=[(1,100),(2,235),(3,32)])
    cmds.textField(text="Switch Control",editable=False)
    itemData["switchControl"] = cmds.textField(text=data.get("switchControl",""))
    cmds.button(label="+",w=30,c=partial(NLTA_UI.PickObject,itemData["switchControl"]))
    cmds.setParent("..")
    
    cmds.rowColumnLayout(numberOfColumns=3,columnWidth=[(1,100),(2,235),(3,32)])
    cmds.textField(text="Switch Attribute",editable=False)
    itemData["switchAttr"] = cmds.textField(text=data.get("switchAttr",""))
    cmds.button(label="+",w=30,c=partial(NLTA_UI.PickAttrOnly,itemData["switchAttr"]))
    cmds.setParent("..")

    cmds.rowColumnLayout(numberOfColumns=3,columnWidth=[(1,100),(2,235),(3,32)])
    cmds.textField(text="Value Active",editable=False)
    itemData["valueActive"] = cmds.textField(text=data.get("valueActive",""))
    cmds.button(label="+",w=30,c=partial(NLTA_UI.PickObject,itemData["valueActive"]))
    cmds.setParent("..")

    cmds.rowColumnLayout(numberOfColumns=3,columnWidth=[(1,100),(2,235),(3,32)])
    cmds.textField(text="Ref Objects",editable=False)
    itemData["refObjects"] = cmds.scrollField(text=data.get("refObjects",""),height=65)
    cmds.button(label="+",w=30,c=partial(NLTA_UI.PickObject,itemData["refObjects"]))
    cmds.setParent("..")

    cmds.rowColumnLayout(numberOfColumns=3,columnWidth=[(1,100),(2,235),(3,32)])
    cmds.textField(text="Sources",editable=False)
    itemData["sources"] = cmds.scrollField(text=data.get("sources","Controls..."),height=65)
    cmds.button(label="+",w=30,c=partial(NLTA_UI.PickObject,itemData["sources"]))
    cmds.setParent("..")



    cmds.rowColumnLayout(numberOfColumns=3,columnWidth=[(1,100),(2,235),(3,32)])
    cmds.textField(text="Targets",editable=False)
    itemData["targets"] = cmds.scrollField(text=data.get("targets","Joints..."),height=65)
    cmds.button(label="+",w=30,c=partial(NLTA_UI.PickObject,itemData["targets"]))
    cmds.setParent("..")

    cmds.rowColumnLayout(numberOfColumns=3,columnWidth=[(1,100),(2,245),(3,32)])
    cmds.textField(text="Mirror",editable=False)
    itemData["mirror"] = cmds.checkBox(value=data.get("mirror", True),label="")
    cmds.setParent("..")

    cmds.button(label="X",w=380,bgc=(0.5,0.2,0.2),c=partial(Delete,itemUI))
    cmds.setParent("..")
    cmds.setParent("..")

    ITEMS["items"][itemUI] = itemData
    ITEMS["order"].append(itemUI)










