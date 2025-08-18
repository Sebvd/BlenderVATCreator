# This files consists of functions that are reused across the different VAT modes

import bpy
from mathutils import Vector
import numpy as np
import os


# Filter objects so only to return objects of type mesh
def FilterSelection(Objects : list[bpy.types.Object]) -> list[bpy.types.Object]:
    FilteredObjects = []
    for Object in Objects:
        if(Object.type == "MESH"):
            FilteredObjects.append(Object)

    return FilteredObjects

# Returns the larges absolute bounds information to be sent to Unreal Engine
def CompareBounds(CurrentBounds, CompareBounds):
    for i in range(3):
        if(abs(CompareBounds[i]) > CurrentBounds[i]):
            CurrentBounds[i] = abs(CompareBounds[i])

# Convert the given vector to the correct coordinate system
def ConvertCoordinate(Coordinate) -> Vector:
    properties = bpy.context.scene.VATExporter_RegularProperties
    NewCoordinate = Coordinate
    # Flip coordinates based on input
    if(properties.FlipX):
        NewCoordinate *= Vector((-1.0, 1.0, 1.0))
    if(properties.FlipY):
        NewCoordinate *= Vector((1.0, -1.0, 1.0))
    if(properties.FlipZ):
        NewCoordinate *= Vector((1.0, 1.0, -1.0))

    # Rearrange coordinate channels
    CoordinateSystem = properties.CoordinateSystem
    match CoordinateSystem:
        case "xzy":
            NewCoordinate = Vector((NewCoordinate[0], NewCoordinate[2], NewCoordinate[1]))
        case "yxz":
            NewCoordinate = Vector((NewCoordinate[1], NewCoordinate[0], NewCoordinate[2]))
        case "yzx":
            NewCoordinate = Vector((NewCoordinate[1], NewCoordinate[2], NewCoordinate[0]))
        case "zxy":
            NewCoordinate = Vector((NewCoordinate[2], NewCoordinate[0], NewCoordinate[1]))
        case "zyx":
            NewCoordinate = Vector((NewCoordinate[2], NewCoordinate[1], NewCoordinate[0]))

    return NewCoordinate

# Moves a normalized vector from range (-1,1) to range (0,1)
def UnsignVector(InputVector) -> Vector:
    InputVector += Vector((1.0, 1.0, 1.0))
    InputVector /= 2.0
    InputVector = np.clip(InputVector, 0, 1)
    return InputVector

# Get the extends for the correct bounds information in Unreal
def GetExtends(ExtendsMin, ExtendsMax, StartExtendsMin, StartExtendsMax):
    ExtraExtendsMin = np.maximum(np.zeros(3), StartExtendsMin - ExtendsMin)
    ExtraExtendsMax = np.maximum(np.zeros(3), ExtendsMax - StartExtendsMax)
    OutputExtendsMin = np.array([ExtraExtendsMin[0], ExtraExtendsMax[1], ExtraExtendsMin[2]])
    OutputExtendsMax = np.array([ExtraExtendsMax[0], ExtraExtendsMin[1], ExtraExtendsMax[2]])

    return OutputExtendsMin, OutputExtendsMax

# Creates a texture with the given pixels
def CreateTexture(Pixels, TextureWidth, TextureHeight, FileName, Format):
    # Create the texture itself
    Texture = bpy.data.images.new(
        name = FileName,
        width = TextureWidth,
        height = TextureHeight,
        alpha = True,
        float_buffer = True
    )
    
    # Set the texture settings
    Texture.colorspace_settings.is_data = True
    Texture.colorspace_settings.name = "Non-Color"
    Texture.pixels = Pixels.ravel()

    # Export the textures to disk
    properties = bpy.context.scene.VATExporter_RegularProperties
    ExportEnvironment = bpy.data.scenes.new("ImageExportEnvironment")
    ExportSettings = ExportEnvironment.render.image_settings
    ExportSettings.color_depth = Format
    ExportDirectory = bpy.path.abspath(properties.OutputDirectory)
    TargetFile = os.path.join(ExportDirectory, FileName + ".png")
    Texture.save_render(TargetFile, scene = ExportEnvironment, quality = 100)
    
    # Clean up
    bpy.data.scenes.remove(ExportEnvironment)
    bpy.data.images.remove(Texture)
    return

# Export mesh with LODs
def ExportWithLODs(Objects : list[bpy.types.Object]):
    # Get base data
    scene = bpy.context.scene
    properties = scene.VATExporter_RegularProperties
    
    # Cancel if mesh export is not enabled
    if(not properties.FileMeshEnabled):
        return

    # Give each object a decimate modifier, store the modifier in an array
    DecimateModifiers = []
    for Object in Objects:
        DecimateModifier = Object.modifiers.new("Decimate", "DECIMATE")
        DecimateModifier.angle_limit = 0.0
        DecimateModifier.decimate_type = "DISSOLVE"
        DecimateModifier.use_dissolve_boundaries = True
        DecimateModifiers.append(DecimateModifier)

    # Prepare LOD and export data
    LODList = scene.VATExporter_LODList
    if(len(LODList) == 0):
        bpy.ops.vatexporter.addlod() # Add LOD0 incase its missing

    # Iterate through the LODs and export
    BaseName = properties.FileMeshName
    BaseDirectory = properties.OutputDirectory
    for i, LOD in enumerate(LODList):
        # Correct settings for the LODs
        AngleLimit = 3.141519 * (1 - LOD.ReductionRate / 100.0)
        for DecimateModifier in DecimateModifiers:
            DecimateModifier.angle_limit = AngleLimit

        # Export settings
        NewName = BaseName
        if(i > 0):
            NewName += f"_LOD{i}"
        ExportFile = os.path.join(BaseDirectory, bpy.path.clean_name(NewName) + ".fbx")

        # Perform the export
        bpy.ops.export_scene.fbx(
            filepath = ExportFile,
            use_selection = True,
            bake_space_transform = False,
            bake_anim = False
        )


