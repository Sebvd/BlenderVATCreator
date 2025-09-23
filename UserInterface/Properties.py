import bpy
from bpy.types import PropertyGroup, Operator
from bpy.props import IntProperty, EnumProperty, PointerProperty, BoolProperty, StringProperty
from bpy.utils import register_class, unregister_class

# Main property group
class VATEXPORTER_PG_Properties(PropertyGroup):
    # General export settings
    FrameSpacing : IntProperty(
        name = "Frame Spacing",
        description = "Instead of evaluating the VAT each frame, the VATs get evaluated every x amount of frames",
        min = 1,
        soft_min = 1,
        soft_max = 10,
        default = 1
    )
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
    SplitVertices : BoolProperty(
        name = "Split Vertices",
        description = "Split vertices at the hard edges to preserve their normals. This results in overlapping vertices, but allows you to preserve hard edges.",
        default = True
    )
    OutputDirectory : StringProperty(
        name = "Output directory",
        description = "The target directory to store the meshes in",
        subtype = "DIR_PATH"
    )
    RestPose : EnumProperty(
        name  = "Rest pose",
        description = "Where to take the rest pose from (the mesh without the animations applied)",
        items = [
            ("RANGESTART", "Range Start", ""),
            ("RANGEEND", "Range End", ""),
            ("CUSTOM", "Custom", "")
        ]
    )
    CustomRestPoseFrame : IntProperty(
        name = "Custom rest pose frame",
        description = "Which frame to take the rest pose from",
        default = 1,
        min = 0,
        soft_min = 0,
        soft_max = 256
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
    
    # Settings for mesh
    FileMeshName : StringProperty(
        name = "File mesh name",
        description = "The target file name of the generated mesh file",
        default = "SM_VATMesh",
        subtype = "FILE_NAME"
    )
    FileMeshEnabled : BoolProperty(
        name = "File mesh enabled",
        description = "Whether to export a VAT mesh",
        default = True
    )

    # Position texture settings
    FilePositionTexture : StringProperty(
        name = "File position texture name",
        description = "The target file name of the position texture",
        default = "T_Simulation_VATP",
        subtype = "FILE_NAME"
    )
    FilePositionTextureEnabled : BoolProperty(
        name = "File position texture enabled",
        description = "Whether to export a position texture",
        default = True
    )
    FilePositionTextureFormat : EnumProperty(
        name = "File position texture format",
        description = "The format of the position texture",
        items = [
            ("8", "8 bit float", ""),
            ("16", "16 bit float", "")
        ],
        default = "16"
    )

    # Rotation texture settings
    FileRotationTexture : StringProperty(
        name = "File rotation texture name",
        description = "The target file name of the rotation texture",
        default = "T_Simulation_VATN",
        subtype = "FILE_NAME"
    )
    FileRotationTextureEnabled : BoolProperty(
        name = "File rotation texture enabled",
        description = "Whether to export a rotation texture",
        default = True
    )
    FileRotationTextureFormat : EnumProperty(
        name = "File rotation texture format",
        description = "The format of the rotation texture",
        items = [
            ("8", "8 bit float", ""),
            ("16", "16 bit float", "")
        ],
        default = "8"
    )

    # Data texture settings
    FileDataTexture : StringProperty(
        name = "File data texture name",
        description = "The target file name for the data texture",
        default = "T_Simulation_VATL",
        subtype = "FILE_NAME"
    )
    FileDataTextureEnabled : BoolProperty(
        name = "Data texture enabled",
        description = "Whether to export the data texture",
        default = True
    )

    # JSON settings
    FileJSONData : StringProperty(
        name = "JSON data file name",
        description = "The target file name for the JSON file that contains additional simulation data that is required in the target engine",
        default = "Simulation_DATA",
        subtype = "FILE_NAME"
    )
    FileJSONDataEnabled : BoolProperty(
        name = "JSON data enabled",
        description = "Whether to export a separate JSON file that contains information on the VAT animation",
        default = True
    )   

    # Scale texture settings
    FileScaleTextureEnabled : BoolProperty(
        name = "Scale texture enabled",
        description = "Whether to enable encoding scaling data into a texture",
        default = False
    )
    FileSingleChannelScaleEnabled : BoolProperty(
        name = "Single channel scale",
        description = "Check this box if the scale is uniform. If checked, the scale will be encoded into the position texture, which is more performant",
        default = False
    )
    FileScaleTexture : StringProperty(
        name = "Scale texture name",
        description = "The target file name for the scale texture",
        default = "T_Simulation_VATS",
        subtype = "FILE_NAME"
    )
    FileScaleTextureFormat : EnumProperty(
        name = "File scale texture format",
        description = "The format of the scale texture",
        items = [
            ("8", "8 bit float", ""),
            ("16", "16 bit float", "")
        ],
        default = "8"
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