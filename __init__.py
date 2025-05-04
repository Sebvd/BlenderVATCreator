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

modules = []

def register():
    for module in modules:
        module.register

def unregister():
    for module in modules:
        module.unregister