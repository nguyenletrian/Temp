import maya.cmds as cmds
import importlib
import math
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

import NLTA_General, NLTA_OpenMaya
for module in [NLTA_General, NLTA_OpenMaya]:
    try:
        importlib.reload(module)
    except:
        reload(module)

cmds.selectPref(trackSelectionOrder=True)


def ShowQuardraw(*arr):
    cmds.lockNode("initialShadingGroup", lock=False, lockUnpublished=False)

def GetVertexsSelected(*arr):
    sel = cmds.ls(sl=True)
    if not sel:
        return []
    verts = cmds.polyListComponentConversion(sel, toVertex=True)
    return cmds.ls(verts, fl=True)

def GetMesh(*arr):
    selection = cmds.ls(sl=True, fl=True)
    return list(dict.fromkeys(s.split(".")[0] for s in selection))


def JointPos(j):
    return om.MVector(cmds.xform(j, q=True, ws=True, t=True))

def GetID(component):
    if isinstance(component, (int, float)):
        return int(component)
    return int(component.rsplit("[", 1)[-1].split("]", 1)[0])


def GetMeshData(mesh):
    dag = NLTA_OpenMaya.GetDagPath(mesh)
    return {"dag": dag, "fn": om.MFnMesh(dag)}

def GetMeshFn(mesh):
    return GetMeshData(mesh)["fn"]


def GetVertexIterator(mesh):
    return om.MItMeshVertex(GetMeshData(mesh)["dag"])


def GetEdgeIterator(mesh):
    return om.MItMeshEdge(GetMeshData(mesh)["dag"])

def GetSkinData(mesh):
    dag = NLTA_OpenMaya.GetDagPath(mesh)
    history = om.MItDependencyGraph(
        dag.node(),
        om.MFn.kSkinClusterFilter,
        om.MItDependencyGraph.kUpstream,
        om.MItDependencyGraph.kDepthFirst,
        om.MItDependencyGraph.kPlugLevel
    )
    return dag, None if history.isDone() else oma.MFnSkinCluster(history.currentItem())


def CreateVertexComponent(vertexIds):
    component = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
    om.MFnSingleIndexedComponent(component).addElements(vertexIds)
    return component



def EdgeDirection(mesh, edgeIndex):
    edgeIt = GetEdgeIterator(mesh)
    edgeIt.setIndex(GetID(edgeIndex))
    p1 = edgeIt.point(0, om.MSpace.kWorld)
    p2 = edgeIt.point(1, om.MSpace.kWorld)
    return om.MVector(p2 - p1).normal()


def CheckEdgeBorder(mesh, edgeId):
    edgeIt = GetEdgeIterator(mesh)
    edgeIt.setIndex(GetID(edgeId))
    return edgeIt.onBoundary()


def VertexFromEdges(mesh, edges):
    dag = GetMeshData(mesh)["dag"]
    edge_it = om.MItMeshEdge(dag)
    vertex_ids = set()

    for edge in edges:
        edge_it.setIndex(GetID(edge))
        vertex_ids.add(edge_it.vertexId(0))
        vertex_ids.add(edge_it.vertexId(1))

    return ["{}.vtx[{}]".format(mesh, vertex_id) for vertex_id in vertex_ids]


def GetConnectedEdges(mesh, vertex_index):
    dag = GetMeshData(mesh)["dag"]
    vertex_it = om.MItMeshVertex(dag)
    vertex_it.setIndex(vertex_index)
    return vertex_it.getConnectedEdges()


def EdgeCenter(mesh, edgeId):
    edgeIt = GetEdgeIterator(mesh)
    edgeIt.setIndex(GetID(edgeId))
    p1 = om.MVector(edgeIt.point(0, om.MSpace.kWorld))
    p2 = om.MVector(edgeIt.point(1, om.MSpace.kWorld))
    return (p1 + p2) * 0.5


def GetEdgeRing(mesh, start_edge):
    edge_ids = cmds.polySelect(
        mesh,
        edgeRing=GetID(start_edge),
        noSelection=True
    )

    if not edge_ids:
        return []

    return ["{}.e[{}]".format(mesh, edge_id) for edge_id in edge_ids]



def GetFarthestEdge(mesh, baseEdge, edges):
    baseId = GetID(baseEdge)
    edgeIt = GetEdgeIterator(mesh)
    edgeIt.setIndex(baseId)
    p1 = om.MVector(edgeIt.point(0, om.MSpace.kWorld))
    p2 = om.MVector(edgeIt.point(1, om.MSpace.kWorld))
    baseCenter = (p1 + p2) * 0.5
    maxDistance = -1.0
    farEdge = None
    for edge in edges:
        edgeId = GetID(edge)
        edgeIt.setIndex(edgeId)
        p1 = om.MVector(edgeIt.point(0, om.MSpace.kWorld))
        p2 = om.MVector(edgeIt.point(1, om.MSpace.kWorld))
        center = (p1 + p2) * 0.5
        delta = center - baseCenter
        distance = delta * delta
        if distance > maxDistance:
            maxDistance = distance
            farEdge = edge
    return farEdge


def GetClosestEdge(mesh, edges, joint):
    jointPos = JointPos(joint)
    edgeIt = GetEdgeIterator(mesh)
    minDistance = float("inf")
    closestEdge = None
    for edge in edges:
        edgeId = GetID(edge)
        edgeIt.setIndex(edgeId)
        p1 = om.MVector(edgeIt.point(0, om.MSpace.kWorld))
        p2 = om.MVector(edgeIt.point(1, om.MSpace.kWorld))
        center = (p1 + p2) * 0.5
        delta = center - jointPos
        distance = delta * delta
        if distance < minDistance:
            minDistance = distance
            closestEdge = edge
    return closestEdge

def GetFarthestVertex(mesh, verts, joint):
    jointPos = JointPos(joint)
    points = GetMeshFn(mesh).getPoints(om.MSpace.kWorld)
    maxDistance = -1.0
    farthestVert = None
    for vert in verts:
        vertexId = GetID(vert)
        delta = om.MVector(points[vertexId]) - jointPos
        distance = delta * delta
        if distance > maxDistance:
            maxDistance = distance
            farthestVert = vert
    return farthestVert


def CheckEdgeLoopClosed(mesh, edges):
    edgeIds = [GetID(edge) for edge in edges]
    meshFn = GetMeshFn(mesh)
    vertexCount = {}
    for edgeId in edgeIds:
        v0, v1 = meshFn.getEdgeVertices(edgeId)
        vertexCount[v0] = vertexCount.get(v0, 0) + 1
        vertexCount[v1] = vertexCount.get(v1, 0) + 1
    return all(count == 2 for count in vertexCount.values())


def GetPerpEdge(v1, v2, threshold=0.25):
    mesh = v1.split(".")[0]
    vertexId = GetID(v1)
    targetId = GetID(v2)
    meshFn = GetMeshFn(mesh)
    points = meshFn.getPoints(om.MSpace.kWorld)
    p1 = om.MVector(points[vertexId])
    direction = om.MVector(points[targetId]) - p1
    if direction.length() < 1e-8:
        return None
    direction.normalize()
    vertIt = GetVertexIterator(mesh)
    vertIt.setIndex(vertexId)
    bestEdge = None
    bestScore = float("inf")
    for edgeId in vertIt.getConnectedEdges():
        v0, v1Id = meshFn.getEdgeVertices(edgeId)
        otherId = v1Id if v0 == vertexId else v0
        if otherId == targetId:
            continue
        edgeDir = om.MVector(points[otherId]) - p1
        if edgeDir.length() < 1e-8:
            continue
        edgeDir.normalize()
        score = abs(direction * edgeDir)
        if score < bestScore:
            bestScore = score
            bestEdge = edgeId
    if bestEdge is None or bestScore > threshold:
        return None
    return "{}.e[{}]".format(mesh, bestEdge)

def EdgeLoopToVerts(edge, angleTolerance=60):
    if not edge:
        return []
    mesh = edge.split(".")[0]
    seedId = GetID(edge)
    loopEdges = GetEdgeLoop(edge)
    if not loopEdges:
        return []
    edgeIt = GetEdgeIterator(mesh)
    def GetDir(edgeName):
        edgeIt.setIndex(GetID(edgeName))
        p0 = edgeIt.point(0, om.MSpace.kWorld)
        p1 = edgeIt.point(1, om.MSpace.kWorld)
        direction = om.MVector(p1 - p0)
        if direction.length() < 1e-8:
            return None
        direction.normalize()
        return direction
    minDot = math.cos(math.radians(angleTolerance))
    count = len(loopEdges)
    seedIndex = next((i for i, edgeName in enumerate(loopEdges) if GetID(edgeName) == seedId),None)
    if seedIndex is None:
        return []
    result = [loopEdges[seedIndex]]
    used = {seedIndex}
    # BACKWARD
    currentDir = GetDir(loopEdges[seedIndex])
    i = (seedIndex - 1) % count
    while i not in used:
        direction = GetDir(loopEdges[i])
        if direction is None or currentDir is None:
            break
        if abs(currentDir * direction) < minDot:
            break
        result.insert(0, loopEdges[i])
        used.add(i)
        currentDir = direction
        i = (i - 1) % count
    # FORWARD
    currentDir = GetDir(loopEdges[seedIndex])
    i = (seedIndex + 1) % count
    while i not in used:
        direction = GetDir(loopEdges[i])
        if direction is None or currentDir is None:
            break
        if abs(currentDir * direction) < minDot:
            break
        result.append(loopEdges[i])
        used.add(i)
        currentDir = direction
        i = (i + 1) % count
    verts = cmds.polyListComponentConversion(result,fromEdge=True,toVertex=True)
    return cmds.ls(verts, fl=True) or []

def EdgesToVerts(edges):
    if not edges:
        return []
    if isinstance(edges, str):
        edges = [edges]
    mesh = edges[0].split(".")[0]
    meshFn = GetMeshFn(mesh)
    vertices = set()
    for edge in edges:
        edgeId = GetID(edge)
        v0, v1 = meshFn.getEdgeVertices(edgeId)
        vertices.add(v0)
        vertices.add(v1)
    return [
        "{}.vtx[{}]".format(mesh, vertexId)
        for vertexId in sorted(vertices)
    ]


def GetConnectVerts(v, vertSet):
    mesh = v.split(".")[0]
    vertexId = GetID(v)
    vertSetIds = {GetID(vertex) for vertex in vertSet}
    meshFn = GetMeshFn(mesh)
    vertIt = GetVertexIterator(mesh)
    vertIt.setIndex(vertexId)
    result = []
    for edgeId in vertIt.getConnectedEdges():
        v0, v1 = meshFn.getEdgeVertices(edgeId)
        otherId = v1 if v0 == vertexId else v0
        if otherId in vertSetIds:
            result.append((v,"{}.vtx[{}]".format(mesh, otherId),"{}.e[{}]".format(mesh, edgeId)))
    return result


def GetJointAxis(joint):
    matrix = cmds.xform(joint, q=True, ws=True, m=True)
    return om.MVector(matrix[0], matrix[1], matrix[2]).normal()


def GetJointEdge(mesh, joint, vertex_index):
    return GetBestEdgeByAxis(mesh,joint,vertex_index,perpendicular=False)


def GetJointEdgeLoop(mesh, joint, vtxIndex):
    edge_id = GetJointEdge(mesh, joint, vtxIndex)
    if edge_id is None:
        cmds.warning("No edge found")
        return []
    return GetEdgeLoop("{}.e[{}]".format(mesh, edge_id))


def GetClosestJoints(targetJoint, joints, count=1):
    result = []
    for joint in joints:
        if joint == targetJoint:
            continue
        distance = NLTA_General.GetDistance(targetJoint, joint)
        result.append((joint, distance))
    result.sort(key=lambda item: item[1])
    return result[:count]
    

def GetPerpendicularEdge(mesh, joint, vertex_index):
    return GetBestEdgeByAxis(mesh,joint,vertex_index,perpendicular=True)

def GetPerpendicularEdgeLoop(mesh, joint, vtxIndex):
    edge_id = GetPerpendicularEdge(mesh, joint, vtxIndex)
    if edge_id is None:
        cmds.warning("No edge found")
        return []
    return GetEdgeLoop("{}.e[{}]".format(mesh, edge_id))

def GetTwoClosestJoints(targetJoint, joints):
    return GetClosestJoints(targetJoint, joints, 2)

def GetClosestJoint(targetJoint, joints):
    return GetClosestJoints(targetJoint, joints, 1)

def GetBestEdgeByAxis(mesh, joint, vertex_index, perpendicular=False):
    dag = GetMeshData(mesh)["dag"]
    joint_axis = GetJointAxis(joint)
    edge_it = om.MItMeshEdge(dag)
    edges = GetConnectedEdges(mesh, vertex_index)
    best_edge = None
    best_value = float("inf") if perpendicular else -1.0
    for edge_id in edges:
        edge_it.setIndex(edge_id)
        p1 = om.MVector(edge_it.point(0, om.MSpace.kWorld))
        p2 = om.MVector(edge_it.point(1, om.MSpace.kWorld))
        direction = (p2 - p1).normal()
        dot = abs(direction * joint_axis)
        if perpendicular:
            if dot < best_value:
                best_value = dot
                best_edge = edge_id
        elif dot > best_value:
            best_value = dot
            best_edge = edge_id
    return best_edge


def EdgesBetween(mesh, edgeSource, edgeTarget):
    id1 = GetID(edgeSource)
    id2 = GetID(edgeTarget)
    edges = cmds.polySelect(mesh,edgeRingPath=(id1, id2), noSelection=True)
    if edges is None:
        edges = cmds.polySelect(mesh,edgeLoopPath=(id1, id2),noSelection=True)
    if edges is None:
        return []
    if isinstance(edges, int):
        edges = [edges]
    return ["{}.e[{}]".format(mesh, edgeId) for edgeId in edges]


def CheckEdgesBetween(mesh, edgeSource, edges):
    sourceId = GetID(edgeSource)
    for edge in edges:
        targetId = GetID(edge)
        result = cmds.polySelect(mesh,edgeRingPath=(sourceId, targetId),noSelection=True)
        if result:
            return edge
    return []


def EdgeRatioBetweenJoints(mesh, edgeId, jointA, jointB):
    pA = JointPos(jointA)
    pB = JointPos(jointB)
    edgeCenter = EdgeCenter(mesh, edgeId)
    boneVector = pB - pA
    edgeVector = edgeCenter - pA
    lengthSquared = boneVector * boneVector
    if lengthSquared == 0:
        return 0.0
    ratio = (edgeVector * boneVector) / lengthSquared
    return max(0.0, min(1.0, ratio))

def EdgeRatioBetweenEdges(mesh, edgeMid, edgeA, edgeB):
    pA = EdgeCenter(mesh, edgeA)
    pB = EdgeCenter(mesh, edgeB)
    pC = EdgeCenter(mesh, edgeMid)
    vectorAB = pB - pA
    vectorAC = pC - pA
    lengthSquared = vectorAB * vectorAB
    if lengthSquared == 0:
        return 0.0
    ratio = (vectorAC * vectorAB) / lengthSquared
    return max(0.0, min(1.0, ratio))


def GetMeshComponents(mesh):
    meshFn = GetMeshFn(mesh)
    adjacency = [[] for _ in range(meshFn.numVertices)]
    for edgeId in range(meshFn.numEdges):
        v1, v2 = meshFn.getEdgeVertices(edgeId)
        adjacency[v1].append(v2)
        adjacency[v2].append(v1)
    visited = set()
    components = []
    for startVertex in range(meshFn.numVertices):
        if startVertex in visited:
            continue
        component = []
        stack = [startVertex]
        visited.add(startVertex)
        while stack:
            vertex = stack.pop()
            component.append(vertex)
            for neighbor in adjacency[vertex]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components

def SelectVerticesWithinRadius(mesh, joint, verts, radius):
    jointPos = JointPos(joint)
    meshFn = GetMeshFn(mesh)
    points = meshFn.getPoints(om.MSpace.kWorld)
    radiusSquared = radius * radius
    result = []
    for vert in verts:
        vertexId = GetID(vert)
        delta = points[vertexId] - jointPos
        if delta * delta <= radiusSquared:
            result.append(vert)
    return result


def SelectLoopRegion(mesh, joint, joints, verts):
    closest = GetClosestJoints(joint, joints, 2)
    if len(closest) < 2:
        cmds.warning("Need at least 2 other joints")
        return []
    radius = min(closest[0][1], closest[1][1]) * 0.7
    return SelectVerticesWithinRadius(mesh, joint, verts, radius)


def GetIntersectVerts(meshA, meshB, threshold, *arr):
    sourceFn = GetMeshFn(meshA)
    targetFn = GetMeshFn(meshB)
    points = sourceFn.getPoints(om.MSpace.kWorld)
    thresholdSquared = threshold * threshold
    result = []
    for vertexId, point in enumerate(points):
        closestPoint, _ = targetFn.getClosestPoint(point, om.MSpace.kWorld)
        delta = point - closestPoint
        if delta * delta <= thresholdSquared:
            result.append("{}.vtx[{}]".format(meshA, vertexId))
    return result


def GetVertexBetweenParentChild(data, *arr):
    mesh = data["mesh"]
    source = data["source"]
    destination = data["destination"]
    closestVertex = GetClosestVertex(mesh,source)
    edgeLoop = GetJointEdgeLoop(mesh,source,closestVertex)
    sourceEdge = GetClosestEdge(mesh,edgeLoop,source)
    destinationEdge = GetClosestEdge(mesh,edgeLoop,destination)
    edgeBetween = EdgesBetween(mesh,sourceEdge,destinationEdge)
    cmds.select(edgeBetween)


def GetVertRatioBetweenJoints(data, *arr):
    vert = data["vert"]
    joints = data["joints"]
    if len(joints) != 2:
        cmds.error("Need exactly 2 joints")
    joint1, joint2 = joints
    dist1 = NLTA_General.GetDistance(vert,joint1)
    dist2 = NLTA_General.GetDistance(vert,joint2)
    total = dist1 + dist2
    if total == 0:
        ratio1 = 0.5
        ratio2 = 0.5
    else:
        ratio1 = 1.0 - (dist1 / total)
        ratio2 = 1.0 - (dist2 / total)
    return {"vert": vert,"joints": [joint1, joint2],"ratios": [ratio1, ratio2]}


def GetClosestVertex(mesh, joint):
    meshFn = GetMeshFn(mesh)
    jointPos = om.MPoint(cmds.xform(joint, q=True, ws=True, t=True))
    closestPoint, _ = meshFn.getClosestPoint(jointPos, om.MSpace.kWorld)
    vertices = meshFn.getPoints(om.MSpace.kWorld)
    closestIndex = -1
    minDistance = float("inf")
    for index, vertex in enumerate(vertices):
        delta = vertex - closestPoint
        distance = delta * delta
        if distance < minDistance:
            minDistance = distance
            closestIndex = index
    return closestIndex


def GetEdgeLoop(startEdge, *arr):
    mesh = startEdge.split(".")[0] if isinstance(startEdge, str) else None
    edgeId = GetID(startEdge)
    if mesh is None:
        cmds.error("startEdge must be a mesh edge component.")
    data = GetMeshData(mesh)
    edgeIt = om.MItMeshEdge(data["dag"])
    vertIt = om.MItMeshVertex(data["dag"])
    visited = set()
    def Walk(edgeId, fromVertex):
        result = []
        while True:
            if edgeId in visited:
                break
            visited.add(edgeId)
            result.append(edgeId)
            edgeIt.setIndex(edgeId)
            v0 = edgeIt.vertexId(0)
            v1 = edgeIt.vertexId(1)
            nextVertex = v1 if v0 == fromVertex else v0
            vertIt.setIndex(nextVertex)
            connectedEdges = vertIt.getConnectedEdges()
            if vertIt.onBoundary():
                candidates = []
                for edge in connectedEdges:
                    if edge == edgeId:
                        continue
                    edgeIt.setIndex(edge)
                    if edgeIt.onBoundary():
                        candidates.append(edge)
                if len(candidates) != 1:
                    break
                nextEdge = candidates[0]
            else:
                if len(connectedEdges) != 4:
                    break
                nextEdge = None
                currentFaces = set(edgeIt.getConnectedFaces())
                for edge in connectedEdges:
                    if edge == edgeId:
                        continue
                    edgeIt.setIndex(edge)
                    if edgeIt.onBoundary():
                        continue
                    commonFaces = currentFaces & set(edgeIt.getConnectedFaces())
                    if not commonFaces:
                        nextEdge = edge
                        break
                if nextEdge is None:
                    break
            edgeId = nextEdge
            fromVertex = nextVertex
        return result
    edgeIt.setIndex(edgeId)
    v0 = edgeIt.vertexId(0)
    v1 = edgeIt.vertexId(1)
    loop = []
    loop.extend(reversed(Walk(edgeId, v0)))
    visited.discard(edgeId)
    loop.extend(Walk(edgeId, v1))
    result = []
    seen = set()
    for edge in loop:
        if edge in seen:
            continue
        seen.add(edge)
        result.append("{}.e[{}]".format(mesh, edge))
    return result


def SortCircularJoints(joints, clockwise=False):
    if len(joints) < 3:
        return joints[:]
    positions = {joint: om.MVector(cmds.xform(joint, q=True, ws=True, t=True)) for joint in joints}
    center = sum(positions.values(), om.MVector())
    center /= len(joints)
    maxDistance = -1.0
    xAxis = None
    for i, jointA in enumerate(joints):
        for jointB in joints[i + 1:]:
            vector = positions[jointA] - positions[jointB]
            distance = vector * vector
            if distance > maxDistance:
                maxDistance = distance
                xAxis = vector.normal()
    normal = om.MVector()
    vectors = [positions[joint] - center for joint in joints]
    for i, vectorA in enumerate(vectors):
        for vectorB in vectors[i + 1:]:
            normal += vectorA ^ vectorB
    if normal.length() < 1e-6:
        cmds.warning("Cannot compute normal.")
        return joints[:]
    normal.normalize()
    yAxis = normal ^ xAxis
    yAxis.normalize()
    result = []
    for joint in joints:
        vector = positions[joint] - center
        x = vector * xAxis
        y = vector * yAxis
        angle = math.atan2(y, x)
        result.append((angle, joint))
    result.sort(key=lambda item: item[0], reverse=clockwise)
    return [joint for _, joint in result]


def Normalize(vector):
    length = math.sqrt(sum(value * value for value in vector))
    return vector if length == 0 else [value / length for value in vector]

def Dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def GetPos(vertex):
    return cmds.xform(vertex, q=True, ws=True, t=True)

def ListToPerVerts(verts, threshold=9999):
    returnData = {}
    for vertex in verts:
        connections = GetConnectVerts(vertex, verts)
        for source, target, _ in connections:
            edge = GetPerpEdge(source, target, threshold)
            if edge is None:
                continue
            returnData[vertex] = EdgeLoopToVerts(edge)
    return returnData



def GetMirrorVertexByUv(vtx, axis="U", tol=0.01):
    mesh = vtx.split(".")[0]
    uvs = cmds.polyListComponentConversion(vtx, tuv=True)
    uvs = cmds.ls(uvs, fl=True)
    if not uvs:
        return None
    uv = uvs[0]
    u, v = cmds.polyEditUV(uv, q=True)
    if axis.upper() == "U":
        target_uv = (1.0 - u, v)
    else:
        target_uv = (u, 1.0 - v)
    vtx_count = cmds.polyEvaluate(mesh, v=True)
    best = None
    best_dist = 999999
    for i in range(vtx_count):
        other = "{}.vtx[{}]".format(mesh,i)
        other_uvs = cmds.polyListComponentConversion(other,tuv=True)
        other_uvs = cmds.ls(other_uvs, fl=True)
        if not other_uvs:
            continue
        ou, ov = cmds.polyEditUV(other_uvs[0],q=True )
        dist = (abs(ou - target_uv[0]) + abs(ov - target_uv[1]))
        if dist < best_dist:
            best_dist = dist
            best = other
    if best_dist <= tol:
        return best
    return None


def MirrorVertexByUvSingle(vtx, axis="X"):
    mirror_vtx = GetMirrorVertexByUv(vtx)
    if not mirror_vtx:
        cmds.warning("Mirror vertex not found")
        return
    pos = cmds.pointPosition(vtx, w=True)
    x, y, z = pos
    axis = axis.upper()
    if axis == "X":
        mirrored_pos = (-x, y, z)
    elif axis == "Y":
        mirrored_pos = (x, -y, z)
    elif axis == "Z":
        mirrored_pos = (x, y, -z)
    else:
        cmds.warning("Invalid axis")
        return
    cmds.xform(mirror_vtx, ws=True, t=mirrored_pos)

def MirrorVertexByUv(*arr):
    verts = cmds.ls(selection=True,flatten=True)
    for vert in verts:
        MirrorVertexByUvSingle(vert)

def MirrorVertPos(*arr):
    sel = cmds.ls(orderedSelection=True)
    if len(sel) != 2:
        cmds.warning("Select source vertex then target vertex")
        return
    src = sel[0]
    dst = sel[1]
    x, y, z = cmds.pointPosition(src, w=True)
    mirrored_pos = (-x, y, z)
    cmds.xform(dst,ws=True,t=mirrored_pos)

def ColorVertices(vertices, color=(1, 0, 0, 1)):
    meshMap = {}
    for vertex in vertices:
        mesh = vertex.split(".")[0]
        meshMap.setdefault(mesh, []).append(GetID(vertex))
    for mesh, ids in meshMap.items():
        meshFn = GetMeshFn(mesh)
        meshFn.setVertexColors([om.MColor(color)] * len(ids), ids)
        shape = cmds.listRelatives(mesh, s=True, ni=True)
        if shape:
            cmds.setAttr(shape[0] + ".displayColors", 1)



def MatchVertexPairs(meshA, meshB, vertsA, vertsB):
    def GetMesh(mesh):
        sel = om.MSelectionList()
        sel.add(mesh)
        path = sel.getDagPath(0)
        fn = om.MFnMesh(path)
        return path, fn
    pathA, fnA = GetMesh(meshA)
    pathB, fnB = GetMesh(meshB)
    if len(vertsA) != 3 or len(vertsB) != 3:
        raise ValueError("Exactly 3 vertices are required for each mesh.")
    if fnA.numVertices != fnB.numVertices:
        raise ValueError("Meshes have different vertex counts.")
    def BuildVertexFaces(path, vertexCount):
        result = {}
        it = om.MItMeshVertex(path)
        for vertexID in range(vertexCount):
            it.setIndex(vertexID)
            result[vertexID] = set(it.getConnectedFaces())
        return result

    vertexFacesA = BuildVertexFaces(pathA,fnA.numVertices)
    vertexFacesB = BuildVertexFaces(pathB,fnB.numVertices)

    def FindSeedFace(fn, vertexFaces, vertices):
        commonFaces = (vertexFaces[vertices[0]] & vertexFaces[vertices[1]] & vertexFaces[vertices[2]] )
        for faceID in commonFaces:
            faceVertices = list(fn.getPolygonVertices(faceID))
            if not all(vertex in faceVertices for vertex in vertices):
                continue
            count = len(faceVertices)
            for center in vertices:
                index = faceVertices.index(center)
                prevVertex = faceVertices[(index - 1) % count]
                nextVertex = faceVertices[(index + 1) % count]
                others = [vertex for vertex in vertices if vertex != center ]
                if (others[0] in (prevVertex, nextVertex) and others[1] in (prevVertex, nextVertex)):
                    return faceID
        raise ValueError(
            "The 3 vertices must lie on the same face "
            "and form 2 connected edges."
        )
    seedFaceA = FindSeedFace(fnA,vertexFacesA,vertsA)
    seedFaceB = FindSeedFace(fnB,vertexFacesB,vertsB)

    def FindCenterVertex(fn, faceID, vertices):
        faceVertices = list(fn.getPolygonVertices(faceID))
        count = len(faceVertices)
        for center in vertices:
            index = faceVertices.index(center)
            prevVertex = faceVertices[ (index - 1) % count ]
            nextVertex = faceVertices[ (index + 1) % count ]
            others = [ vertex for vertex in vertices if vertex != center ]
            if ( others[0] in (prevVertex, nextVertex) and others[1] in (prevVertex, nextVertex) ):
                return center
        raise ValueError( "Could not determine center vertex." )
    centerA = FindCenterVertex(fnA,seedFaceA,vertsA)
    centerB = FindCenterVertex(fnB,seedFaceB,vertsB)

    outerA = [ vertex for vertex in vertsA if vertex != centerA ]
    outerB = [ vertex for vertex in vertsB if vertex != centerB ]

    mapping = { centerA: centerB }
    reverseMapping = { centerB: centerA }
    mapping[outerA[0]] = outerB[0]
    mapping[outerA[1]] = outerB[1]
    reverseMapping[outerB[0]] = outerA[0]
    reverseMapping[outerB[1]] = outerA[1]

    def GetComponent(path, startVertex):
        component = set()
        it = om.MItMeshVertex(path)
        stack = [startVertex]
        while stack:
            vertexID = stack.pop()
            if vertexID in component:
                continue
            component.add(vertexID)
            it.setIndex(vertexID)
            neighbors = it.getConnectedVertices()
            for neighbor in neighbors:
                if neighbor not in component:
                    stack.append(neighbor)
        return component

    componentA = GetComponent(pathA,centerA)
    componentB = GetComponent(pathB,centerB)
    if len(componentA) != len(componentB):
        raise ValueError(
            "Selected components have different vertex counts."
        )

    faceMapping = {seedFaceA: seedFaceB}
    reverseFaceMapping = {seedFaceB: seedFaceA}

    def FindMatchingFace(faceA):
        verticesA = list(fnA.getPolygonVertices(faceA))
        mappedVertices = []
        for vertexA in verticesA:
            if vertexA in mapping:
                mappedVertices.append(mapping[vertexA])
        if len(mappedVertices) < 2:
            return None
        candidateFaces = None
        for vertexB in mappedVertices:
            faces = vertexFacesB[vertexB]
            if candidateFaces is None:
                candidateFaces = set(faces)
            else:
                candidateFaces &= faces

        if not candidateFaces:
            return None

        for faceB in candidateFaces:
            if faceB in reverseFaceMapping:
                continue

            verticesB = set(fnB.getPolygonVertices(faceB))
            if all( vertex in verticesB for vertex in mappedVertices ):
                return faceB
        return None

    def MapFace(faceA, faceB):
        verticesA = list(fnA.getPolygonVertices(faceA))
        verticesB = list(fnB.getPolygonVertices(faceB))
        if len(verticesA) != len(verticesB):
            raise ValueError(
                "Topology mismatch: face vertex count differs."
            )
        count = len(verticesA)
        candidates = []

        for reverse in (False, True):
            orderA = (list(reversed(verticesA)) if reverse else verticesA )
            for offset in range(count):
                valid = True
                candidate = []
                for i in range(count):
                    vertexA = orderA[i]
                    vertexB = verticesB[ (i + offset) % count ]
                    if vertexA in mapping:
                        if mapping[vertexA] != vertexB:
                            valid = False
                            break
                    if vertexB in reverseMapping:
                        if reverseMapping[vertexB] != vertexA:
                            valid = False
                            break
                    candidate.append( (vertexA, vertexB) )
                if valid:
                    candidates.append(candidate)
        if not candidates:
            raise RuntimeError( "Cannot determine mapping for face {} -> {}.".format( faceA, faceB ) )

        if len(candidates) > 1:
            raise RuntimeError( "Ambiguous topology at face {} -> {}. " "More seed vertices are required.".format( faceA, faceB ) )
        for vertexA, vertexB in candidates[0]:
            if vertexA not in mapping:
                mapping[vertexA] = vertexB
                reverseMapping[vertexB] = vertexA
    processedFaces = set()
    changed = True
    while changed:
        changed = False
        for faceA in list(faceMapping.keys()):
            if faceA in processedFaces:
                continue
            faceB = faceMapping[faceA]
            MapFace( faceA, faceB )
            processedFaces.add(faceA)
            changed = True
            verticesA = fnA.getPolygonVertices(faceA)
            for vertexA in verticesA:
                if vertexA not in mapping:
                    continue
                vertexB = mapping[vertexA]
                for nextFaceA in vertexFacesA[vertexA]:
                    if nextFaceA in faceMapping:
                        continue
                    nextFaceB = FindMatchingFace(nextFaceA)
                    if nextFaceB is None:
                        continue
                    faceMapping[nextFaceA] = nextFaceB
                    reverseFaceMapping[nextFaceB] = nextFaceA

    missing = [ vertex for vertex in componentA if vertex not in mapping ]
    if missing:
        raise RuntimeError(
            "Failed to match entire component. "
            "{} vertices remain.".format(
                len(missing)
            )
        )

    return [
        (vertexA, mapping[vertexA])
        for vertexA in sorted(componentA)
    ]


def FindSymmetricVertexPairs(mesh, vertsA, vertsB):
    if len(vertsA) != 3 or len(vertsB) != 3:
        raise ValueError("Exactly 3 vertices are required on each component.")
    if set(vertsA) & set(vertsB):
        raise ValueError("vertsA and vertsB must belong to different components.")

    # ---------------------------------------------------------
    # Get mesh
    # ---------------------------------------------------------

    sel = om.MSelectionList()
    sel.add(mesh)
    path = sel.getDagPath(0)
    fn = om.MFnMesh(path)

    # ---------------------------------------------------------
    # Build vertex -> faces
    # ---------------------------------------------------------

    vertexFaces = {}
    it = om.MItMeshVertex(path)
    for vertexID in range(fn.numVertices):
        it.setIndex(vertexID)
        vertexFaces[vertexID] = set(it.getConnectedFaces())

    # ---------------------------------------------------------
    # Find common face
    # ---------------------------------------------------------

    def FindCommonFace(vertices):
        common = set(vertexFaces[vertices[0]])
        for vertex in vertices[1:]:
            common &= vertexFaces[vertex]
        if not common:
            return None
        return next(iter(common))
    faceA = FindCommonFace(vertsA)
    faceB = FindCommonFace(vertsB)

    if faceA is None:
        raise ValueError("vertsA are not on the same face.")

    if faceB is None:
        raise ValueError("vertsB are not on the same face.")

    # ---------------------------------------------------------
    # Find center vertex
    #
    # The 3 selected vertices must form 2 connected edges.
    # ---------------------------------------------------------
    def FindCenterVertex(faceID, vertices):
        faceVertices = list(fn.getPolygonVertices(faceID))
        count = len(faceVertices)
        for vertex in vertices:
            index = faceVertices.index(vertex)
            prevVertex = faceVertices[(index - 1) % count]
            nextVertex = faceVertices[(index + 1) % count]
            others = [v for v in vertices if v != vertex]
            if (others[0] in (prevVertex, nextVertex) and others[1] in (prevVertex, nextVertex)):
                return vertex
        return None

    centerA = FindCenterVertex(faceA, vertsA)
    centerB = FindCenterVertex(faceB, vertsB)
    if centerA is None or centerB is None:
        raise ValueError(
            "Each group of 3 vertices must form "
            "2 connected edges on the same face."
        )

    # ---------------------------------------------------------
    # Get connected component
    # ---------------------------------------------------------

    def GetComponent(startVertex):
        component = set()
        stack = [startVertex]
        it = om.MItMeshVertex(path)
        while stack:
            vertex = stack.pop()
            if vertex in component:
                continue
            component.add(vertex)
            it.setIndex(vertex)
            for neighbor in it.getConnectedVertices():
                if neighbor not in component:
                    stack.append(neighbor)
        return component
    componentA = GetComponent(centerA)
    componentB = GetComponent(centerB)

    # Verify seeds
    if not all(vertex in componentA for vertex in vertsA):
        raise ValueError("vertsA are not in the same component.")

    if not all( vertex in componentB for vertex in vertsB):
        raise ValueError("vertsB are not in the same component.")

    if len(componentA) != len(componentB):
        raise ValueError(
            "The two components have different vertex counts: "
            "{} vs {}".format(
                len(componentA),
                len(componentB)
            )
        )

    # ---------------------------------------------------------
    # Build face -> vertices
    # ---------------------------------------------------------

    faceVertices = {}
    componentFacesA = set()
    componentFacesB = set()

    for vertex in componentA:
        componentFacesA.update(vertexFaces[vertex])

    for vertex in componentB:
        componentFacesB.update(vertexFaces[vertex])

    for faceID in componentFacesA | componentFacesB:
        faceVertices[faceID] = list(fn.getPolygonVertices(faceID))

    # ---------------------------------------------------------
    # Initial vertex mapping
    # ---------------------------------------------------------

    mapping = {}
    reverseMapping = {}
    for a, b in zip(vertsA, vertsB):

        if a in mapping and mapping[a] != b:
            raise ValueError("Conflicting mapping on component A.")

        if b in reverseMapping and reverseMapping[b] != a:
            raise ValueError("Conflicting mapping on component B.")
        mapping[a] = b
        reverseMapping[b] = a

    # ---------------------------------------------------------
    # Initial face mapping
    # ---------------------------------------------------------

    faceMapping = {faceA: faceB}
    reverseFaceMapping = {faceB: faceA}

    # ---------------------------------------------------------
    # Map a face using cyclic topology
    # ---------------------------------------------------------

    def MapFace(sourceFace, targetFace):
        source = faceVertices[sourceFace]
        target = faceVertices[targetFace]
        if len(source) != len(target):
            raise RuntimeError("Face topology mismatch: {} -> {}".format(sourceFace,targetFace))
        count = len(source)
        candidates = []
        # -----------------------------------------------------
        # Try both winding directions and all cyclic offsets.
        # -----------------------------------------------------
        for reverse in (False, True):
            sourceOrder = (list(reversed(source)) if reverse else source)
            for offset in range(count):
                candidate = []
                valid = True
                for i in range(count):
                    vertexA = sourceOrder[i]
                    vertexB = target[ (i + offset) % count ]
                    if vertexA in mapping:
                        if mapping[vertexA] != vertexB:
                            valid = False
                            break
                    if vertexB in reverseMapping:
                        if reverseMapping[vertexB] != vertexA:
                            valid = False
                            break
                    candidate.append((vertexA, vertexB))
                if valid:
                    candidates.append(candidate)

        if not candidates:
            raise RuntimeError("Cannot map face {} -> {}.".format(sourceFace,targetFace))

        # -----------------------------------------------------
        # If there is more than one valid solution, topology
        # alone cannot distinguish them.
        # -----------------------------------------------------
        if len(candidates) > 1:
            raise RuntimeError(
                "Ambiguous topology between face {} and {}. "
                "The selected 3 vertices are not enough "
                "to uniquely determine the symmetry.".format(
                    sourceFace,
                    targetFace
                )
            )

        candidate = candidates[0]
        for vertexA, vertexB in candidate:
            if vertexA not in mapping:
                mapping[vertexA] = vertexB
                reverseMapping[vertexB] = vertexA

    # ---------------------------------------------------------
    # Find target face from mapped vertices
    # ---------------------------------------------------------

    def FindMatchingFace(sourceFace):
        sourceVertices = faceVertices[sourceFace]
        mappedVertices = []
        for vertexA in sourceVertices:
            if vertexA in mapping:
                mappedVertices.append(mapping[vertexA])

        if len(mappedVertices) < 2:
            return None
        candidates = None
        for vertexB in mappedVertices:
            faces = ( vertexFaces[vertexB] & componentFacesB)
            if candidates is None:
                candidates = set(faces)
            else:
                candidates &= faces

        if not candidates:
            return None

        for targetFace in candidates:
            if targetFace in reverseFaceMapping:
                continue
            targetVertices = set(faceVertices[targetFace])
            if all(vertexB in targetVertices for vertexB in mappedVertices):
                return targetFace
        return None

    # ---------------------------------------------------------
    # Traverse from component A to component B
    # ---------------------------------------------------------

    processedFaces = set()
    while True:
        progress = False
        for sourceFace in list(faceMapping.keys()):
            if sourceFace in processedFaces:
                continue
            targetFace = faceMapping[sourceFace]
            # Map vertices of this face
            MapFace(sourceFace,targetFace)
            processedFaces.add(sourceFace)
            progress = True
            # Find neighboring faces
            sourceVertices = faceVertices[sourceFace]
            for vertexA in sourceVertices:
                if vertexA not in mapping:
                    continue
                for nextFaceA in vertexFaces[vertexA]:
                    if nextFaceA not in componentFacesA:
                        continue
                    if nextFaceA in faceMapping:
                        continue
                    nextFaceB = FindMatchingFace(nextFaceA)
                    if nextFaceB is None:
                        continue
                    if nextFaceB in reverseFaceMapping:
                        continue
                    faceMapping[nextFaceA] = nextFaceB
                    reverseFaceMapping[nextFaceB] = nextFaceA
                    progress = True
        if not progress:
            break

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    missingA = [vertex for vertex in componentA if vertex not in mapping ]
    if missingA:
        raise RuntimeError(
            "Could not match entire component. "
            "{} vertices remain.".format(
                len(missingA)
            )
        )
    # Make sure every target vertex was mapped
    if len(mapping) != len(componentA):
        raise RuntimeError("Mapping count mismatch.")

    return [
        (vertexA, mapping[vertexA])
        for vertexA in sorted(componentA)
    ]


def CopySkinByVertexPairs(meshA, meshB, pairs):
    if not pairs:
        return

    dagA, skinA = GetSkinData(meshA)
    dagB, skinB = GetSkinData(meshB)

    if skinA is None:
        raise RuntimeError("No skinCluster found on {}".format(meshA))
    if skinB is None:
        raise RuntimeError("No skinCluster found on {}".format(meshB))

    influencesA = skinA.influenceObjects()
    influencesB = skinB.influenceObjects()
    influenceIndexB = {
        om.MFnDagNode(influence).fullPathName(): index
        for index, influence in enumerate(influencesB)
    }

    influenceMap = {}
    for indexA, influence in enumerate(influencesA):
        name = om.MFnDagNode(influence).fullPathName()
        if name not in influenceIndexB:
            raise RuntimeError("Influence '{}' from {} does not exist on {}.".format(name, meshA, meshB))
        influenceMap[indexA] = influenceIndexB[name]

    sourceComponent = CreateVertexComponent([vertexA for vertexA, _ in pairs])
    targetComponent = CreateVertexComponent([vertexB for _, vertexB in pairs])
    sourceWeights, influenceCountA = skinA.getWeights(dagA, sourceComponent)

    influenceCountB = len(influencesB)
    targetWeights = [0.0] * (len(pairs) * influenceCountB)

    for vertexIndex in range(len(pairs)):
        sourceOffset = vertexIndex * influenceCountA
        targetOffset = vertexIndex * influenceCountB

        for sourceInfluenceIndex in range(influenceCountA):
            weight = sourceWeights[sourceOffset + sourceInfluenceIndex]
            if weight:
                targetWeights[targetOffset + influenceMap[sourceInfluenceIndex]] = weight

    skinB.setWeights(
        dagB,
        targetComponent,
        om.MIntArray(range(influenceCountB)),
        om.MDoubleArray(targetWeights),
        False
    )
    print("Copied skin weights: {} vertices".format(len(pairs)))


def FindMirrorJointPairs(joints, axis=0, tolerance=0.001):
    jointData = {}

    for joint in joints:
        dagPath = NLTA_OpenMaya.GetDagPath(joint)
        position = om.MTransformationMatrix(dagPath.inclusiveMatrix()).translation(om.MSpace.kWorld)
        jointData[joint] = (position.x, position.y, position.z)

    toleranceSquared = tolerance * tolerance
    pairs = []
    used = set()

    for jointA, positionA in jointData.items():
        if jointA in used:
            continue

        mirrored = list(positionA)
        mirrored[axis] *= -1.0

        if abs(positionA[axis]) <= tolerance:
            pairs.append((jointA, jointA))
            used.add(jointA)
            continue

        bestJoint = None
        bestDistance = None

        for jointB, positionB in jointData.items():
            if jointB == jointA or jointB in used:
                continue

            distance = sum((mirrored[i] - positionB[i]) ** 2 for i in range(3))
            if distance > toleranceSquared:
                continue

            if bestDistance is None or distance < bestDistance:
                bestJoint = jointB
                bestDistance = distance

        if bestJoint is not None:
            pairs.append((jointA, bestJoint))
            used.update((jointA, bestJoint))

    return pairs

def MirrorSkinByPairs(mesh, vertexPairs, jointPairs):
    if not vertexPairs:
        return

    dagPath, skinFn = GetSkinData(mesh)
    if skinFn is None:
        raise RuntimeError("No skinCluster found on {}".format(mesh))

    influences = skinFn.influenceObjects()
    influenceNames = {
        om.MFnDagNode(influence).fullPathName(): index
        for index, influence in enumerate(influences)
    }

    jointMap = {}
    for jointA, jointB in jointPairs:
        if jointA not in influenceNames:
            raise RuntimeError("{} is not an influence of {}".format(jointA, mesh))
        if jointB not in influenceNames:
            raise RuntimeError("{} is not an influence of {}".format(jointB, mesh))
        jointMap[influenceNames[jointA]] = influenceNames[jointB]

    sourceComponent = CreateVertexComponent([vertexA for vertexA, _ in vertexPairs])
    targetComponent = CreateVertexComponent([vertexB for _, vertexB in vertexPairs])
    sourceWeights, influenceCount = skinFn.getWeights(dagPath, sourceComponent)
    targetWeights = om.MDoubleArray(len(vertexPairs) * influenceCount, 0.0)

    for vertexIndex in range(len(vertexPairs)):
        offset = vertexIndex * influenceCount

        for influenceA in range(influenceCount):
            weight = sourceWeights[offset + influenceA]
            if not weight:
                continue

            influenceB = jointMap.get(influenceA)
            if influenceB is not None:
                targetWeights[offset + influenceB] = weight

    skinFn.setWeights(
        dagPath,
        targetComponent,
        om.MIntArray(range(influenceCount)),
        targetWeights,
        False
    )
    print("Mirrored skin: {} vertices".format(len(vertexPairs)))


def GetSymmetryPlaneFromPairs(mesh, pairs):
    if len(pairs) != 3:
        raise ValueError("Exactly 3 vertex pairs are required.")

    meshFn = GetMeshFn(mesh)
    midpoints = []

    for vertexA, vertexB in pairs:
        pointA = meshFn.getPoint(vertexA, om.MSpace.kWorld)
        pointB = meshFn.getPoint(vertexB, om.MSpace.kWorld)
        midpoints.append(om.MPoint(
            (pointA.x + pointB.x) * 0.5,
            (pointA.y + pointB.y) * 0.5,
            (pointA.z + pointB.z) * 0.5
        ))

    p0, p1, p2 = midpoints
    normal = (p1 - p0) ^ (p2 - p0)

    if normal.length() < 1e-8:
        raise ValueError("The 3 midpoint positions are collinear. Cannot determine symmetry plane.")

    normal.normalize()
    return p0, normal

def MirrorPointByPlane(point, planePoint, planeNormal):
    vector = point - planePoint
    distance = vector * planeNormal
    return point - (planeNormal * (2.0 * distance))

def MirrorVertexPositionsByPairs(mesh, pairs):
    if not pairs:
        return
    if len(pairs) < 3:
        raise ValueError("At least 3 vertex pairs are required.")

    planePoint, planeNormal = GetSymmetryPlaneFromPairs(mesh, pairs[:3])
    meshFn = GetMeshFn(mesh)
    points = meshFn.getPoints(om.MSpace.kWorld)

    for vertexA, vertexB in pairs:
        points[vertexB] = MirrorPointByPlane(points[vertexA], planePoint, planeNormal)

    meshFn.setPoints(points, om.MSpace.kWorld)
    meshFn.updateSurface()


def GetMirrorPairsSameComponent(mesh, vertsA, vertsB, tolerance=0.0001):
    if len(vertsA) != 3 or len(vertsB) != 3:
        raise ValueError("Exactly 3 source and 3 target vertices are required.")

    meshFn = GetMeshFn(mesh)
    points = meshFn.getPoints(om.MSpace.kWorld)
    vertIt = GetVertexIterator(mesh)

    # ---------------------------------------------------------
    # Determine source / target side from vertsA
    # ---------------------------------------------------------

    avgXA = sum(points[v].x for v in vertsA) / 3.0
    sourceNegative = avgXA < 0

    sourceSide = set()
    targetSide = set()

    for vertexId, p in enumerate(points):
        if abs(p.x) <= tolerance:
            continue

        if sourceNegative:
            if p.x < 0:
                sourceSide.add(vertexId)
            else:
                targetSide.add(vertexId)
        else:
            if p.x > 0:
                sourceSide.add(vertexId)
            else:
                targetSide.add(vertexId)

    if not all(v in sourceSide for v in vertsA):
        raise ValueError("vertsA are not on the same source side.")

    if not all(v in targetSide for v in vertsB):
        raise ValueError("vertsB are not on the opposite target side.")

    # ---------------------------------------------------------
    # Build adjacency
    # ---------------------------------------------------------

    adjacency = {}
    degree = {}

    for vertexId in range(meshFn.numVertices):
        vertIt.setIndex(vertexId)
        neighbors = list(vertIt.getConnectedVertices())
        adjacency[vertexId] = neighbors
        degree[vertexId] = len(neighbors)

    # ---------------------------------------------------------
    # Initial mapping
    # ---------------------------------------------------------

    mapping = {}
    reverseMapping = {}

    for a, b in zip(vertsA, vertsB):
        mapping[a] = b
        reverseMapping[b] = a

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def MirrorDistance(sourceId, targetId):
        sp = points[sourceId]
        tp = points[targetId]

        dx = (-sp.x) - tp.x
        dy = sp.y - tp.y
        dz = sp.z - tp.z

        return dx * dx + dy * dy + dz * dz

    def CountMappedNeighborMatches(sourceId, targetId):
        score = 0
        targetNeighbors = set(adjacency[targetId])

        for sourceNeighbor in adjacency[sourceId]:
            if sourceNeighbor not in mapping:
                continue

            mappedTarget = mapping[sourceNeighbor]

            if mappedTarget in targetNeighbors:
                score += 1

        return score

    def GetCandidateScore(sourceId, targetId):
        # Topology degree should match
        degreeDiff = abs(degree[sourceId] - degree[targetId])

        # More already-mapped neighbor connections = much better
        mappedMatches = CountMappedNeighborMatches(sourceId, targetId)

        # Position only used as secondary guide
        mirrorDist = MirrorDistance(sourceId, targetId)

        return (
            degreeDiff * 1000000.0
            - mappedMatches * 10000.0
            + mirrorDist
        )

    def FindTargetNeighbor(sourceParent, targetParent, sourceNeighbor):
        candidates = []

        for targetNeighbor in adjacency[targetParent]:
            if targetNeighbor not in targetSide:
                continue

            if targetNeighbor in reverseMapping:
                continue

            # Prefer same vertex valence
            if degree[sourceNeighbor] != degree[targetNeighbor]:
                continue

            score = GetCandidateScore(sourceNeighbor, targetNeighbor)
            candidates.append((score, targetNeighbor))

        # If strict degree filtering found nothing,
        # allow degree mismatch as fallback
        if not candidates:
            for targetNeighbor in adjacency[targetParent]:
                if targetNeighbor not in targetSide:
                    continue

                if targetNeighbor in reverseMapping:
                    continue

                score = GetCandidateScore(sourceNeighbor, targetNeighbor)
                candidates.append((score, targetNeighbor))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0])

        return candidates[0][1]

    # ---------------------------------------------------------
    # Flood fill
    # ---------------------------------------------------------

    queue = list(vertsA)
    processed = set()

    while queue:
        sourceVertex = queue.pop(0)

        if sourceVertex in processed:
            continue

        if sourceVertex not in mapping:
            continue

        processed.add(sourceVertex)

        targetVertex = mapping[sourceVertex]

        for sourceNeighbor in adjacency[sourceVertex]:
            if sourceNeighbor not in sourceSide:
                continue

            if sourceNeighbor in mapping:
                continue

            targetNeighbor = FindTargetNeighbor(
                sourceVertex,
                targetVertex,
                sourceNeighbor
            )

            if targetNeighbor is None:
                continue

            mapping[sourceNeighbor] = targetNeighbor
            reverseMapping[targetNeighbor] = sourceNeighbor
            queue.append(sourceNeighbor)

    # ---------------------------------------------------------
    # Second pass
    #
    # Try unresolved verts again after more neighbors
    # have already been mapped.
    # ---------------------------------------------------------

    changed = True

    while changed:
        changed = False

        unresolved = [
            v for v in sourceSide
            if v not in mapping
        ]

        for sourceVertex in unresolved:
            mappedParents = [
                n for n in adjacency[sourceVertex]
                if n in mapping
            ]

            if not mappedParents:
                continue

            candidates = None

            # Target must connect to all mapped target neighbors
            for sourceParent in mappedParents:
                targetParent = mapping[sourceParent]

                validTargets = {
                    n for n in adjacency[targetParent]
                    if n in targetSide
                    and n not in reverseMapping
                }

                if candidates is None:
                    candidates = validTargets
                else:
                    candidates &= validTargets

            if not candidates:
                continue

            ranked = []

            for targetVertex in candidates:
                score = GetCandidateScore(
                    sourceVertex,
                    targetVertex
                )

                ranked.append(
                    (score, targetVertex)
                )

            if not ranked:
                continue

            ranked.sort(key=lambda item: item[0])
            targetVertex = ranked[0][1]

            mapping[sourceVertex] = targetVertex
            reverseMapping[targetVertex] = sourceVertex

            changed = True

    return [(a, mapping[a]) for a in sorted(mapping)]


def GetMeshSides(mesh, sourceVerts, tolerance=0.0001):
    meshFn = GetMeshFn(mesh)
    points = meshFn.getPoints(om.MSpace.kWorld)

    sourceAvgX = sum(points[v].x for v in sourceVerts) / float(len(sourceVerts))
    sourceNegative = sourceAvgX < 0

    sourceSide = set()
    targetSide = set()
    centerVerts = set()

    for vertexId, point in enumerate(points):
        if abs(point.x) <= tolerance:
            centerVerts.add(vertexId)
        elif sourceNegative:
            if point.x < 0:
                sourceSide.add(vertexId)
            else:
                targetSide.add(vertexId)
        else:
            if point.x > 0:
                sourceSide.add(vertexId)
            else:
                targetSide.add(vertexId)

    return sourceSide, targetSide, centerVerts

def GetVertexComponentIds(mesh, startVertex):
    vertIt = GetVertexIterator(mesh)
    result = set()
    stack = [startVertex]

    while stack:
        vertex = stack.pop()
        if vertex in result:
            continue

        result.add(vertex)
        vertIt.setIndex(vertex)

        for neighbor in vertIt.getConnectedVertices():
            if neighbor not in result:
                stack.append(neighbor)

    return result


def GetMirrorPairs(meshA, vertsA, meshB, vertsB):
    if len(vertsA) != 3 or len(vertsB) != 3:
        raise ValueError("Exactly 3 source and 3 target vertices are required.")

    # ---------------------------------------------------------
    # Same mesh
    # ---------------------------------------------------------

    if meshA == meshB:
        componentA = GetVertexComponentIds(meshA, vertsA[0])
        componentB = GetVertexComponentIds(meshB, vertsB[0])

        # Same connected component
        if componentA == componentB:
            return GetMirrorPairsSameComponent(
                meshA,
                vertsA,
                vertsB
            )

        # Different components inside same mesh
        return FindSymmetricVertexPairs(
            meshA,
            vertsA,
            vertsB
        )

    # ---------------------------------------------------------
    # Different meshes
    # ---------------------------------------------------------

    return MatchVertexPairs(
        meshA,
        meshB,
        vertsA,
        vertsB
    )


def MirrorMeshPosition(*arr):
    sel = cmds.ls(orderedSelection=True, fl=True)

    if len(sel) != 6:
        cmds.warning("Select exactly 6 vertices: 3 source then 3 target.")
        return

    if not all(".vtx[" in v for v in sel):
        cmds.warning("Selection must contain vertices only.")
        return

    sourceVerts = sel[:3]
    targetVerts = sel[3:]

    meshA = sourceVerts[0].split(".")[0]
    meshB = targetVerts[0].split(".")[0]

    if any(v.split(".")[0] != meshA for v in sourceVerts):
        cmds.warning("First 3 vertices must belong to the same mesh.")
        return

    if any(v.split(".")[0] != meshB for v in targetVerts):
        cmds.warning("Last 3 vertices must belong to the same mesh.")
        return

    sourceIds = [GetID(v) for v in sourceVerts]
    targetIds = [GetID(v) for v in targetVerts]

    # ---------------------------------------------------------
    # Build topology pairs
    # ---------------------------------------------------------

    pairs = GetMirrorPairs(
        meshA,
        sourceIds,
        meshB,
        targetIds
    )

    if not pairs:
        cmds.warning("No mirror pairs found.")
        return

    # ---------------------------------------------------------
    # Get source positions before modifying anything
    # ---------------------------------------------------------

    sourceFn = GetMeshFn(meshA)
    sourcePoints = sourceFn.getPoints(om.MSpace.kWorld)

    # ---------------------------------------------------------
    # Mirror all resolved pairs
    # ---------------------------------------------------------

    cmds.undoInfo(openChunk=True)

    try:
        for sourceId, targetId in pairs:
            p = sourcePoints[sourceId]

            cmds.xform(
                "{}.vtx[{}]".format(meshB, targetId),
                ws=True,
                t=(-p.x, p.y, p.z)
            )

    finally:
        cmds.undoInfo(closeChunk=True)

    print(
        "Mirror Position | {} -> {} | {} pairs".format(
            meshA,
            meshB,
            len(pairs)
        )
    )
