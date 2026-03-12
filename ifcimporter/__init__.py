import bpy

from . import operators, ui


classes = [
    operators.BLENDERRAIL_OT_import_ifc,

    ui.BLENDERRAIL_PT_ifc_import,
]



def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
