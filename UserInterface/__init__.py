from . import (
    MainMenu,
    MeshSettings,
    Properties,
    VATSettings,
    ExportSettings
)
from importlib import reload

modules = [MainMenu, Properties, VATSettings, MeshSettings, ExportSettings]

def register():
    for module in modules:
        reload(module)
        module.register()

def unregister():
    for module in modules:
        module.unregister()
