import bpy
from . import draw, operators, thumbnail_render, ui


classes = [
    thumbnail_render.BLENDERRAIL_OT_render_selected_thumbnail,
    operators.BLENDERRAIL_OT_viewport_panel,
    ui.BLENDERRAIL_PT_thumbnail_panel
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    thumbnail_render.register()


def unregister():
    operators.BLENDERRAIL_OT_viewport_panel.shutdown()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    thumbnail_render.unregister()
