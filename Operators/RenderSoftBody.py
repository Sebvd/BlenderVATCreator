import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class
from math import ceil, floor
from mathutils import Vector
import numpy as np
import os
import json
from importlib import reload
from .VATFunctions import (
    CreateTexture,
    FilterSelection, 
    CompareBounds, 
    UnsignVector, 
    ExportWithLODs, 
    GetExtends,
    ConvertCoordinate,
    GetEvaluationFrame
)



# Softbody calculation
def RenderSoftbodyVAT():
    # Main starting data
    StartSelection = bpy.context.selected_objects
    SelectedObjects = FilterSelection(StartSelection)
    context = bpy.context
    properties = context.scene.VATExporter_RegularProperties
    bCaughtVATError = False

    FrameStart = context.scene.frame_start
    FrameEnd = context.scene.frame_end
    FrameSpacing = properties.FrameSpacing

    # Prepare selected objects
    EvaluationFrame = GetEvaluationFrame()
    EdgeSplitModifiers, VertexCount, StartVertices, CompareMeshes, StartExtendsMin, StartExtendsMax = PrepareSelectedObjects(SelectedObjects, EvaluationFrame)
    FrameCount = min(ceil((FrameEnd - FrameStart + 1) / FrameSpacing), properties.ExportResolutionV)
    VertexCount = min(VertexCount, properties.ExportResolutionU)
    
    # Initialize export data
    TextureArraySize = VertexCount * FrameCount
    PixelPositions = np.ones((TextureArraySize, 4))
    PixelNormals = np.ones((TextureArraySize, 4))
    Bounds = Vector((0.0, 0.0, 0.0))
    ExtendsMin = np.array([np.inf] * 3)
    ExtendsMax = np.array([np.inf * -1] * 3)

    # Start VAT process
    PrevFrameVertexCount = 0
    for Frame in range(FrameStart, FrameEnd + 1):
        # Check if we should write data for this specific frame (if we don't it might break non-cached simulations)
        if((Frame - FrameStart) % FrameSpacing != 0):
            bpy.context.scene.frame_set(Frame)
            continue

        # Check if we are exceeding the maximum number of frames
        VerticalPixelIndex = floor((Frame - FrameStart) / FrameSpacing)
        if(VerticalPixelIndex >= FrameCount):
            break

        # Start writing to frame
        FrameArrayPosition = VerticalPixelIndex * VertexCount
        FrameVertexCount = 0
        for SelectedObject in SelectedObjects:   
            # Get data from the frame
            FramePositions, FrameNormals, FrameBounds, bCaughtVATError = GetObjectDataAtFrame(
                SelectedObject, Frame, StartVertices, FrameVertexCount, ExtendsMin, ExtendsMax)
            ObjectVertexCount = len(FramePositions)

            # Insert data into array
            RestSpace = min(ObjectVertexCount, max(0, VertexCount - FrameVertexCount))
            FramePositions = np.resize(FramePositions, (RestSpace, 4))
            FrameNormals = np.resize(FrameNormals, (RestSpace, 4))
            InsertLocationStart = FrameArrayPosition + FrameVertexCount
            InsertLocationEnd = InsertLocationStart + RestSpace
            PixelPositions[InsertLocationStart:InsertLocationEnd, :] = FramePositions
            PixelNormals[InsertLocationStart:InsertLocationEnd, :] = FrameNormals

            # Update bounds
            CompareBounds(Bounds, FrameBounds)

            # Update local array position
            FrameVertexCount += ObjectVertexCount
            if(FrameVertexCount > VertexCount):
                break
        
        # Check if the vertex count decreases this frame
        if(Frame != FrameStart and FrameVertexCount != PrevFrameVertexCount):
            bCaughtVATError = True
        PrevFrameVertexCount = FrameVertexCount

        # Loop out of the frame loop if we encounter an error with the VAT objects
        if(bCaughtVATError):
            break

    # Error out if the loop encountered irregular polycounts
    if(bCaughtVATError):
        RemoveEdgeSplit(SelectedObjects, EdgeSplitModifiers)
        return True, "The polycount is changing per frame, which is not allowed with VATs. Check your modifiers."

    # Get the correct position data normalized for pixels and get the bounds
    PixelPositions, Bounds = NormalizePositions(PixelPositions, Bounds)
    OutputExtendsMin, OutputExtendsMax = GetExtends(ExtendsMin, ExtendsMax, StartExtendsMin, StartExtendsMax)

    # Create the export data
    CreateVATMeshes(SelectedObjects, VertexCount, FrameCount, FrameStart)
    if(properties.FilePositionTextureEnabled):
        CreateTexture(PixelPositions, VertexCount, FrameCount, properties.FilePositionTexture, properties.FilePositionTextureFormat)
    if(properties.FileRotationTextureEnabled):
        CreateTexture(PixelNormals, VertexCount, FrameCount, properties.FileRotationTexture, properties.FileRotationTextureFormat)
    if(properties.FileJSONDataEnabled):
        CreateJSON(Bounds, OutputExtendsMin, OutputExtendsMax, properties, VertexCount)

    # Reset selected objects to their original state
    for CompareMesh in CompareMeshes:
        bpy.data.meshes.remove(CompareMesh)

    RemoveEdgeSplit(SelectedObjects, EdgeSplitModifiers)
    bpy.context.scene.frame_set(FrameStart)
    for Object in StartSelection:
        Object.select_set(True)

    # Return
    return False, ""

# Assign edge split modifier
def PrepareSelectedObjects(Objects : list[bpy.types.Object], EvaluationFrame : int):
    # Get the object data from the evaluation frame
    VertexCount = 0
    EdgeSplitModifiers = []
    Vertices = []
    CompareMeshes = []
    StartExtendsMin = np.array([np.inf] * 3)
    StartExtendsMax = np.array([np.inf * -1] * 3)
    for Object in Objects:
        # Assign an edge split modifier is the toggle for sharp edges has been enabled
        EdgeSplitModifier = Object.modifiers.new("EdgeSplit", "EDGE_SPLIT")
        EdgeSplitModifier.use_edge_angle = False
        EdgeSplitModifier.use_edge_sharp = True
        EdgeSplitModifiers.append(EdgeSplitModifier)

        # Calculate vertex data
        CompareMesh = GetObjectAtFrame(Object, EvaluationFrame)
        Vertices += CompareMesh.vertices
        
        VertexCount += len(CompareMesh.vertices)
        CompareMeshes.append(CompareMesh)

        # Calculate start extends
        for Vertex in CompareMesh.vertices:
            ConvertedCoord = Vector((Vertex.co[0], -1 * Vertex.co[1], Vertex.co[2]))
            np.minimum(StartExtendsMin, ConvertedCoord, StartExtendsMin)
            np.maximum(StartExtendsMax, ConvertedCoord, StartExtendsMax)

    # Clean up and return
    return EdgeSplitModifiers, VertexCount, Vertices, CompareMeshes, StartExtendsMin, StartExtendsMax

# Remove the edge split modifier we just added
def RemoveEdgeSplit(Objects : list[bpy.types.Object], EdgeSplitModifiers):
    for i, Object in enumerate(Objects):
        Object.modifiers.remove(EdgeSplitModifiers[i])

# Get the object data at a certain frame
def GetObjectAtFrame(Object : bpy.types.Object, Frame, bShouldTransform : bool = True):
    # Base variables
    context = bpy.context
    scene = context.scene
    scene.frame_set(Frame)

    # Creating a new measure object at the current frame
    DependencyGraph = context.view_layer.depsgraph
    CompareObject = Object.evaluated_get(DependencyGraph)
    TemporaryObject = bpy.data.meshes.new_from_object(CompareObject)
    if(bShouldTransform):
        TemporaryObject.transform(Object.matrix_world)

    # Return
    return TemporaryObject

# Get positions (as offsets) and normals from the given object at the given frame for all its vertices
def GetObjectDataAtFrame(Object : bpy.types.Object, Frame, CompareVertices, TotalVertexCount, ExtendsMin, ExtendsMax):
    # Get object data
    CompareMesh = GetObjectAtFrame(Object, Frame)
    Vertices = CompareMesh.vertices
    Positions = np.ones((len(Vertices), 4))
    Normals = np.ones((len(Vertices), 4))
    Bounds = Vector((0.0, 0.0, 0.0))

    # Check if the polycount increases this frame
    if(TotalVertexCount + len(Vertices) > len(CompareVertices)):
        return Positions, Normals, Bounds, True

    # Create vertex offsets and normals data
    for Vertex in Vertices:
        # Position calculation
        CompareVertex = CompareVertices[TotalVertexCount + Vertex.index].co
        Offset = ConvertCoordinate(Vertex.co - CompareVertex)
        ConvertedOffset = (*Offset, 1.0)
        Positions[Vertex.index] = ConvertedOffset

        # Create new bounds & extents
        CompareBounds(Bounds, ConvertedOffset)
        np.minimum(Vertex.co[:], ExtendsMin, ExtendsMin)
        np.maximum(Vertex.co[:], ExtendsMax, ExtendsMax)

        # Normal calculation
        VertexNormal = ConvertCoordinate(Vertex.normal.copy())
        ConvertedNormal = UnsignVector(Vector((VertexNormal[0], VertexNormal[1], VertexNormal[2])))
        Normals[Vertex.index] = (*ConvertedNormal, 1.0)

    bpy.data.meshes.remove(CompareMesh)
    return Positions, Normals, Bounds, False

# Bring positions to a range from 0-1 based on the maximum calculated bounds
def NormalizePositions(Positions, Bounds):
    # Set the bounds to a minimum of 0.01 to prevent divisions by 0 in the shader
    MeasureBounds = [max((ceil(axis * 10000)/10000), 0.01) for axis in Bounds]

    # Move positions into range
    NormalizedPositions = Positions / np.array((*MeasureBounds, 1.0))
    NormalizedPositions += np.array((1,1,1,0))
    NormalizedPositions /= np.array((2,2,2,1))
    NormalizedPositions = np.clip(NormalizedPositions, 0, 1)

    return NormalizedPositions, MeasureBounds

# Create VAT mesh andd export it
def CreateVATMeshes(Objects : list[bpy.types.Object], VertexCount, FrameCount, StartFrame):
    scene = bpy.context.scene
    scene.frame_set(StartFrame)
    LocalVertexCount = 0
    bpy.ops.object.select_all(action = "DESELECT")
    NewObjects = []
    NewDatas = []
    for Object in Objects:
        # Create a copy
        NewObject = Object.copy()
        NewData = GetObjectAtFrame(Object, StartFrame, False)
        NewObject.data = NewData

        # Apply the modifiers for each object (e.g., subsurf modifer can cause UV issues)
        Modifiers = NewObject.modifiers
        bpy.context.collection.objects.link(NewObject)
        for Modifier in Modifiers:
            bpy.context.view_layer.objects.active = NewObject
            bpy.ops.object.modifier_apply(modifier = Modifier.name)
        bpy.context.collection.objects.unlink(NewObject)

        # UV data
        DistanceToTop = 1.0 / FrameCount * 0.5 # Make sure that the UV is exactly in the middle of the pixel in the v axis

        # Setting the UVs
        PixelUVLayer = NewObject.data.uv_layers.new(name = "PixelUVs")
        for Loop in NewObject.data.loops:
            PixelUVLayer.data[Loop.index].uv = (
                min((Loop.vertex_index + LocalVertexCount + 0.5), VertexCount - 0.5) / VertexCount, 
                1.0 - DistanceToTop
            )

        # Link the object to the scene
        bpy.context.collection.objects.link(NewObject)
        NewObject.select_set(True)

        NewObjects.append(NewObject)
        NewDatas.append(NewData)

        LocalVertexCount += len(NewObject.data.vertices)

    # Export the meshes
    ExportWithLODs(NewObjects)

    # Clean up
    for i, NewObject in enumerate(NewObjects):
        
        bpy.data.objects.remove(NewObject)
        bpy.data.meshes.remove(NewDatas[i])

# Creates the JSON file containing the VAT data
def CreateJSON(Bounds, ExtendsMin, ExtendsMax, properties, VertexCount):
    # Create JSON dict
    SimulationData = dict()
    SimulationData["FPS"] = bpy.context.scene.render.fps
    SimulationData["Bounds"] = Bounds
    SimulationData["ExtendsMin"] = ExtendsMin.tolist()
    SimulationData["ExtendsMax"] = ExtendsMax.tolist()
    SimulationData["VertexCount"] = VertexCount

    # Export the JSPON
    TargetDirectory = bpy.path.abspath(properties.OutputDirectory)
    FileName = bpy.path.clean_name(properties.FileJSONData)
    TargetFile = os.path.join(TargetDirectory, FileName + ".json")
    with open(TargetFile, "w") as File:
        json.dump(SimulationData, File, indent = 2)

# Check if the export data is valid
def IsDefaultExportValid():
    # Get properties
    properties = bpy.context.scene.VATExporter_RegularProperties
    
    # Check directory
    BaseDirectory = bpy.path.abspath(properties.OutputDirectory)
    if(os.path.isdir(BaseDirectory) == False):
        Warning = "Target directory is not valid"
        return False, Warning
    
    # Check file for meshes
    FileMeshName = bpy.path.clean_name(properties.FileMeshName)
    FileMeshEnabled = properties.FileMeshEnabled
    if(FileMeshName == "" and FileMeshEnabled):
        Warning = "Incorrect mesh name"
        return False, Warning
    # Check file name for JSON file
    FileJSONData = bpy.path.clean_name(properties.FileJSONData)
    FileJSONDataEnabled = properties.FileJSONDataEnabled
    if(FileJSONData == "" and FileJSONDataEnabled):
        Warning = "Incorrect JSON file name"
        return False, Warning
    # Check file name for position texture
    FilePositionTexture = bpy.path.clean_name(properties.FilePositionTexture)
    FilePositionTextureEnabled = properties.FilePositionTextureEnabled
    if(FilePositionTexture == "" and FilePositionTextureEnabled):
        Warning = "Incorrect position texture name"
        return False, Warning
    # Check file name for rotation texture
    FileRotationTexture = bpy.path.clean_name(properties.FileRotationTexture)
    FileRotationTextureEnabled = properties.FileRotationTextureEnabled
    if(FileRotationTexture == "" and FileRotationTextureEnabled):
        Warning = "Incorrect rotation texture name"
        return False, Warning

    return True, ""

# Main function to render softbody
class VATEXPORTER_OT_RenderSoftBody(Operator):
    bl_idname = "vatexporter.rendersoftbody"
    bl_label = "Render softbody to VAT"
    bl_options = {"REGISTER"}

    # Check if the function can be ran
    @classmethod
    def poll(cls, context):
        # Check based on object selection
        bHasActiveObject = context.active_object != None
        bIsObjectMode = context.mode == "OBJECT"

        # Check based on user settings
        properties = context.scene.VATExporter_RegularProperties
        bIsExporting = properties.FileMeshEnabled or properties.FileJSONDataEnabled or properties.FilePositionTextureEnabled or properties.FileRotationTextureEnabled

        # Return poll
        return bHasActiveObject and bIsObjectMode and bIsExporting
    
    # run the function
    def execute(self, context):
        # Check if we can export. If not, cancel the operation
        bIsExportValid, Warning = IsDefaultExportValid()
        if(bIsExportValid == False):
            self.report({"WARNING"}, Warning)
            return {"CANCELLED"}
        # Check if we can export based on viewport selection
        if(not bpy.context.selected_objects):
            self.report({"WARNING"}, "Nothing is selected")
            return {"CANCELLED"}

        bVATError, VATErrorDescription = RenderSoftbodyVAT()
        if(bVATError):
            self.report({"ERROR"}, VATErrorDescription)
            return {"CANCELLED"}
        
        return {"FINISHED"}

modules = [VATEXPORTER_OT_RenderSoftBody]

def register():
    for module in modules:
        register_class(module)

def unregister():
    for module in modules:
        unregister_class(module)

if __name__ == "__main__":
    register()