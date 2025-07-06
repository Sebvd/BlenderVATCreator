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
        row = layout.row()
        row.label(text = "Output directory")
        row.prop(properties, "OutputDirectory", text = "")

        # Section on the mesh name
        box = layout.box()
        row = box.row()
        row.prop(properties, "FileMeshEnabled", text = "VAT mesh")
        row = box.row()
        if(not properties.FileMeshEnabled):
            row.enabled = False
        row.label(text = "Output mesh name")
        row.prop(properties, "FileMeshName", text = "")

        # Section on the JSON data
        box = layout.box()
        row = box.row()
        row.prop(properties, "FileJSONDataEnabled", text = "Simulation data JSON file")
        row = box.row()
        if(not properties.FileJSONDataEnabled):
            row.enabled = False
        row.label(text = "Data file name")
        row.prop(properties, "FileJSONData", text = "")

        # Section on the position texture
        box = layout.box()
        row = box.row()
        row.prop(properties, "FilePositionTextureEnabled", text = "File position texture")
        row1 = box.row()
        row2 = box.row()
        if(not properties.FilePositionTextureEnabled):
            row1.enabled = False
            row2.enabled = False
        row1.label(text = "Position texture name")
        row1.prop(properties, "FilePositionTexture", text = "")
        row2.label(text = "Format")
        row2.prop(properties, "FilePositionTextureFormat", text = "")

        # Section on the rotation texture
        box = layout.box()
        row = box.row()
        row.prop(properties, "FileRotationTextureEnabled", text = "File rotation texture")
        row1 = box.row()
        row2 = box.row()
        if(not properties.FileRotationTextureEnabled):
            row1.enabled = False
            row2.enabled = False
        row1.label(text = "Rotation texture name")
        row1.prop(properties, "FileRotationTexture", text = "")
        row2.label(text = "Format")
        row2.prop(properties, "FileRotationTextureFormat", text = "")

        # Section for the lookup texture
        if(properties.VATType == "FLUID"):
            box = layout.box()
            row = box.row()
            row.prop(properties, "FileLookUpTextureEnabled", text = "File lookup texture")
            row = box.row()
            if(not properties.FileLookUpTextureEnabled):
                row.enabled = False
            row.label(text = "Lookup texture name")
            row.prop(properties, "FileLookUpTexture", text = "")

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