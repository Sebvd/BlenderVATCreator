from . import (
    MainMenu,
    Properties,
    VATSettings,
    LODSettings,
    ExportSettings
)

modules = [MainMenu, Properties, VATSettings, LODSettings, ExportSettings]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in modules:
        module.unregister()
