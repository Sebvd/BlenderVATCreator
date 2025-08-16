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

    # Checkbox whether to export the position texture
    FilePositionTextureEnabled : BoolProperty(
        name = "File position texture enabled",
        description = "Whether to export a position texture",
        default = True
    )

    # Checkbox whether to export the normal texture
    FileRotationTextureEnabled : BoolProperty(
        name = "File rotation texture enabled",
        description = "Whether to export a rotation texture",
        default = True
    )

    # Checkbox whether to export the lookup texture
    FileLookUpTextureEnabled : BoolProperty(
        name = "Lookup texture enabled",
        description = "Whether to export the lookup texture",
        default = True
    )

    # Checkbox whether to export the file mesh
    FileMeshEnabled : BoolProperty(
        name = "File mesh enabled",
        description = "Whether to export a VAT mesh",
        default = True
    )

    # Checkbox whether to export the JSON data
    FileJSONDataEnabled : BoolProperty(
        name = "JSON data enabled",
        description = "Whether to export a separate JSON file that contains information on the VAT animation",
        default = True
    )

    # Export settings for the position texture
    FilePositionTextureFormat : EnumProperty(
        name = "File position texture format",
        description = "The format of the position texture",
        items = [
            ("8", "8 bit float", ""),
            ("16", "16 bit float", "")
        ],
        default = "16"
    )

    # Export settings for the rotation texture
    FileRotationTextureFormat : EnumProperty(
        name = "File rotation texture format",
        description = "The format of the rotation texture",
        items = [
            ("8", "8 bit float", ""),
            ("16", "16 bit float", "")
        ],
        default = "8"
    )

    # Maximum export resolutions
    ExportResolutionU : IntProperty(
        name = "Max size U",
        description = "The maximum size of the produced texture(s) alongside the U coordinate",
        min = 1,
        soft_min = 1,
        soft_max = 4096,
        default = 4096 
    )
    ExportResolutionV : IntProperty(
        name = "Max size V",
        description = "The maximum size of the produced texture(s) alongside the V coordinate",
        min = 1,
        soft_min = 1,
        soft_max = 4096,
        default = 4096 
    )

    # Settings for export coordinate system
    CoordinateSystem : EnumProperty(
        name = "Coordinate system",
        description  = "The coordinate system to export to",
        items = [
            ("xyz", "xyz", ""),
            ("xzy", "xzy", ""),
            ("yxz", "yxz", ""),
            ("yzx", "yzx", ""),
            ("zxy", "zxy", ""),
            ("zyx", "zyx", "")
        ]
    )
    FlipX : BoolProperty(
        name = "Flip X",
        description = "Flip the (Blender) X coordinate",
        default = False
    )
    FlipY : BoolProperty(
        name = "Flip Y",
        description = "Flip the (Blender) Y coordinate",
        default = True
    )
    FlipZ : BoolProperty(
        name = "Flip Z",
        description = "Flip the (Blender) Z coordinate",
        default = False
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