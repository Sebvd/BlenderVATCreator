import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class
from .VATFunctions import (
    FilterSelection,
    CompareBounds,
    CreateTexture
)
import os
from mathutils import Vector
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

    # Accumulate the VAT data
    for Frame in range(FrameStart, FrameEnd + 1):
        # Check if we should write data for this specific frame (if we don't it might break non-cached simulations)
        bpy.context.scene.frame_set(Frame)
        if((Frame - FrameStart) % FrameSpacing != 0):
            continue

        # Loop over the objects and get their position
        VerticalPixelIndex = floor((Frame - FrameStart) / FrameSpacing)
        for i, Object in enumerate(SelectedObjects):
            # Create the basic data arrays
            PixelIndex = VerticalPixelIndex + i
            PixelPositions[PixelIndex] = (*Object.location, 1.0)
            PixelNormals[PixelIndex] = Object.rotation_euler.to_quaternion()
            PixelScales[PixelIndex] = (*Object.scale, 1.0)

            # Create the bounds data
            CompareBounds(PositionBounds, Object.location)
            CompareBounds(ScaleBounds, Object.scale)
    
    # Convert data
    PositionBounds = [max((ceil(axis * 10000)/10000), 0.01) for axis in PositionBounds]
    ScaleBounds = [max((ceil(axis * 10000)/10000), 0.01) for axis in ScaleBounds]
    PixelPositions = NormalizePositions(PixelPositions, PositionBounds)
    PixelNormals = NormalizePositions(PixelNormals, Vector((1.0, 1.0, 1.0)))
    PixelScales = NormalizePositions(PixelScales, ScaleBounds)

    # Create exports
    if(properties.FilePositionTextureEnabled):
        CreateTexture(PixelPositions, ObjectCount, FrameCount, properties.FilePositionTexture, properties.FilePositionTextureFormat)
    if(properties.FileRotationTextureEnabled):
        CreateTexture(PixelNormals, ObjectCount, FrameCount, properties.FileRotationTexture, properties.FileRotationTextureFormat)
    if(properties.FileScaleTextureEnabled and (not properties.FileSingleChannelScaleEnabled)):
        CreateTexture(PixelScales, ObjectCount, FrameCount, properties.FileScaleTexture, properties.FileScaleTextureFormat)

    print("Rendering rigid body")

# Bring positions to a range from 0-1 based on the maximum calculated bounds
def NormalizePositions(Positions, Bounds):
    # Move positions into range
    NormalizedPositions = Positions / np.array((*Bounds, 1.0))
    NormalizedPositions += np.array((1,1,1,0))
    NormalizedPositions /= np.array((2,2,2,1))
    NormalizedPositions = np.clip(NormalizedPositions, 0, 1)

    return NormalizedPositions

# Create the JSON file for rigid body sims
def CreateJSON():
    pass

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