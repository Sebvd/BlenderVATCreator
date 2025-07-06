import bpy
from bpy.types import Operator, Panel
from bpy.utils import register_class, unregister_class
from math import ceil, floor
from mathutils import Vector
import numpy as np
import os
import json
from .VATFunctions import (
    CreateTexture,
    FilterSelection, 
    CompareBounds, 
    UnsignVector, 
    ExportWithLODs, 
    GetExtends
)

# Check if the export data is valid
def IsExportValid():
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

# Softbody calculation
def RenderSoftbodyVAT():
    # Main data & start data
    StartSelection = bpy.context.selected_objects
    SelectedObjects = FilterSelection(StartSelection)
    context = bpy.context
    StartFrame = context.scene.frame_current
    properties = context.scene.VATExporter_RegularProperties

    # Declare main variables
    FrameStart = 1
    FrameEnd = 80
    FrameSpacing = 1

    # Prepare selected objects
    EdgeSplitModifiers, VertexCount, StartVertices, CompareMeshes, StartExtendsMin, StartExtendsMax = PrepareSelectedObjects(SelectedObjects, 1)
    FrameCount = ceil((FrameEnd - FrameStart + 1) / FrameSpacing)
    
    # Initialize export data
    PixelPositions = np.ones((VertexCount * FrameCount, 4))
    PixelNormals = np.ones((VertexCount * FrameCount, 4))
    Bounds = Vector((0.0, 0.0, 0.0)) # Used to normalize the position
    ExtendsMin = np.array([np.inf] * 3) # Used to set the correct bounding box information on the mesh in Unreal
    ExtendsMax = np.array([np.inf * -1] * 3)

    # Start VAT process
    for Frame in range(FrameStart, FrameEnd + 1, FrameSpacing):
        LocalArrayPosition = 0
        FrameArrayPosition = floor((Frame - FrameStart) / FrameSpacing) * VertexCount
        TotalVertexCount = 0
        for SelectedObject in SelectedObjects:   
            # Get data from the frame
            FramePositions, FrameNormals, FrameBounds = GetObjectDataAtFrame(
                SelectedObject, Frame, StartVertices, TotalVertexCount, ExtendsMin, ExtendsMax)
            ObjectVertexCount = len(FramePositions)
            TotalVertexCount += ObjectVertexCount

            # Insert data into array
            InsertLocation = FrameArrayPosition + LocalArrayPosition
            PixelPositions[InsertLocation:(InsertLocation + ObjectVertexCount), :] = FramePositions
            PixelNormals[InsertLocation:(InsertLocation + ObjectVertexCount), :] = FrameNormals

            # Update bounds
            CompareBounds(Bounds, FrameBounds)

            # Update local array position
            LocalArrayPosition += ObjectVertexCount
            
    # Get the correct position data normalized for pixels and get the bounds
    PixelPositions, Bounds = NormalizePositions(PixelPositions, Bounds)
    OutputExtendsMin, OutputExtendsMax = GetExtends(ExtendsMin, ExtendsMax, StartExtendsMin, StartExtendsMax)

    # Create the export data
    CreateVATMeshes(SelectedObjects, VertexCount, FrameCount, StartFrame)
    if(properties.FilePositionTextureEnabled):
        CreateTexture(PixelPositions, VertexCount, FrameCount, properties.FilePositionTexture, properties.FilePositionTextureFormat)
    if(properties.FileRotationTextureEnabled):
        CreateTexture(PixelNormals, VertexCount, FrameCount, properties.FileRotationTexture, properties.FileRotationTextureFormat)
    if(properties.FileJSONDataEnabled):
        CreateJSON(Bounds, OutputExtendsMin, OutputExtendsMax, properties)

    # Reset selected objects to their original state
    for CompareMesh in CompareMeshes:
        bpy.data.meshes.remove(CompareMesh)

    RemoveEdgeSplit(SelectedObjects, EdgeSplitModifiers)
    bpy.context.scene.frame_set(StartFrame)
    for Object in StartSelection:
        Object.select_set(True)

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
def GetObjectAtFrame(Object : bpy.types.Object, Frame):
    # Base variables
    context = bpy.context
    scene = context.scene
    scene.frame_set(Frame)

    # Creating a new measure object at the current frame
    DependencyGraph = context.view_layer.depsgraph
    CompareObject = Object.evaluated_get(DependencyGraph)
    TemporaryObject = bpy.data.meshes.new_from_object(CompareObject)
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

    # Create vertex offsets and normals data
    for Vertex in Vertices:
        # Position calculation
        CompareVertex = CompareVertices[TotalVertexCount + Vertex.index].co
        Offset = Vertex.co - CompareVertex
        ConvertedOffset = (Offset[0], -1 * Offset[1], Offset[2], 1.0)
        Positions[Vertex.index] = ConvertedOffset

        # Create new bounds & extents
        CompareBounds(Bounds, ConvertedOffset)
        np.minimum(Vertex.co[:], ExtendsMin, ExtendsMin)
        np.maximum(Vertex.co[:], ExtendsMax, ExtendsMax)

        # Normal calculation
        VertexNormal = Vertex.normal.copy()
        ConvertedNormal = UnsignVector(Vector((VertexNormal[0], -1 * VertexNormal[1], VertexNormal[2])))
        Normals[Vertex.index] = (ConvertedNormal[0], ConvertedNormal[1], ConvertedNormal[2], 1.0)

    bpy.data.meshes.remove(CompareMesh)
    return Positions, Normals, Bounds

# Bring positions to a range from 0-1 based on the maximum calculated bounds
def NormalizePositions(Positions, Bounds):
    # Set the bounds to a minimum of 0.01 to prevent divisions by 0 in the shader
    MeasureBounds = [max((ceil(axis * 10000)/10000), 0.01) for axis in Bounds]

    # Move positions into range
    NormalizedPositions = Positions / np.array((MeasureBounds[0], MeasureBounds[1], MeasureBounds[2], 1.0))
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
        NewData = GetObjectAtFrame(Object, StartFrame)
        #NewData = Object.data.copy()
        NewObject.data = NewData
        
        # UV data
        DistanceToTop = 1.0 / FrameCount * 0.5 # Make sure that the UV is exactly in the middle of the pixel in the v axis

        # Setting the UVs
        PixelUVLayer = NewObject.data.uv_layers.new(name = "PixelUVs")
        for Loop in NewObject.data.loops:
            PixelUVLayer.data[Loop.index].uv = ((Loop.vertex_index + LocalVertexCount + 0.5) / VertexCount, 1.0 - DistanceToTop)

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
def CreateJSON(Bounds, ExtendsMin, ExtendsMax, properties):
    # Create JSON dict
    SimulationData = dict()
    SimulationData["FPS"] = bpy.context.scene.render.fps
    SimulationData["Bounds"] = Bounds
    SimulationData["ExtendsMin"] = ExtendsMin.tolist()
    SimulationData["ExtendsMax"] = ExtendsMax.tolist()

    # Export the JSPON
    TargetDirectory = bpy.path.abspath(properties.OutputDirectory)
    FileName = bpy.path.clean_name(properties.FileJSONData)
    TargetFile = os.path.join(TargetDirectory, FileName + ".json")
    with open(TargetFile, "w") as File:
        json.dump(SimulationData, File, indent = 2)

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
        bIsExportValid, Warning = IsExportValid()
        if(bIsExportValid == False):
            self.report({"WARNING"}, Warning)
            return {"CANCELLED"}
        # Check if we can export based on viewport selection
        if(not bpy.context.selected_objects):
            self.report({"WARNING"}, "Nothing is selected")
            return {"CANCELLED"}

        RenderSoftbodyVAT()
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