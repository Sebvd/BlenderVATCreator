from . import (
    RenderSoftBody,
    VATFunctions,
    RenderRigidBody,
    RenderDynamic
)
from importlib import reload

from . import VATFunctions
reload(VATFunctions)

modules = [RenderSoftBody, RenderRigidBody]

def register():
    for module in modules:
        reload(module)
        module.register()

def unregister():
    for module in modules:
        module.unregister()