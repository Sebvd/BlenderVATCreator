import bpy
import bmesh
import os
from bpy.utils import register_class, unregister_class
from bpy.types import Operator
from math import ceil
from mathutils import Vector
import numpy as np
from .VATFunctions import (
    FilterSelection,
    UnsignVector,
    CreateTexture
)

# Execute the render dynamic operator
def RenderDynamic():
    # Basic vars
    context = bpy.context
    StartSelection = FilterSelection(context.selected_objects)
    properties = context.scene.VATExporter_RegularProperties

    FrameStart = context.scene.frame_start
    FrameEnd = context.scene.frame_end
    FrameSpacing = properties.FrameSpacing

    # Prepass: Get the basic data on the simulation and the target textures
    TriangulationModifiers = PrepareSelectedObjects(StartSelection)
    FrameCount = ceil((FrameEnd - FrameStart + 1) / FrameSpacing)
    MaxVertices, MaxFaces, BoundsMin, BoundsMax, RestPoseFrame = PrePass(StartSelection, FrameStart, FrameEnd, FrameSpacing)

    # Data pass
    PixelPositions, PixelNormals, PixelData = DataPass(StartSelection, FrameStart, FrameEnd, FrameSpacing, MaxVertices, MaxFaces, BoundsMin, BoundsMax)

    # Export
    if(properties.FilePositionTextureEnabled):
        CreateTexture(PixelPositions, MaxVertices, FrameCount, properties.FilePositionTexture, properties.FilePositionTextureFormat)
    if(properties.FileRotationTextureEnabled):
        CreateTexture(PixelNormals, MaxVertices, FrameCount, properties.FileRotationTexture, properties.FileRotationTextureFormat)
    if(properties.FileDataTextureEnabled):
        CreateTexture(PixelData, MaxFaces * 3, FrameCount, properties.FileDataTexture, "16")
    if(properties.FileMeshEnabled):
        CreateVATMesh(StartSelection, RestPoseFrame, FrameCount, MaxFaces * 3)

    # Clean up
    for i, Object in enumerate(StartSelection):
        Object.modifiers.remove(TriangulationModifiers[i])

# Prepass: Get the basic data on the simulation and the target textures
def PrePass(Objects : list[bpy.types.Object], FrameStart, FrameEnd, FrameSpacing):
    MaxVertices = 0
    MaxFaces = 0
    BoundsMin = np.array([np.inf] * 3)
    BoundsMax = np.array([np.inf * -1] * 3)
    RestPoseFrame = FrameStart
    for Frame in range(FrameStart, FrameEnd + 1):
        # Set the current frame
        bpy.context.scene.frame_set(Frame)
        if((Frame - FrameStart) % FrameSpacing != 0):
            continue
        
        # Calculate the maximum number of vertices and faces in each frame
        VertexCount = 0
        FaceCount = 0
        for Object in Objects:
            CompareObject = GetObjectAtFrame(Object, Frame)
            VertexCount += len(CompareObject.data.vertices)
            FaceCount += len(CompareObject.data.polygons)
            
            # Get the maximum size of the bounding box for each frame
            Corners = [Vector(Corner) for Corner in CompareObject.bound_box]
            for Corner in Corners:
                BoundsMin = np.minimum(BoundsMin, Corner)
                BoundsMax = np.maximum(BoundsMax, Corner)
        
        if(VertexCount > MaxVertices):
            MaxVertices = VertexCount
            RestPoseFrame = Frame
        if(FaceCount > MaxFaces):
            MaxFaces = FaceCount

    return MaxVertices, MaxFaces, BoundsMin, BoundsMax, RestPoseFrame

def DataPass(Objects : list[bpy.types.Object], FrameStart, FrameEnd, FrameSpacing, VertexCount, FaceCount, BoundsMin, BoundsMax):
    # Position and normal texture data
    FrameCount = ceil((FrameEnd - FrameStart + 1) / FrameSpacing)
    TransformTextureSize = FrameCount * VertexCount
    PixelPositions = np.zeros((TransformTextureSize, 4))
    PixelNormals = np.ones((TransformTextureSize, 4))

    DataVertexCount = FaceCount * 3
    DataTextureArraySize = FrameCount * DataVertexCount
    PixelData = np.zeros((DataTextureArraySize, 4))
    
    # Write to the texture data
    for Frame in range(FrameStart, FrameEnd + 1):
        VertexCountTransforms = 0
        VertexCountData = 0
        VerticalPixelIndexTransforms = VertexCount * (Frame - FrameStart)
        VerticalPixelIndexData = DataVertexCount * (Frame - FrameStart)
        for Object in Objects:
            # Get the object data
            CompareObject = GetObjectAtFrame(Object, Frame)
            Vertices = CompareObject.data.vertices

            Faces = CompareObject.data.polygons
            for Face in Faces:
                VertexIndices = Face.vertices
                for i, VertexIndex in enumerate(VertexIndices):
                    # Write to transform textures
                    TransformTextureArrayIndex = VerticalPixelIndexTransforms + VertexCountTransforms + VertexIndex
                    FramePosition = GetRelativePosition(Vertices[VertexIndex].co, Vector(BoundsMin), Vector(BoundsMax))
                    PixelPositions[TransformTextureArrayIndex] = (*FramePosition, 1.0)
                    PixelNormals[TransformTextureArrayIndex] = (*UnsignVector(Vertices[VertexIndex].normal), 1.0)

                    # Write to data texture
                    DataTextureArrayIndex = VerticalPixelIndexData + Face.index * 3 + i + VertexCountData
                    UVData = (VertexIndex + 0.5) / VertexCount
                    PixelData[DataTextureArrayIndex] = (UVData, 1.0, 1.0, 1.0)

            VertexCountTransforms += len(Vertices)
            VertexCountData += (len(Faces) * 3)
    
    return PixelPositions, PixelNormals, PixelData

# Create VAT meshes
def CreateVATMesh(Objects : list[bpy.types.Object], RestPoseFrame, FrameCount, VertexCount):
    scene = bpy.context.scene
    scene.frame_set(RestPoseFrame)
    bpy.ops.Object.select_all(action = "DESELECT")
    NewObjects = []
    NewDatas = []
    LocalVertexCount = 0
    for i, Object in enumerate(Objects):
        # Create duplicate objects with new data
        NewObject = Object.copy()
        CompareObject = GetObjectAtFrame(Object, RestPoseFrame)
        NewData = bpy.data.meshes.new_from_object(CompareObject)
        NewObject = bpy.data.objects.new(Object.name, NewData)
        NewObject.data.transform(Object.matrix_world)
        bpy.context.collection.objects.link(NewObject)

        # Separate all the triangles in the mesh
        Normals = [Loop.normal.copy() for Loop in NewData.loops]
        bm = bmesh.new()
        bm.from_mesh(NewData)
        bmesh.ops.split_edges(bm, edges = bm.edges)
        bm.to_mesh(NewData)
        bm.free()
        NewData.normals_split_custom_set(Normals)
        NewData.update()

        # Set the UVs
        DistanceToTop = 1.0 / FrameCount * 0.5
        PixelUVLayer = NewObject.data.uv_layers.new(name = "PixelUVs")
        for Loop in NewObject.data.loops:
            PixelUVLayer.data[Loop.index].uv = (
                (Loop.vertex_index + LocalVertexCount + 0.5) / VertexCount,
                1.0 - DistanceToTop
            )

        # Update the arrays for cleanup afterwards
        NewObjects.append(NewObject)
        NewDatas.append(NewData)
        LocalVertexCount += len(NewData.vertices)

    # Export
    ExportVATMesh(NewObjects)

    # Clean up
    for i, NewObject in enumerate(NewObjects):
        bpy.data.objects.remove(NewObject)
        bpy.data.meshes.remove(NewDatas[i])
        pass

# Function to export the VAT mesh
def ExportVATMesh(Objects : list[bpy.types.Object]):
    # Get base data
    scene = bpy.context.scene
    properties = scene.VATExporter_RegularProperties

    # Cancel if mesh export is not enabled
    if(not properties.FileMeshEnabled):
        return
    
    # Select the objects to export
    for Object in Objects:
        Object.select_set(True)
    
    # Export
    BaseName = properties.FileMeshName
    BaseDirectory = properties.OutputDirectory
    ExportFile = os.path.join(BaseDirectory, bpy.path.clean_name(BaseName) + ".fbx")
    bpy.ops.export_scene.fbx(
        filepath = ExportFile,
        use_selection = True,
        bake_space_transform = False,
        bake_anim = False
    )

def PrepareSelectedObjects(Objects : list[bpy.types.Object]):
    TriangulationModifiers = []
    for Object in Objects:
        TriangulateModifier = Object.modifiers.new("Triangulate", "TRIANGULATE")
        TriangulationModifiers.append(TriangulateModifier)

    return TriangulationModifiers

def GetObjectAtFrame(Object : bpy.types.Object, Frame : int):
    # Get base variables
    context = bpy.context
    scene = context.scene
    scene.frame_set(Frame)

    # Get the object at the current frame
    DependencyGraph = context.view_layer.depsgraph
    CompareObject = Object.evaluated_get(DependencyGraph)

    return CompareObject

def GetRelativePosition(Position : Vector, BoundsMin : Vector, BoundsMax : Vector):
    OriginPosition = Position - BoundsMin
    BoundsSize = BoundsMax - BoundsMin
    RelativePosition = Vector([OriginPosition[i] / BoundsSize[i] for i in range(3)])

    return RelativePosition

class VATEXPORTER_OT_RenderDynamic(Operator):
    bl_idname = "vatexporter.renderdynamic"
    bl_label = "Render dynamic polycounts to VAT"
    bl_options = {"REGISTER"}

    # Check if the function can be ran
    @classmethod
    def poll(self, context):
        # Check based on object selection
        bHasActiveObject = context.active_object != None
        bIsObjectMode = context.mode == "OBJECT"

        # Check based on user settings
        properties = context.scene.VATExporter_RegularProperties
        bIsExporting = properties.FileMeshEnabled or properties.FileJSONDataEnabled or properties.FilePositionTextureEnabled or properties.FileRotationTextureEnabled or properties.FileDataTextureEnabled

        return bHasActiveObject and bIsObjectMode and bIsExporting
    
    # run the function
    def execute(self, context):
        print("executing dynamic polycounts")
        RenderDynamic()
        return {"FINISHED"}

def register():
    register_class(VATEXPORTER_OT_RenderDynamic)

def unregister():
    unregister_class(VATEXPORTER_OT_RenderDynamic)