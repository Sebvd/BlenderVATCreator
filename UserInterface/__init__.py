from . import (
    MainMenu,
    MeshSettings,
    Properties,
    VATSettings,
    ExportSettings,
    TextureSettings
)
from importlib import reload

modules = [MainMenu, Properties, VATSettings, TextureSettings, MeshSettings, ExportSettings]

def register():
    for module in modules:
        reload(module)
        module.register()

def unregister():
    for module in modules:
        module.unregister()
