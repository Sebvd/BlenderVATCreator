# For debugging purposes
import sys
sys.path.append("e:\school\personalprojects\\2025\TechArt\BlenderVATRoot\BlenderVATExporter")

bl_info = {
    "name" : "VAT exporter",
    "author": "Seb van den Beemt",
    "version" : (0,0),
    "blender" : (4,3,2),
    "location" : "View3D -> Sidebar",
    "description" : "Export Vertex Animation Textures (VATs)",
    "warning" : "Still in development",
    "doc_url" : ""
}

import UserInterface, Operators
from importlib import reload

modules = [UserInterface, Operators]

def register():
    for module in modules:
        reload(module)
        module.register()

def unregister():
    for module in modules:
        module.unregister()

if __name__ == "__main__":
    print("executing")
    unregister() # For now a debug
    register()