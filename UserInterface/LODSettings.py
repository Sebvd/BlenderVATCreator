import bpy
from bpy.types import PropertyGroup, UIList, Panel
from bpy.props import StringProperty, FloatProperty, CollectionProperty
from bpy.utils import register_class, unregister_class

# Settings for each individual LOD item
class VATEXPORTER_PG_LODSettings(PropertyGroup):
    DisplayName : StringProperty(
        name = "Display name",
        description = "LOD number",
        default = "LOD0"        
    )

    ReductionRate : FloatProperty(
        name = "Reduction rate",
        description = "The amount of reduction, expressed in percentages (0-100%)",
        default = 100,
        min = 0,
        max = 100,
        soft_min = 0,
        soft_max = 100
    )

# Widget for each individual LOD item
class VATEXPORTER_UL_LODWidget(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        row.label(text = item.DisplayName)

# Widget that draws the combined LOD menu
class VATEXPORTER_PT_LODs(Panel):
    # Class properties
    bl_label = "LOD settings"
    bl_idname = "VATEXPORTER_PT_LODs"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VATTools"

    # Draw widget
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        row.template_list("VATEXPORTER_UL_LODWidget")


modules = [VATEXPORTER_PG_LODSettings, VATEXPORTER_UL_LODWidget, VATEXPORTER_PT_LODs]

# Register
def register():
    bpy.types.Scene.LODList = CollectionProperty(type = VATEXPORTER_PG_LODSettings)
    
    for module in modules:
        register_class(module)

# Unregister
def unregister():
    del bpy.types.Scene.LODList

    for module in modules:
        unregister_class(module)

# Debug register
if __name__ == "__main__":
    register()