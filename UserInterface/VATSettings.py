from bpy.types import Panel, Operator
from bpy.utils import register_class, unregister_class

class VATEXPORTER_PT_VATSettings(Panel):
    # Class variables
    bl_label = "VAT settings"
    bl_idname = "VATEXPORTER_PT_VATSettings"
    bl_parent_id = "VATEXPORTER_PT_MainSettings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    # Draw header
    def draw_header_preset(self, context):
        layout = self.layout
        layout.operator("vatexporter.setenginedefault", 
                        text = "", 
                        icon = "PRESET",
                        emboss = False
                        )

    # Draw UI
    def draw(self, context):
        scene = context.scene
        properties = scene.VATExporter_RegularProperties
        layout = self.layout

        # Create sliders for maximum texture sizes
        row = layout.row()
        split = row.split(factor = 0.4)
        column = split.column()
        column.label(text = "Target Coords")
        column.label(text = "Flip Coords")
        column.label(text = "Max U")
        column.label(text = "Max V")

        column = split.column()
        column.prop(properties, "CoordinateSystem", text = "")
        row = column.row()
        row.prop(properties, "FlipX", text = "X")
        row.prop(properties, "FlipY", text = "Y")
        row.prop(properties, "FlipZ", text = "Z")
        column.prop(properties, "ExportResolutionU", text = "")
        column.prop(properties, "ExportResolutionV", text = "")

class VATEXPORTER_PT_ExportSection(Panel):
    # Class variables
    bl_label = ""
    bl_idname = "VATEXPORTER_PT_ExportSection"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VATTools"
    bl_parent_id = "VATEXPORTER_PT_MainSettings"
    bl_options = {"HIDE_HEADER"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        properties = scene.VATExporter_RegularProperties

        # A different button for every editor mode
        if(properties.VATType == "SOFTBODY"): # Softbody
            layout.operator("vatexporter.rendersoftbody", text = "Export")
        elif(properties.VATType == "RIGIDBODY"): # Rigidbody
            layout.operator("vatexporter.renderrigidbody", text = "Export")
        elif(properties.VATType == "FLUID"): # Fluid
            layout.operator("mesh.primitive_cube_add", text = "Export")
        else: # Particles
            layout.operator("mesh.primitive_cube_add", text = "Export")

# class VATEXPORTER_PT_EngineDefaultsList(Panel):
#     bl_

class VATEXPORTER_OT_SetEngineDefaults(Operator):
    bl_idname = "vatexporter.setenginedefault"
    bl_label = "automatically sets the correct coordinate system for the selected game engine"

    def execute(self, context):
        return {"FINISHED"}

modules = [VATEXPORTER_PT_VATSettings, VATEXPORTER_PT_ExportSection, VATEXPORTER_OT_SetEngineDefaults]

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