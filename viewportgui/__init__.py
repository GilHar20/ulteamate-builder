import bpy
from . import draw, operators


classes = [
    operators.BLENDERRAIL_OT_viewport_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    operators.BLENDERRAIL_OT_viewport_panel.shutdown()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
