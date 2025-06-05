modules = []

def register():
    for module in modules:
        module.register()

def unregister():
    for module in modules:
        module.unregister()