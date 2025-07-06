from . import (
    MainMenu,
    Properties,
    VATSettings,
    LODSettings,
    ExportSettings
)
from importlib import reload

modules = [MainMenu, Properties, VATSettings, LODSettings, ExportSettings]

def register():
    for module in modules:
        reload(module)
        module.register()

def unregister():
    for module in modules:
        module.unregister()
