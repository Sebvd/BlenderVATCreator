import bpy
from bpy.app.handlers import persistent
from bpy.types import PropertyGroup, UIList, Panel, Operator
from bpy.props import StringProperty, FloatProperty, IntProperty, CollectionProperty
from bpy.utils import register_class, unregister_class

# Settings for each individual LOD item
class VATEXPORTER_PG_LODSettings(PropertyGroup):
    DisplayName : StringProperty(
        name = "Display name",
        description = "LOD number display",
        default = "LOD0"        
    )

    ReductionRate : FloatProperty(
        name = "Reduction rate",
        description = "The amount of reduction, expressed in percentages (0-100%)",
        default = 100,
        min = 0,
        max = 100,
        soft_min = 0,
        soft_max = 100,
        precision = 4
    )

# Widget for each individual LOD item
class VATEXPORTER_UL_LODWidget(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        row.label(text = item.DisplayName, icon = "MESH_DATA")
        row.label(text = f"{item.ReductionRate}%")

# Widget that draws the combined LOD menu
class VATEXPORTER_PT_LODs(Panel):
    # Class properties
    bl_label = "LOD settings"
    bl_idname = "VATEXPORTER_PT_LODs"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VATTools"
    bl_parent_id = "VATEXPORTER_PT_VATSettings"
    bl_options = {"DEFAULT_CLOSED"}

    # Draw widget
    def draw(self, context):
        # Basic values
        layout = self.layout
        scene = context.scene

        # LODs box
        row = layout.row()
        split = row.split(factor = 0.85)
        column = split.column()
        column.template_list("VATEXPORTER_UL_LODWidget", "LODs", scene, "VATExporter_LODList", scene, "VATExporter_LODIndex")

        # + and - buttons
        column = split.column()
        column.operator("vatexporter.addlod", text = "", icon = "ADD")
        column.operator("vatexporter.removelod", text = "", icon = "REMOVE")

        # Per LOD settings
        if(scene.VATExporter_LODIndex >= 0 and scene.VATExporter_LODList):
            LOD = scene.VATExporter_LODList[scene.VATExporter_LODIndex]

            row = layout.row()
            row.label(text = "Reduction rate")
            row.prop(LOD, "ReductionRate", text = "")

# Button to add a new item to the LOD list
class VATEXPORTER_OT_AddLOD(Operator):
    bl_idname = "vatexporter.addlod"
    bl_label = "Add a new LOD"

    def execute(self, context):
        # Add the entry
        LODList = context.scene.VATExporter_LODList
        LODList.add()

        # Set the correct name
        Length = len(LODList)
        NewName = f"LOD{Length - 1}"
        LODList[Length - 1].DisplayName = NewName

        return {"FINISHED"}

# Button that allows people to remove an LOD
class VATEXPORTER_OT_RemoveLOD(Operator):
    bl_idname = "vatexporter.removelod"
    bl_label = "Remove a LOD"

    @classmethod
    def poll(cls, context):
        return context.scene.VATExporter_LODList
    
    def execute(self, context):
        # Delete the LOD and set the correct selected index
        LODList = context.scene.VATExporter_LODList
        LODIndex = context.scene.VATExporter_LODIndex

        if(len(LODList) > 1):
            LODList.remove(LODIndex)
            context.scene.VATExporter_LODIndex = min(max(0, LODIndex - 1), len(LODList) - 1)

            # Update the LODs so that they have the correct display name
            for i in range(0, len(LODList)):
                LODList[i].DisplayName = f"LOD{i}"

        return {"FINISHED"}

modules = [VATEXPORTER_PG_LODSettings, VATEXPORTER_UL_LODWidget, VATEXPORTER_PT_LODs, VATEXPORTER_OT_AddLOD, VATEXPORTER_OT_RemoveLOD]

# Create a function that builds a default value for the collection property
@persistent
def DefaultListValue(scene):
    LODList = bpy.context.scene.VATExporter_LODList
    if(len(LODList) < 1):
        LODList.add()
        LODList[0].DisplayName = "LOD0"

# Register
def register():  
    for module in modules:
        register_class(module)

    bpy.types.Scene.VATExporter_LODList = CollectionProperty(type = VATEXPORTER_PG_LODSettings)
    bpy.types.Scene.VATExporter_LODIndex = IntProperty(name = "Index for LOD list", default = 0)
    bpy.app.handlers.load_post.append(DefaultListValue)

# Unregister
def unregister():
    del bpy.types.Scene.VATExporter_LODList
    del bpy.types.Scene.VATExporter_LODIndex

    for module in modules:
        unregister_class(module)

    bpy.app.handlers.load_post.remove(DefaultListValue)

# Debug register
if __name__ == "__main__":
    register()