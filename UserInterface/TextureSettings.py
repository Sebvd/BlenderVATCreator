from bpy.types import Panel
from bpy.utils import register_class, unregister_class

class VATEXPORTER_PT_TextureSettings(Panel):
    # Class variables
    bl_label = "Texture & JSON settings"
    bl_idname = "VATEXPORTER_PT_TextureSettings"
    bl_parent_id = "VATEXPORTER_PT_VATSettings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    # Draw header
    def draw_header_preset(self, context):
        layout = self.layout
        operator = layout.operator("wm.call_menu",
                                   text = "",
                                   icon = "PRESET",
                                   emboss = False
                                   )
        operator.name = "VATEXPORTER_MT_EnginePresets"

    # Draw body
    def draw(self, context):
        scene = context.scene
        properties = scene.VATExporter_RegularProperties
        layout = self.layout

        # Maximum texture sizes and coordinate systems
        row = layout.row()
        split = row.split(factor = 0.4)
        column = split.column()
        column.label(text = "Target Coords")
        column.label(text = "Flip Coords")
        column.label(text = "Max U")

        column = split.column()
        column.prop(properties, "CoordinateSystem", text = "")
        row = column.row()
        row.prop(properties, "FlipX", text = "X")
        row.prop(properties, "FlipY", text = "Y")
        row.prop(properties, "FlipZ", text = "Z")
        column.prop(properties, "ExportResolutionU", text = "")
        
        # Advanced settings
        if(properties.VATType == "FLUID"):
            row = layout.row()
            split = row.split(factor = 0.4)
            column = split.column()
            column.label(text = "Max U (Data)")
            column = split.column()
            column.prop(properties, "DataTextureResolutionU", text = "")

# Register class
def register():
    register_class(VATEXPORTER_PT_TextureSettings)

# Unregister class
def unregister():
    unregister_class(VATEXPORTER_PT_TextureSettings)

# Debug register
if __name__ == "__main__":
    register()