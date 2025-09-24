import bpy
import bmesh
import os
from bpy.utils import register_class, unregister_class
from bpy.types import Operator
from math import ceil, floor
from mathutils import Vector
import numpy as np
from .VATFunctions import (
    FilterSelection,
    UnsignVector,
    CreateTexture,
    ConvertCoordinate
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
    VertexCount, MaxFaces, BoundsMin, BoundsMax, RestPoseFrame = PrePass(StartSelection, FrameStart, FrameEnd, FrameSpacing)
    TransformTextureSize = GetTextureDimensions(VertexCount)

    # Data pass
    NewObjects, NewDatas = MeshPass(StartSelection, RestPoseFrame, FrameCount, MaxFaces * 3)
    print(f"From NewDatas: {len(NewDatas[0].vertices)}")
    print(f"From max faces: {MaxFaces * 3}")
    PixelPositions, PixelNormals, PixelData = DataPass(StartSelection, TransformTextureSize, BoundsMin, BoundsMax, NewDatas, FrameCount, MaxFaces * 3)
    

    # Export
    if(properties.FilePositionTextureEnabled):
        CreateTexture(PixelPositions, TransformTextureSize[0], TransformTextureSize[1], properties.FilePositionTexture, properties.FilePositionTextureFormat)
    if(properties.FileRotationTextureEnabled):
        CreateTexture(PixelNormals, TransformTextureSize[0], TransformTextureSize[1], properties.FileRotationTexture, properties.FileRotationTextureFormat)
    if(properties.FileDataTextureEnabled):
        CreateTexture(PixelData, MaxFaces * 3, FrameCount, properties.FileDataTexture, "16")

    # Clean up
    for i, Object in enumerate(StartSelection):
        Object.modifiers.remove(TriangulationModifiers[i])

    for i, NewObject in enumerate(NewObjects):
        bpy.data.objects.remove(NewObject)
        bpy.data.meshes.remove(NewDatas[i])

# Prepass: Get the basic data on the simulation and the target textures
def PrePass(Objects : list[bpy.types.Object], FrameStart, FrameEnd, FrameSpacing):
    # Basic data
    BoundsMin = np.array([np.inf] * 3)
    BoundsMax = np.array([np.inf * -1] * 3)
    RestPoseFrame = FrameStart
    VertexCount = 0
    MaxFaceCount = 0
    MaxVertexCount = 0

    # Find the vertexcount and facecount across the frame range
    for Frame in range(FrameStart, FrameEnd + 1):
        # Current frame
        bpy.context.scene.frame_set(Frame)
        if((Frame - FrameStart) % FrameSpacing != 0):
            continue

        # Gather vertex and face data
        LocalFaceCount = 0
        LocalVertexCount = 0
        for Object in Objects:
            CompareObject = GetObjectAtFrame(Object, Frame)
            VertexCount += len(CompareObject.data.vertices)
            LocalFaceCount += len(CompareObject.data.polygons)
            LocalVertexCount += len(CompareObject.data.vertices)

            # Get the maximum size of the bounding box for each frame
            Corners = [Vector(Corner) for Corner in CompareObject.bound_box]
            for Corner in Corners:
                BoundsMin = np.minimum(BoundsMin, Corner)
                BoundsMax = np.maximum(BoundsMax, Corner)

            if(LocalFaceCount > MaxFaceCount):
                MaxFaceCount = LocalFaceCount
                RestPoseFrame = Frame
            if(LocalVertexCount >  MaxVertexCount):
                MaxVertexCount = VertexCount
    
    BoundsMin = ConvertCoordinate(Vector(BoundsMin))
    BoundsMax = ConvertCoordinate(Vector(BoundsMax))

    return VertexCount, MaxFaceCount, BoundsMin, BoundsMax, RestPoseFrame

def DataPass(Objects : list[bpy.types.Object], TextureSize, BoundsMin, BoundsMax, NewDatas : list[bpy.types.Mesh], FrameCount, VertexCount):
    # Position and normal texture data
    TransformTextureSize = TextureSize[0] * TextureSize[1]
    PixelPositions = np.zeros((TransformTextureSize, 4))
    PixelNormals = np.zeros((TransformTextureSize, 4))
    FrameStart = bpy.context.scene.frame_start
    FrameEnd = bpy.context.scene.frame_end

    # Data texture
    DataTextureSize = FrameCount * VertexCount
    PixelData = np.zeros((DataTextureSize, 4))

    # Write to the texture data
    FrameVertexCount = 0
    FrameCount = FrameEnd - FrameStart
    for Frame in range(FrameStart, FrameEnd + 1):
        LocalVertexCount = 0
        VerticalPixelIndex = VertexCount * (Frame - FrameStart)
        for i, NewData in enumerate(NewDatas):
            CompareObject = GetObjectAtFrame(Objects[i], Frame)
            CompareVertices = CompareObject.data.vertices
            Polygons = NewData.polygons
            Loops = NewData.loops
            for Polygon in Polygons:
                if(Polygon.index >= len(CompareObject.data.polygons)):
                    continue
                TargetPolygon = CompareObject.data.polygons[Polygon.index]
                TargetVertices = TargetPolygon.vertices
                LoopIndices = Polygon.loop_indices
                for k, LoopIndex in enumerate(LoopIndices):
                    # Get the data for the pixel positions
                    TargetVertex = CompareVertices[TargetVertices[k]]
                    TransformArrayPosition = TargetVertices[k] + FrameVertexCount
                    TargetPosition = ConvertCoordinate(TargetVertex.co)
                    PixelPositions[TransformArrayPosition] = (*GetRelativePosition(TargetPosition, Vector(BoundsMin), Vector(BoundsMax)), 1.0)
                    PixelNormals[TransformArrayPosition] = (*UnsignVector(TargetVertex.normal), 1.0)

                    # Write the data for the data texture
                    DataTextureArrayIndex = VerticalPixelIndex + Loops[LoopIndex].vertex_index + LocalVertexCount
                    UVPixel = (
                        ((TransformArrayPosition % TextureSize[0]) + 0.5) / TextureSize[0],
                        (floor(TransformArrayPosition / TextureSize[0]) + 0.5) / TextureSize[1],
                        0.0,
                        1.0
                    )
                    PixelData[DataTextureArrayIndex] = UVPixel

            FrameVertexCount += len(CompareVertices)
            LocalVertexCount += len(CompareVertices)


    return PixelPositions, PixelNormals, PixelData

# Create VAT meshes
def MeshPass(Objects : list[bpy.types.Object], RestPoseFrame, FrameCount, VertexCount):
    # Mesh data
    scene = bpy.context.scene
    scene.frame_set(RestPoseFrame)
    bpy.ops.Object.select_all(action = "DESELECT")
    NewObjects = []
    NewDatas = []
    LocalVertexCount = 0
    properties = scene.VATExporter_RegularProperties

    # Lookup texture data
    for i, Object in enumerate(Objects):
        # Create duplicate objects with new data
        NewObject = Object.copy()
        CompareObject = GetObjectAtFrame(Object, RestPoseFrame)
        NewData = bpy.data.meshes.new_from_object(CompareObject)
        NewObject = bpy.data.objects.new(Object.name, NewData)
        NewObject.data.transform(Object.matrix_world)
        print(len(NewObject.data.polygons))
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

        # Set the UVs & data texture pixels
        DistanceToTop = 1.0 / FrameCount * 0.5
        PixelUVLayer = NewObject.data.uv_layers.new(name = "PixelUVs")
        for Loop in NewObject.data.loops:
            # Set the UVs
            PixelUVLayer.data[Loop.index].uv = (
                (Loop.vertex_index + LocalVertexCount + 0.5) / VertexCount,
                1.0 - DistanceToTop
            )

        # Update the arrays for cleanup afterwards
        NewObjects.append(NewObject)
        NewDatas.append(NewData)
        LocalVertexCount += len(NewData.vertices)


    # Export
    if(properties.FileMeshEnabled):
        ExportVATMesh(NewObjects)

    # Return
    return NewObjects, NewDatas

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

def GetObjectAtFrame(Object : bpy.types.Object, Frame : int) -> bpy.types.Object:
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

def GetTextureDimensions(VertexCount : int):
    MaxSize = 1024
    Rows = ceil(VertexCount / MaxSize)
    return (MaxSize, Rows)

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