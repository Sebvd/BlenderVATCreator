import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Operator

class VATEXPORTER_OT_RenderDynamic(Operator):
    bl_idname = "vatexporter.renderdynamic"
    bl_label = "Render dynamic polycounts to VAT"
    bl_options = {"REGISTER"}

    # Check if the function can be ran
    @classmethod
    def poll(self, context):
        # Check based on object selection
        bHasActiveObject = context.active_object != None
        bIsObjectMode = context.mode == "OBJECT"

        # Check based on user settings
        properties = context.scene.VATExporter_RegularProperties
        bIsExporting = properties.FileMeshEnabled or properties.FileJSONDataEnabled or properties.FilePositionTextureEnabled or properties.FileRotationTextureEnabled or properties.FileLookUpTextureEnabled

        return bHasActiveObject and bIsObjectMode and bIsExporting
    
    # run the function
    def execute(self, context):
        print("executing dynamic polycounts")
        return {"FINISHED"}

def register():
    register_class(VATEXPORTER_OT_RenderDynamic)

def unregister():
    unregister_class(VATEXPORTER_OT_RenderDynamic)