import bpy
from bpy.types import PropertyGroup, Operator
from bpy.props import IntProperty, EnumProperty, PointerProperty, BoolProperty, StringProperty
from bpy.utils import register_class, unregister_class

# Main property group
class VATEXPORTER_PG_Properties(PropertyGroup):
    # Frame spacing, the frequency of frames to evaluate
    FrameSpacing : IntProperty(
        name = "Frame Spacing",
        description = "Instead of evaluating the VAT each frame, the VATs get evaluated every x amount of frames",
        min = 1,
        soft_min = 1,
        soft_max = 10,
        default = 1
    )

    # VAT type (Softbody, rigidbody, fluid, particles)
    VATType : EnumProperty(
        name = "",
        description = "The type of VAT to choose",
        items = [
            ("SOFTBODY", "Soft body", ""),
            ("RIGIDBODY", "Rigid body", ""),
            ("FLUID", "Fluid", ""),
            ("PARTICLE", "Particle", "")
        ],
        default = "SOFTBODY"
    )

    # For softbody sims: Whether or not split the vertices at your hard edges to preserve their normals
    SplitVertices : BoolProperty(
        name = "Split Vertices",
        description = "Split vertices at the hard edges to preserve their normals. This results in overlapping vertices, but allows you to preserve hard edges.",
        default = True
    )

    # Target directory of the generated files
    OutputDirectory : StringProperty(
        name = "Output directory",
        description = "The target directory to store the meshes in",
        subtype = "DIR_PATH"
    )
    
    # Target name of the generated VAT mesh
    FileMeshName : StringProperty(
        name = "File mesh name",
        description = "The target file name of the generated mesh file",
        default = "SM_VATMesh",
        subtype = "FILE_NAME"
    )

    # Target name of the generated VAT position texture
    FilePositionTexture : StringProperty(
        name = "File position texture name",
        description = "The target file name of the position texture",
        default = "T_Simulation_VATP",
        subtype = "FILE_NAME"
    )

    # Target name of the generated VAT rotation texture
    FileRotationTexture : StringProperty(
        name = "File rotation texture name",
        description = "The target file name of the rotation texture",
        default = "T_Simulation_VATN",
        subtype = "FILE_NAME"
    )

    # Target name of the generated VAT lookup texture - only intended for fluid animations
    FileLookUpTexture : StringProperty(
        name = "File lookup texture name",
        description = "The target file name for the lookup texture",
        default = "T_Simulation_VATL",
        subtype = "FILE_NAME"
    )

    # Target name of the generated JSON information file
    FileJSONData : StringProperty(
        name = "JSON data file name",
        description = "The target file name for the JSON file that contains additional simulation data that is required in the target engine",
        default = "Simulation_DATA",
        subtype = "FILE_NAME"
    )

# Register class
def register():
    register_class(VATEXPORTER_PG_Properties)

    bpy.types.Scene.VATExporter_RegularProperties = PointerProperty(type = VATEXPORTER_PG_Properties)

# Unregister class
def unregister():
    unregister_class(VATEXPORTER_PG_Properties)

    del bpy.types.Scene.VATExporter_RegularProperties

# Debug register
if __name__ == "__main__":
    register()