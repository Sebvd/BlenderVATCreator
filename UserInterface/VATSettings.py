from bpy.types import Panel, Menu, Operator
from bpy.utils import register_class, unregister_class
from bpy.props import EnumProperty

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
        operator = layout.operator("wm.call_menu", 
                        text = "", 
                        icon = "PRESET",
                        emboss = False
                        )
        operator.name = "VATEXPORTER_MT_EnginePresets"

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
            layout.operator("vatexporter.renderdynamic", text = "Export")
        else: # Particles
            layout.operator("mesh.primitive_cube_add", text = "Export")

class VATEXPORTER_MT_EnginePresets(Menu):
    bl_idname = "VATEXPORTER_MT_EnginePresets"
    bl_label = "Engine presets"

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        column.operator("vatexporter.selectenginepreset", text = "Blender (default)").EngineOption = "BLENDER"
        column.operator("vatexporter.selectenginepreset", text = "Unreal Engine (pre 5.6)").EngineOption = "OLDUNREAL"
        column.operator("vatexporter.selectenginepreset", text = "Unreal Engine").EngineOption = "NEWUNREAL"
        column.operator("vatexporter.selectenginepreset", text = "Unity").EngineOption = "UNITY"
        column.operator("vatexporter.selectenginepreset", text = "Godot").EngineOption = "GODOT"

class VATEXPORTER_OT_SelectEnginePreset(Operator):
    bl_idname = "vatexporter.selectenginepreset"
    bl_label = "Select engine preset"
    bl_options = {"REGISTER"}

    EngineOption : EnumProperty(
        name = "",
        description = "Preset of target engine to use",
        items = [
            ("BLENDER", "Blender (default)", ""),
            ("OLDUNREAL", "Unreal Engine (old)", ""),
            ("NEWUNREAL", "Unreal Engine", ""),
            ("UNITY", "Unity", ""),
            ("GODOT", "Godot", "")
        ]
    )

    def execute(self, context):
        EngineOption = self.EngineOption
        properties = context.scene.VATExporter_RegularProperties
        match EngineOption:
            case "BLENDER":
                properties.FlipX = False
                properties.FlipY = False
                properties.FlipZ = False
                properties.CoordinateSystem = "xyz"
            case "OLDUNREAL":
                properties.FlipX = False
                properties.FlipY = True
                properties.FlipZ = False
                properties.CoordinateSystem = "xyz"
            case "NEWUNREAL":
                properties.FlipX = False
                properties.FlipY = False
                properties.FlipZ = False
                properties.CoordinateSystem = "xzy"
            case "UNITY":
                properties.FlipX = False
                properties.FlipY = False
                properties.FlipZ = False
                properties.CoordinateSystem = "xzy"
            case "GODOT":
                properties.FlipX = False
                properties.FlipY = True
                properties.FlipZ = False
                properties.CoordinateSystem = "xzy"
        return {"FINISHED"}

modules = [VATEXPORTER_PT_VATSettings, VATEXPORTER_PT_ExportSection, VATEXPORTER_MT_EnginePresets, VATEXPORTER_OT_SelectEnginePreset]

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