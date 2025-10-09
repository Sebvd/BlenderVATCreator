from bpy.types import Panel
from bpy.utils import register_class, unregister_class

# Main settings panel
class VATEXPORTER_PT_MainSettings(Panel):
    # Class variables
    bl_label = "VAT exporter"
    bl_idname = "VATEXPORTER_PT_MainSettings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VATTools"
    bl_options = {"DEFAULT_CLOSED"}

    # Draw UI
    def draw(self, context):
        # Default variables
        scene = context.scene
        properties = scene.VATExporter_RegularProperties
        layout = self.layout
        split = layout.split()

        # Left column
        column = split.column()
        column.label(text = "Frame start")
        column.label(text = "Frame end")
        column.label(text = "Frame spacing")
        column.label(text = "VAT type")
        
        # Right column
        column = split.column()
        column.prop(scene, "frame_start", text = "")
        column.prop(scene, "frame_end", text = "")
        column.prop(properties, "FrameSpacing", text = "")
        column.prop(properties, "VATType", text = "")

modules = [VATEXPORTER_PT_MainSettings]

# Register class
def register():
    for module in modules:
        register_class(module)


# Unregister class
def unregister():
    for module in modules:
        unregister_class(module)

# Debug register
if __name__ == "__main__":
    register()