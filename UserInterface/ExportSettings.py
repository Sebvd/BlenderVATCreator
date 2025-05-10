from bpy.types import Panel
from bpy.utils import register_class, unregister_class

class VATEXPORTER_PT_ExportSettings(Panel):
    # Class variables
    bl_label = "Export Settings"
    bl_idname = "VATEXPORTER_PT_ExportSettings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VATTools"
    bl_parent_id = "VATEXPORTER_PT_VATSettings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        # Basic variables
        scene = context.scene
        layout = self.layout
        properties = scene.VATExporter_RegularProperties

        # Drawing the export settings text labels
        split = layout.split()
        column = split.column()
        column.label(text = "Output directory")
        column.label(text = "Output mesh name")
        column.label(text = "Data file name")
        column.label(text = "Position texture name")
        column.label(text = "Rotation texture name")
        if(properties.VATType == "FLUID"):
            column.label(text = "Lookup texture name")

        # Drawing the export settings text fields
        column = split.column()
        column.prop(properties, "OutputDirectory", text = "")
        column.prop(properties, "FileMeshName", text = "")
        column.prop(properties, "FileJSONData", text = "")
        column.prop(properties, "FilePositionTexture", text = "")
        column.prop(properties, "FileRotationTexture", text = "")
        if(properties.VATType == "FLUID"):
            column.prop(properties, "FileLookUpTexture", text = "")


modules = [VATEXPORTER_PT_ExportSettings]

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