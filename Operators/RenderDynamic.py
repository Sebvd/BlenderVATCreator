import bpy
import bmesh
import os
import json
from bpy.utils import register_class, unregister_class
from bpy.types import Operator
from math import ceil, floor
from mathutils import Vector
import numpy as np
from .VATFunctions import (
    FilterSelection,
    UnsignVector,
    CreateTexture,
    ConvertCoordinate,
    GetExtends
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
    Modifiers = PrepareSelectedObjects(StartSelection)
    FrameCount = (FrameEnd - FrameStart + 1)

    # Pass 1: Prepass
    VertexCount, Bounds, RestPoseFrame, RowCount, DataTextureSize, StartBounds = PrePass(StartSelection, FrameStart, FrameEnd, FrameSpacing)
    TransformTextureSize = GetTextureDimensions(VertexCount + 1)

    # Data pass
    NewObjects, NewDatas = MeshPass(StartSelection, RestPoseFrame, FrameCount, DataTextureSize)
    PixelPositions, PixelNormals, PixelData = DataPass(StartSelection, TransformTextureSize, Bounds, NewDatas, FrameCount, DataTextureSize)

    # Export
    if(properties.FilePositionTextureEnabled):
        CreateTexture(PixelPositions, TransformTextureSize[0], TransformTextureSize[1], properties.FilePositionTexture, properties.FilePositionTextureFormat)
    if(properties.FileRotationTextureEnabled):
        CreateTexture(PixelNormals, TransformTextureSize[0], TransformTextureSize[1], properties.FileRotationTexture, properties.FileRotationTextureFormat)
    if(properties.FileDataTextureEnabled):
        CreateTexture(PixelData, DataTextureSize[0], DataTextureSize[1], properties.FileDataTexture, "16")
    if(properties.FileJSONDataEnabled):
        CreateJSON(
            (Bounds[0], Bounds[1]), 
            round(DataTextureSize[1] / RowCount) - 1, 
            (GetExtends(*Bounds, *StartBounds)),
            DataTextureSize[0]
        )

    # Clean up
    for i, Object in enumerate(StartSelection): 
        Object.modifiers.remove(Modifiers[i * 2])
        Object.modifiers.remove(Modifiers[i * 2 + 1])

    for i, NewObject in enumerate(NewObjects):
        bpy.data.objects.remove(NewObject)
        bpy.data.meshes.remove(NewDatas[i])

# Prepass: Get the basic data on the simulation and the target textures
def PrePass(Objects : list[bpy.types.Object], FrameStart, FrameEnd, FrameSpacing):
    # Basic data
    BoundsMin = np.array([np.inf] * 3)
    BoundsMax = np.array([np.inf * -1] * 3)
    StartBoundsMin = BoundsMin.copy()
    StartBoundsMax = BoundsMax.copy()
    RestPoseFrame = FrameStart
    VertexCount = 0
    MaxFaceCount = 0

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
            Corners = [ConvertCoordinate(Vector(Corner) @ Object.matrix_world) for Corner in CompareObject.bound_box]
            LocalBoundsMin = np.array([np.inf] * 3)
            LocalBoundsMax = np.array([np.inf * -1] * 3)
            for Corner in Corners:
                LocalBoundsMin = np.minimum(LocalBoundsMin, Corner)
                LocalBoundsMax = np.maximum(LocalBoundsMax, Corner)

            BoundsMin = np.minimum(LocalBoundsMin, BoundsMin)
            BoundsMax = np.maximum(LocalBoundsMax, BoundsMax)

        # Write data from the rest pose frame (which is the frame with the most polys)
        if(LocalFaceCount > MaxFaceCount):
            MaxFaceCount = LocalFaceCount
            RestPoseFrame = Frame
            StartBoundsMin = LocalBoundsMin
            StartBoundsMax = LocalBoundsMax
    
    # Update bounds
    Bounds = (BoundsMin, BoundsMax)
    StartBounds = (StartBoundsMin, StartBoundsMax)

    # Calculate data texture size
    properties = bpy.context.scene.VATExporter_RegularProperties
    MaxTextureSizeU = properties.DataTextureResolutionU
    FrameCount = FrameEnd - FrameStart + 1
    VATMeshVertexCount = MaxFaceCount * 3
    RowCount = ceil(VATMeshVertexCount / MaxTextureSizeU)
    DataTextureSize = (ceil(VATMeshVertexCount / RowCount), RowCount * FrameCount)


    return VertexCount, Bounds, RestPoseFrame, RowCount, DataTextureSize, StartBounds

# Create VAT meshes
def MeshPass(Objects : list[bpy.types.Object], RestPoseFrame, FrameCount, DataTextureSize):
    # Mesh data
    scene = bpy.context.scene
    scene.frame_set(RestPoseFrame)
    bpy.ops.Object.select_all(action = "DESELECT")
    NewObjects = []
    NewDatas = []
    LocalVertexCount = 0
    properties = scene.VATExporter_RegularProperties

    # Lookup texture data
    for Object in Objects:
        # Create duplicate objects with new data
        NewObject = Object.copy()
        CompareObject = GetObjectAtFrame(Object, RestPoseFrame)
        NewData = bpy.data.meshes.new_from_object(CompareObject)
        NewObject = bpy.data.objects.new(Object.name, NewData)
        bpy.context.collection.objects.link(NewObject)

        # Separate all the triangles in the mesh
        Normals = [Vector((0,1,0)) for Loop in NewData.loops]
        bm = bmesh.new()
        bm.from_mesh(NewData)
        bmesh.ops.split_edges(bm, edges = bm.edges)
        bm.to_mesh(NewData)
        bm.free()
        NewData.normals_split_custom_set(Normals)
        NewData.update()

        # Clear the UV channels of this new object
        UVLayers = NewObject.data.uv_layers
        for UVLayer in UVLayers:
            UVLayers.remove(UVLayer)

        # Set the UVs & data texture pixels
        PixelUVLayer = NewObject.data.uv_layers.new(name = "PixelUVs")
        for Loop in NewObject.data.loops:
            CurrentRow = floor((Loop.vertex_index + LocalVertexCount) / DataTextureSize[0])
            # Set the UVs
            PixelUVLayer.data[Loop.index].uv = (
                ((((Loop.vertex_index + LocalVertexCount) % DataTextureSize[0]) + 0.5) / DataTextureSize[0]),
                ((CurrentRow * FrameCount + 0.5) / DataTextureSize[1])
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

# Data pass: Creates the position, normal and data textures
def DataPass(Objects : list[bpy.types.Object], TextureSize, Bounds, NewDatas : list[bpy.types.Mesh], FrameCount, DataTextureSize):  
    # Position and normal texture data
    TransformTextureSize = TextureSize[0] * TextureSize[1]
    PixelPositions = np.zeros((TransformTextureSize, 4))
    PixelNormals = np.zeros((TransformTextureSize, 4))
    FrameStart = bpy.context.scene.frame_start
    FrameEnd = bpy.context.scene.frame_end
    BoundsMin = Bounds[0]
    BoundsMax = Bounds[1]

    # Data texture
    PixelData = np.zeros((DataTextureSize[0] * DataTextureSize[1], 4))
    DefaultDataValue = (0.5 / DataTextureSize[0], 0.5 / DataTextureSize[1], 0.0, 1.0)
    PixelData = np.full((DataTextureSize[0] * DataTextureSize[1], 4), DefaultDataValue)

    # Write to the texture data
    FrameVertexCount = 0
    for Frame in range(FrameStart, FrameEnd + 1):
        LocalVertexCount = 0
        VerticalPixelIndex = DataTextureSize[0] * (Frame - FrameStart)
        for i, NewData in enumerate(NewDatas):
            CompareObject = GetObjectAtFrame(Objects[i], Frame)
            UVLayer = CompareObject.data.uv_layers.active
            CompareVertices = CompareObject.data.vertices
            Polygons = NewData.polygons
            Loops = NewData.loops
            TargetLoops = CompareObject.data.loops
            for Polygon in Polygons:
                if(Polygon.index >= len(CompareObject.data.polygons)):
                    continue
                TargetPolygon = CompareObject.data.polygons[Polygon.index]
                PolygonLoops = TargetPolygon.loop_indices
                LoopIndices = Polygon.loop_indices
                for k, LoopIndex in enumerate(LoopIndices):
                    # Get the data for the pixel positions
                    TargetLoop = TargetLoops[PolygonLoops[k]]
                    VertexIndex = TargetLoop.vertex_index
                    TargetVertex = CompareVertices[VertexIndex]
                    TransformArrayPosition = VertexIndex + FrameVertexCount + 1
                    TargetPosition = TargetVertex.co
                    TargetNormal = ConvertCoordinate(TargetVertex.normal)
                    ConvertedNormal = UnsignVector(Vector((TargetNormal[0], TargetNormal[1], TargetNormal[2])))
                    ConvertedPosition = ConvertCoordinate(TargetPosition)
                    PixelPositions[TransformArrayPosition] = (*GetRelativePosition(ConvertedPosition, Vector(BoundsMin), Vector(BoundsMax)), 1.0)
                    PixelNormals[TransformArrayPosition] = (*ConvertedNormal, 1.0)

                    # Write the data for the data texture
                    # UV data of transform textures
                    CurrentRow = floor((Loops[LoopIndex].vertex_index + LocalVertexCount) / DataTextureSize[0])
                    Remainder = (Loops[LoopIndex].vertex_index + LocalVertexCount ) % DataTextureSize[0]
                    DataTextureArrayIndex = CurrentRow * DataTextureSize[0] * FrameCount + Remainder + VerticalPixelIndex
                    # UV data of source mesh
                    Coordinates = (0.0, 0.0)
                    if(UVLayer != None):
                        Coordinates = UVLayer.data[TargetLoop.index].uv
                        Coordinates[0] = max(0.0, min(1.0, Coordinates[0]))
                        Coordinates[1] = max(0.0, min(1.0, Coordinates[1]))
                    UVPixel = (
                        (((TransformArrayPosition) % TextureSize[0]) + 0.5) / TextureSize[0],
                        (floor(TransformArrayPosition / TextureSize[0]) + 0.5) / TextureSize[1],
                        Coordinates[0],
                        Coordinates[1]
                    )
                    PixelData[DataTextureArrayIndex] = UVPixel


            FrameVertexCount += len(CompareVertices)
            LocalVertexCount += len(CompareVertices)


    return PixelPositions, PixelNormals, PixelData

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


# Create the JSON data used by the shader
def CreateJSON(Bounds : tuple[Vector, Vector], RowHeight, Extends, DataTextureSizeU):
    # Create the JSON dict
    properties = bpy.context.scene.VATExporter_RegularProperties
    SimulationData = dict()
    SimulationData["Type"] = "DYNAMIC"
    SimulationData["FPS"] = bpy.context.scene.render.fps
    SimulationData["PixelCountU"] = DataTextureSizeU
    SimulationData["BoundsMin"] = list(Bounds[0])
    SimulationData["BoundsMax"] = list(Bounds[1])
    SimulationData["RowHeight"] = RowHeight
    SimulationData["ExtendsMin"] = list(Extends[0])
    SimulationData["Extendsmax"] = list(Extends[1])

    # Export the JSON
    TargetDirectory = bpy.path.abspath(properties.OutputDirectory)
    FileName = bpy.path.clean_name(properties.FileJSONData)
    TargetFile = os.path.join(TargetDirectory, FileName + ".json")
    with open(TargetFile, "w") as File:
        json.dump(SimulationData, File, indent = 2)

# Append triangulation modifiers
def PrepareSelectedObjects(Objects : list[bpy.types.Object]):
    properties = bpy.context.scene.VATExporter_RegularProperties
    Modifiers = []
    bShouldSplitVertices = properties.SplitVertices
    for Object in Objects:
        # Unlock modifiers (The next modifiers must be at the end of the stack)
        ExistingModifiers = Object.modifiers
        for ExistingModifier in ExistingModifiers:
            ExistingModifier.use_pin_to_last = False

        # Assign new modifiers
        TriangulateModifier = Object.modifiers.new("Triangulate", "TRIANGULATE")
        EdgeSplitModifier : bpy.types.EdgeSplitModifier = Object.modifiers.new("EdgeSplit", "EDGE_SPLIT")
        EdgeSplitModifier.use_edge_angle = False
        EdgeSplitModifier.use_edge_sharp = bShouldSplitVertices
        Modifiers.append(TriangulateModifier)
        Modifiers.append(EdgeSplitModifier)

    return Modifiers

# Getting object data at a certain frame
def GetObjectAtFrame(Object : bpy.types.Object, Frame : int) -> bpy.types.Object:
    # Get base variables
    context = bpy.context
    scene = context.scene
    scene.frame_set(Frame)

    # Get the object at the current frame
    DependencyGraph = context.view_layer.depsgraph
    CompareObject = Object.evaluated_get(DependencyGraph)

    return CompareObject

# Get position from within the bounds
def GetRelativePosition(Position : Vector, BoundsMin : Vector, BoundsMax : Vector) -> Vector:
    OriginPosition = Position - BoundsMin
    BoundsSize = BoundsMax - BoundsMin
    RelativePosition = Vector([OriginPosition[i] / BoundsSize[i] for i in range(3)])

    return RelativePosition

# Get the texture dimensions
def GetTextureDimensions(VertexCount : int) -> tuple:
    # Initialize required data
    properties = bpy.context.scene.VATExporter_RegularProperties
    MaxSizeU = properties.ExportResolutionU

    # Calculate transform texture size
    Rows = ceil(VertexCount / MaxSizeU)
    TransformTextureSize = (ceil(VertexCount / Rows), Rows)

    return TransformTextureSize

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