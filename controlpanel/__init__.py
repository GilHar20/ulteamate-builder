import bpy



from . import properties, ui

classes = [
    properties.BLENDERRAIL_PG_RoomItem,
    properties.BLENDERRAIL_PG_FloorItem,
    properties.BLENDERRAIL_OT_set_active_indecies,
    properties.BLENDERRAIL_OT_add_floor,
    properties.BLENDERRAIL_OT_remove_floor,
    properties.BLENDERRAIL_OT_add_curve,
    properties.BLENDERRAIL_OT_remove_curve,
    ui.VIEW3D_PT_treeview
]



def register():
    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.floors = bpy.props.CollectionProperty(type = properties.BLENDERRAIL_PG_FloorItem)
    bpy.types.Scene.active_floor_index = bpy.props.IntProperty(default = 0)
    bpy.types.Scene.active_curve_index = bpy.props.IntProperty(default = 0)


def unregister():
    if hasattr(bpy.types.Scene, 'floors'):
        delattr(bpy.types.Scene, 'floors')
    if hasattr(bpy.types.Scene, 'active_floor_index'):
        delattr(bpy.types.Scene, 'active_floor_index')
    if hasattr(bpy.types.Scene, 'active_curve_index'):
        delattr(bpy.types.Scene, 'active_curve_index')

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)