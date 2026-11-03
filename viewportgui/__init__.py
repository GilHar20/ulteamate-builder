import bpy
from . import draw, operators, thumbnail_render, ui


classes = [
    thumbnail_render.UTMBUILDER_OT_render_selected_thumbnail,
    operators.UTMBUILDER_OT_viewport_panel,
    ui.UTMBUILDER_PT_thumbnail_panel
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    operators.UTMBUILDER_OT_viewport_panel.shutdown()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
