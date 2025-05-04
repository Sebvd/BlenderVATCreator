import bpy
from bpy.types import PropertyGroup
from bpy.props import IntProperty, EnumProperty, CollectionProperty, PointerProperty
from bpy.utils import register_class, unregister_class

class VATEXPORTER_PG_LODProperties(PropertyGroup):
    Test : IntProperty(
        name = "test",
        description = "test"
    )

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

    LODSettings : CollectionProperty(
        name = "LODs",
        type = VATEXPORTER_PG_LODProperties
    )



# Register class
def register():
    register_class(VATEXPORTER_PG_LODProperties)
    register_class(VATEXPORTER_PG_Properties)

    bpy.types.Scene.VATExporter = PointerProperty(type = VATEXPORTER_PG_Properties)

# Unregister class
def unregister():
    unregister_class(VATEXPORTER_PG_LODProperties)
    unregister_class(VATEXPORTER_PG_Properties)

    del bpy.types.Scene.VATExporter

# Debug register
if __name__ == "__main__":
    register()