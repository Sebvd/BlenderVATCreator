bl_info = {
    "name" : "VAT exporter",
    "author": "Seb van den Beemt",
    "version" : (1,0),
    "blender" : (4,3,2),
    "location" : "View3D -> Sidebar",
    "description" : "Export Vertex Animation Textures (VATs)",
    "doc_url" : ""
}

from . import (
    UserInterface, 
    Operators
)
from importlib import reload

modules = [UserInterface, Operators]

def register():
    for module in modules:
        reload(module)
        module.register()

def unregister():
    for module in modules:
        module.unregister()