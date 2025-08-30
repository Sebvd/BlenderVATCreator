import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class
from .VATFunctions import (
    FilterSelection,
    CompareBounds,
    CreateTexture,
    GetExtends,
    GetEvaluationFrame
)
import os
from mathutils import Vector, Matrix
from math import ceil, floor
import numpy as np

# Executing the rigid body VAT render
def RenderRigidBody(): 
    # Basic vars
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
    CompareLocations, StartExtendsMin, StartExtendsMax = PrepareSelectedObjects(SelectedObjects, GetEvaluationFrame())

    # Accumulate the VAT data
    for Frame in range(FrameStart, FrameEnd + 1):
        # Check if we should write data for this specific frame (if we don't it might break non-cached simulations)
        bpy.context.scene.frame_set(Frame)
        if((Frame - FrameStart) % FrameSpacing != 0):
            continue

        # Loop over the objects and get their position
        VerticalPixelIndex = floor((Frame - FrameStart) / FrameSpacing)
        for i, Object in enumerate(SelectedObjects):
            # Frame data
            ObjectLocation = Object.matrix_world.translation
            FrameLocation = ObjectLocation - CompareLocations[i]

            # Create the basic data arrays
            PixelIndex = VerticalPixelIndex + i
            PixelPositions[PixelIndex] = (*FrameLocation, 1.0) 
            PixelNormals[PixelIndex] = Object.rotation_euler.to_quaternion()
            PixelScales[PixelIndex] = (*Object.scale, 1.0)

            # Create the bounds data
            CompareBounds(PositionBounds, FrameLocation)
            CompareBounds(ScaleBounds, Object.scale)
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

    print(PositionBounds)

    # Create exports
    if(properties.FilePositionTextureEnabled):
        CreateTexture(PixelPositions, ObjectCount, FrameCount, properties.FilePositionTexture, properties.FilePositionTextureFormat)
    if(properties.FileRotationTextureEnabled):
        CreateTexture(PixelNormals, ObjectCount, FrameCount, properties.FileRotationTexture, properties.FileRotationTextureFormat)
    if(properties.FileScaleTextureEnabled and (not properties.FileSingleChannelScaleEnabled)):
        CreateTexture(PixelScales, ObjectCount, FrameCount, properties.FileScaleTexture, properties.FileScaleTextureFormat)
    if(properties.FileJSONDataEnabled):
        OutputExtendsMin, OutputExtendsMax = GetExtends(ExtendsMin, ExtendsMax, StartExtendsMin, StartExtendsMax)
        print(f"OutputExtendsMin: {OutputExtendsMin}")
        print(f"OutputExtendsMax: {OutputExtendsMax}")
        #CreateJSON(PositionBounds, ScaleBounds, OutputExtendsMin, OutputExtendsMax, properties, ObjectCount)
        pass

    print("Rendering rigid body")

# Prepare the objects at the evaluation frame
def PrepareSelectedObjects(Objects : list[bpy.types.Object], EvaluationFrame : int, bShouldTransform : bool = True):
    context = bpy.context
    scene = context.scene
    
    StartExtendsMin = np.array([np.inf] * 3)
    StartExtendsMax = np.array([np.inf * -1] * 3)
    CompareLocations = []
    for Object in Objects:
        # Create compare meshes
        scene.frame_set(EvaluationFrame)
        DependencyGraph = context.view_layer.depsgraph
        CompareObject = Object.evaluated_get(DependencyGraph)
        CompareLocation = CompareObject.matrix_world.translation.copy()
        CompareLocations.append(CompareLocation)

        # Return extends
        Corners = [Object.matrix_world @ Vector(Corner) for Corner in Object.bound_box]
        for Corner in Corners:
            StartExtendsMin = np.minimum(StartExtendsMin, Corner)
            StartExtendsMax = np.maximum(StartExtendsMax, Corner)
    
    return CompareLocations, StartExtendsMin, StartExtendsMax

# Bring positions to a range from 0-1 based on the maximum calculated bounds
def NormalizePositions(Positions, Bounds):
    # Move positions into range
    NormalizedPositions = Positions / np.array((*Bounds, 1.0))
    NormalizedPositions += np.array((1,1,1,1))
    NormalizedPositions /= np.array((2,2,2,2))
    NormalizedPositions = np.clip(NormalizedPositions, 0, 1)

    return NormalizedPositions

# Calculate the extends (for currect object culling after the vertex displacements in the target engine)
def CalculateExtends():
    pass

# Create the JSON file for rigid body sims
def CreateJSON(PositionBounds, ScaleBounds, ExtendsMin, ExtendsMax, properties, ObjectCount):
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