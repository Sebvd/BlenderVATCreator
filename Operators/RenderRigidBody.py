import bpy
import os
import json
import bmesh
from bpy.types import Operator
from bpy.utils import register_class, unregister_class
from mathutils import Vector
from math import ceil, floor
import numpy as np
from .VATFunctions import (
    FilterSelection,
    CompareBounds,
    CreateTexture,
    GetExtends,
    GetEvaluationFrame,
    ExportWithLODs,
    ConvertCoordinate,
    ConvertQuaternion
)


# Executing the rigid body VAT render
def RenderRigidBody(): 
    # Basic vars
    print("Collecting data")
    StartSelection = bpy.context.selected_objects
    SelectedObjects = FilterSelection(StartSelection)
    context = bpy.context
    properties = context.scene.VATExporter_RegularProperties

    FrameStart = context.scene.frame_start
    FrameEnd = context.scene.frame_end
    FrameSpacing = properties.FrameSpacing

    # Texture data
    ObjectCount = len(SelectedObjects)
    FrameCount = ceil((FrameEnd - FrameStart + 1) / FrameSpacing)
    TextureArraySize = ObjectCount * FrameCount
    PixelPositions = np.ones((TextureArraySize, 4))
    PixelNormals = np.ones((TextureArraySize, 4))
    PixelScales = np.ones((TextureArraySize, 4))

    PositionBounds = Vector((0.0, 0.0, 0.0))
    ScaleBounds = Vector((0.0, 0.0, 0.0))
    ExtendsMin = np.array([np.inf] * 3)
    ExtendsMax = np.array([np.inf * -1] * 3)
    CompareLocations, StartScales, StartRotations, StartExtendsMin, StartExtendsMax = PrepareSelectedObjects(SelectedObjects, GetEvaluationFrame())

    # Accumulate the VAT data
    for Frame in range(FrameStart, FrameEnd + 1):
        # Check if we should write data for this specific frame (if we don't it might break non-cached simulations)
        bpy.context.scene.frame_set(Frame)
        if((Frame - FrameStart) % FrameSpacing != 0):
            continue

        # Loop over the objects and get their position
        VerticalPixelIndex = floor((Frame - FrameStart) / FrameSpacing)
        for i, Object in enumerate(SelectedObjects):
            # Temp object
            DependencyGraph = context.view_layer.depsgraph
            CompareObject = Object.evaluated_get(DependencyGraph)

            # Frame data
            FrameLocation = ConvertCoordinate(CompareObject.matrix_world.translation) - CompareLocations[i]
            CurrentScale = ConvertCoordinate(CompareObject.matrix_world.to_scale(), FlipAxes = False)
            FrameScale = Vector([CurrentScale[j] / StartScales[i][j] for j in range(3)])
            CurrentRotation = CompareObject.matrix_world.to_quaternion()
            Rotation = ConvertQuaternion(CurrentRotation @ StartRotations[i].inverted())

            # Create the basic data arrays
            PixelIndex = VerticalPixelIndex * len(SelectedObjects)+ i
            PositionAlpha = 1.0
            if(properties.FileScaleTextureEnabled and properties.FileSingleChannelScaleEnabled):
                PositionAlpha = FrameScale[0]
            PixelPositions[PixelIndex] = (*FrameLocation, PositionAlpha)
            PixelNormals[PixelIndex] = Rotation
            PixelScales[PixelIndex] = (*FrameScale, 1.0)

            # Create the bounds data
            CompareBounds(PositionBounds, FrameLocation)
            CompareBounds(ScaleBounds, FrameScale)
            Corners = [Object.matrix_world @ Vector(Corner) for Corner in Object.bound_box]
            for Corner in Corners:
                ExtendsMin = np.minimum(ExtendsMin, Corner)
                ExtendsMax = np.maximum(ExtendsMax, Corner)
    
    # Convert data
    PositionBounds = [max((ceil(axis * 10000)/10000), 0.01) for axis in PositionBounds]
    ScaleBounds = [max((ceil(axis * 10000)/10000), 0.01) for axis in ScaleBounds]
    PixelPositions = NormalizePositions(PixelPositions, PositionBounds)
    PixelNormals = NormalizePositions(PixelNormals, Vector((1.0, 1.0, 1.0)))
    PixelScales = NormalizePositions(PixelScales, ScaleBounds)

    # Create exports
    if(properties.FileMeshEnabled):
        CreateVATMeshes(SelectedObjects, FrameStart, FrameCount, ObjectCount)
    if(properties.FilePositionTextureEnabled):
        CreateTexture(PixelPositions, ObjectCount, FrameCount, properties.FilePositionTexture, properties.FilePositionTextureFormat)
    if(properties.FileRotationTextureEnabled):
        CreateTexture(PixelNormals, ObjectCount, FrameCount, properties.FileRotationTexture, properties.FileRotationTextureFormat)
    if(properties.FileScaleTextureEnabled and (not properties.FileSingleChannelScaleEnabled)):
        CreateTexture(PixelScales, ObjectCount, FrameCount, properties.FileScaleTexture, properties.FileScaleTextureFormat)
    if(properties.FileJSONDataEnabled):
        OutputExtendsMin, OutputExtendsMax = GetExtends(ExtendsMin, ExtendsMax, StartExtendsMin, StartExtendsMax)
        CreateJSON(PositionBounds, ScaleBounds, OutputExtendsMin, OutputExtendsMax, properties, ObjectCount)

# Prepare the objects at the evaluation frame
def PrepareSelectedObjects(Objects : list[bpy.types.Object], EvaluationFrame : int, bShouldTransform : bool = True):
    context = bpy.context
    scene = context.scene
    StartExtendsMin = np.array([np.inf] * 3)
    StartExtendsMax = np.array([np.inf * -1] * 3)
    CompareLocations = []
    StartScales = []
    StartRotations = []

    for Object in Objects:
        # Create compare meshes
        scene.frame_set(EvaluationFrame)
        DependencyGraph = context.view_layer.depsgraph
        CompareObject = Object.evaluated_get(DependencyGraph)

        CompareMatrix = CompareObject.matrix_world.copy()
        CompareLocation = ConvertCoordinate(CompareMatrix.translation)
        CompareLocations.append(CompareLocation)
        StartScale = Vector((ConvertCoordinate(CompareObject.matrix_world.to_scale(), FlipAxes = False)))
        StartScales.append(StartScale)
        StartRotation = CompareMatrix.to_quaternion()
        StartRotations.append(StartRotation)

        # Return extends
        Corners = [Object.matrix_world @ Vector(Corner) for Corner in Object.bound_box]
        for Corner in Corners:
            StartExtendsMin = np.minimum(StartExtendsMin, ConvertCoordinate(Corner))
            StartExtendsMax = np.maximum(StartExtendsMax, ConvertCoordinate(Corner))
    
    return CompareLocations, StartScales, StartRotations, StartExtendsMin, StartExtendsMax

# Bring positions to a range from 0-1 based on the maximum calculated bounds
def NormalizePositions(Positions, Bounds):
    # Move positions into range
    NormalizedPositions = Positions / np.array((*Bounds, 1.0))
    NormalizedPositions += np.array((1,1,1,1))
    NormalizedPositions /= np.array((2,2,2,2))
    NormalizedPositions = np.clip(NormalizedPositions, 0, 1)

    return NormalizedPositions

# Create the JSON file for rigid body sims
def CreateJSON(PositionBounds, ScaleBounds, ExtendsMin, ExtendsMax, properties, ObjectCount):
    # Create the dict
    SimulationData = dict()
    SimulationData["FPS"] = bpy.context.scene.render.fps
    SimulationData["PositionBounds"] = PositionBounds
    SimulationData["ScaleBounds"] = ScaleBounds
    SimulationData["ExtendsMin"] = ExtendsMin.tolist()
    SimulationData["ExtendsMax"] = ExtendsMax.tolist()
    SimulationData["ObjectCount"] = ObjectCount
    SimulationData["PackedScale"] = (properties.FileScaleTextureEnabled and properties.FileSingleChannelScaleEnabled)

    # Export to JSON file
    TargetDirectory = bpy.path.abspath(properties.OutputDirectory)
    FileName = bpy.path.clean_name(properties.FileJSONData)
    TargetFile = os.path.join(TargetDirectory, FileName + ".json")
    with open(TargetFile, "w") as File:
        json.dump(SimulationData, File, indent = 2)

def CreateVATMeshes(Objects : list[bpy.types.Object], StartFrame, FrameCount, ObjectCount):
    scene = bpy.context.scene
    scene.frame_set(StartFrame)
    bpy.ops.Object.select_all(action = "DESELECT")
    NewObjects = []
    NewDatas = []
    for i, Object in enumerate(Objects):
        # Create a copy of the object
        NewObject = Object.copy()
        NewData = GetObjectAtFrame(Object, StartFrame, False)
        NewObject.data = NewData
        TransformMatrix = Object.matrix_world.copy()
        NewObject.data.transform(TransformMatrix)
        bpy.context.collection.objects.link(NewObject)

        # Create the UV data
        DistanceToTop = 1.0 / FrameCount * 0.5

        # Setting the UVs (sample texture UVs)
        bm = bmesh.new()
        bm.from_mesh(NewData)
        bmesh.ops.triangulate(bm, faces = bm.faces[:])
        bm.to_mesh(NewData)
        bm.free()
        PixelUVLayer = NewObject.data.uv_layers.new(name = "PixelUVs")
        OriginUVLayer1 = NewObject.data.uv_layers.new(name = "OriginUVs1")
        OriginUVLayer2 = NewObject.data.uv_layers.new(name = "OriginUVs2")
        Vertices = NewObject.data.vertices
        
        for Loop in NewObject.data.loops:
            PixelUVLayer.data[Loop.index].uv = (
                (i + 0.5) / ObjectCount,
                1.0 -  DistanceToTop
            )
            VertexLocation = ConvertCoordinate(Vertices[Loop.vertex_index].co - Object.matrix_world.translation)
            OriginUVLayer1.data[Loop.index].uv = (
                VertexLocation[0],
                1.0
            )
            OriginUVLayer2.data[Loop.index].uv = (
                VertexLocation[1],
                1.0 - VertexLocation[2]
            )
        
        NewObject.data.transform(TransformMatrix.inverted())
        NewObjects.append(NewObject)
        NewDatas.append(NewData)
    
    ExportWithLODs(NewObjects)

    # Remove the objects and meshes after we were done with them
    for NewObject, NewData in zip(NewObjects, NewDatas):
        bpy.data.objects.remove(NewObject)
        bpy.data.meshes.remove(NewData)
        pass

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
    # Check file name for scale texture
    FileScaleTexture = bpy.path.clean_name(properties.FileScaleTexture)
    FileScaleTextureEnabled = properties.FileScaleTextureEnabled
    if(FileScaleTexture == "" and FileScaleTextureEnabled):
        Warning = "Incorrect scale texture name"
        return False, Warning

    return True, ""

class VATEXPORTER_OT_RenderRigidBody(Operator):
    bl_idname = "vatexporter.renderrigidbody"
    bl_label = "Render rigidbody sim to VAT"
    bl_options = {"REGISTER"}

    # Check if the function can be ran
    @classmethod
    def poll(cls, context):
        # Check based on object selection
        bHasActiveObject = context.active_object != None
        bIsObjectMode = context.mode == "OBJECT"

        # Check based on user settings
        properties = context.scene.VATExporter_RegularProperties
        bIsExporting = properties.FileMeshEnabled or properties.FileJSONDataEnabled or properties.FilePositionTextureEnabled or properties.FileRotationTextureEnabled or properties.FileScaleTextureEnabled

        # Return poll
        return bHasActiveObject and bIsObjectMode and bIsExporting
    
    # Run the function
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
        RenderRigidBody()
        return {"FINISHED"}

def register():
    register_class(VATEXPORTER_OT_RenderRigidBody)

def unregister():
    unregister_class(VATEXPORTER_OT_RenderRigidBody)