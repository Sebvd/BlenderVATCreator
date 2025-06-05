import bpy
from bpy.types import Operator, Panel
from bpy.utils import register_class, unregister_class
from math import ceil, floor
from mathutils import Vector
import numpy as np
#from .VATFunctions import FilterSelection

# ------------------------------------------------------------------ (To be moved later when building final plugin)
def FilterSelection(Objects : list[bpy.types.Object]):
    FilteredObjects = []
    for Object in Objects:
        if(Object.type == "MESH"):
            FilteredObjects.append(Object)

    return FilteredObjects

def CompareBounds(CurrentBounds, CompareBounds):
    for i in range(3):
        if(abs(CompareBounds[i]) > CurrentBounds[i]):
            CurrentBounds[i] = abs(CompareBounds[i])

def UnsignVector(InputVector):
    InputVector += Vector((1.0, 1.0, 1.0))
    InputVector /= 2.0
    InputVector = np.clip(InputVector, 0, 1)
    return InputVector

def UnsignVectors(InputVectors):
    InputVectors += np.array((1, 1, 1, 0))
    InputVectors /= np.array((2, 2, 2, 1))
    InputVectors = np.clip(InputVectors, 0, 1)
    return InputVectors
# ------------------------------------------------------------------

# Softbody calculation
def RenderSoftbodyVAT():
    # Main data & start data
    SelectedObjects = FilterSelection(bpy.context.selected_objects)
    context = bpy.context
    StartFrame = context.scene.frame_current

    # Declare main variables
    FrameStart = 1
    FrameEnd = 10
    FrameSpacing = 3

    # Prepare selected objects
    EdgeSplitModifiers, VertexCount, StartVertices, StartMesh = PrepareSelectedObjects(SelectedObjects, 1)
    FrameCount = ceil((FrameEnd - FrameStart + 1) / FrameSpacing)
    PixelPositions = np.ones((VertexCount * FrameCount, 4))
    PixelNormals = np.ones((VertexCount * FrameCount, 4))
    Bounds = Vector((0.0, 0.0, 0.0))

    # Start VAT process
    for Frame in range(FrameStart, FrameEnd + 1, FrameSpacing):
        LocalArrayPosition = 0
        FrameArrayPosition = floor((Frame - FrameStart) / FrameSpacing) * VertexCount
        for SelectedObject in SelectedObjects:
            # Get data from the frame
            FramePositions, FrameNormals, FrameBounds = GetObjectDataAtFrame(SelectedObject, Frame, StartVertices)
            ObjectVertexCount = len(SelectedObject.data.vertices)

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

    # Create the export data
    CreateVATMeshes(SelectedObjects, VertexCount, FrameCount)
    
    # Reset selected objects to their original state
    bpy.data.meshes.remove(StartMesh)
    context.scene.frame_set(StartFrame)
    RemoveEdgeSplit(SelectedObjects, EdgeSplitModifiers)

# Assign edge split modifier
def PrepareSelectedObjects(Objects : list[bpy.types.Object], EvaluationFrame : int):
    # Get the object data from the evaluation frame
    VertexCount = 0
    EdgeSplitModifiers = []
    Vertices = []
    for Object in Objects:
        # Assign an edge split modifier is the toggle for sharp edges has been enabled
        EdgeSplitModifier = Object.modifiers.new("EdgeSplit", "EDGE_SPLIT")
        EdgeSplitModifier.use_edge_angle = False
        EdgeSplitModifier.use_edge_sharp = True
        EdgeSplitModifiers.append(EdgeSplitModifier)

        # Calculate the vertexcount across all objects
        CompareMesh = GetObjectAtFrame(Object, EvaluationFrame)
        
        Vertices += CompareMesh.vertices
        
        VertexCount += len(Vertices)

    # Clean up and return
    return EdgeSplitModifiers, VertexCount, Vertices, CompareMesh

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
def GetObjectDataAtFrame(Object : bpy.types.Object, Frame, CompareVertices):
    # Get object data
    CompareMesh = GetObjectAtFrame(Object, Frame)
    Vertices = CompareMesh.vertices
    Positions = np.ones((len(Vertices), 4))
    Normals = np.ones((len(Vertices), 4))
    Bounds = Vector((0.0, 0.0, 0.0))

    # Create vertex offsets and normals data
    for Vertex in Vertices:
        # Position calculation
        Offset = Vertex.co - CompareVertices[Vertex.index].co
        ConvertedOffset = (Offset[0], -1 * Offset[1], Offset[2], 1.0)
        Positions[Vertex.index] = ConvertedOffset

        # Create new bounds
        CompareBounds(Bounds, ConvertedOffset)

        # Normal calculation
        VertexNormal = UnsignVector((Vertex.normal.copy()))
        ConvertedNormal = (VertexNormal[0], -1 * VertexNormal[1], VertexNormal[2], 1.0)
        Normals[Vertex.index] = ConvertedNormal

    bpy.data.meshes.remove(CompareMesh)
    return Positions, Normals, Bounds

# Bring positions to a range from 0-1 based on the maximum calculated bounds
def NormalizePositions(Positions, Bounds):
    # Set the bounds to a minimum of 0.01 to prevent divisions by 0 in the shader
    MeasureBounds = [max((ceil(axis * 10000)/10000), 0.01) for axis in Bounds]

    # Move positions into range
    NormalizedPositions = Positions / np.array((MeasureBounds[0], MeasureBounds[1], MeasureBounds[2], 1.0))
    NormalizedPositions = UnsignVectors(NormalizedPositions)
    NormalizedPositions += np.array((1,1,1,0))
    NormalizedPositions /= np.array((2,2,2,1))

    return NormalizedPositions, MeasureBounds

# Create VAT mesh andd export it
def CreateVATMeshes(Objects : list[bpy.types.Object], VertexCount, FrameCount):
    LocalVertexCount = 0
    for Object in Objects:
        # Create a copy
        NewObject = Object.copy()
        NewObject.data = Object.data.copy()
        LocalVertexCount += len(NewObject.data.vertices)

        # UV data
        DistanceToTop = 1.0 / FrameCount * 0.5 # Make sure that the UV is exactly in the middle of the pixel in the v axis

        # Setting the UVs
        PixelUVLayer = NewObject.data.uv_layers.new(name = "PixelUVs")
        for Loop in NewObject.data.loops:
            PixelUVLayer.data[Loop.index].uv = ((Loop.vertex_index + LocalVertexCount + 0.5) / VertexCount, 1.0 - DistanceToTop)

        # Link the object to the scene for debug
        bpy.context.collection.objects.link(NewObject)
    pass

# Main function to render softbody
class VATEXPORTER_OT_RenderSoftBody(Operator):
    bl_idname = "vatexporter.rendersoftbody"
    bl_label = "Render softbody to VAT"
    bl_options = {"REGISTER"}

    # Check if the function can be ran
    @classmethod
    def poll(cls, context):
        bHasActiveObject = context.active_object != None
        bIsObjectMode = context.mode == "OBJECT"
        return bHasActiveObject and bIsObjectMode
    
    # run the function
    def execute(self, context):
        print("Softbody sim")
        RenderSoftbodyVAT()
        return {"FINISHED"}

class VATEXPORTER_PT_DebugPanel(Panel):
    bl_label = "Debug panel"
    bl_idname = "VATEXPORTER_PT_DebugPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VATTools"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("vatexporter.rendersoftbody", text = "execute")

modules = [VATEXPORTER_OT_RenderSoftBody, VATEXPORTER_PT_DebugPanel]

def register():
    for module in modules:
        register_class(module)

def unregister():
    for module in modules:
        unregister_class(module)

if __name__ == "__main__":
    register()