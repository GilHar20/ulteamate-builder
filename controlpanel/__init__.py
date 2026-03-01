import bpy



from . import properties, ui, operators

classes = [
    properties.BLENDERRAIL_PG_Segments,
    properties.BLENDERRAIL_PG_Elements_Objects,
    properties.BLENDERRAIL_PG_Floors,
    properties.BLENDERRAIL_OT_set_active_indecies,
    properties.BLENDERRAIL_OT_add_floor,
    properties.BLENDERRAIL_OT_remove_floor,
    properties.BLENDERRAIL_OT_reorder_floor,
    properties.BLENDERRAIL_OT_add_segment,
    properties.BLENDERRAIL_OT_remove_segment,
    properties.BLENDERRAIL_OT_add_element_object,
    properties.BLENDERRAIL_OT_remove_element_object,
    
    operators.BLENDERRAIL_OT_generate_building,
    
    ui.VIEW3D_PT_treeview
]



def register():
    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.floors = bpy.props.CollectionProperty(type = properties.BLENDERRAIL_PG_Floors)
    bpy.types.Scene.segments = bpy.props.CollectionProperty(type = properties.BLENDERRAIL_PG_Segments)
    bpy.types.Scene.element_objects = bpy.props.CollectionProperty(type = properties.BLENDERRAIL_PG_Elements_Objects)

    bpy.types.Scene.active_floor_index = bpy.props.IntProperty(default = 0)
    bpy.types.Scene.active_segment_index = bpy.props.IntProperty(default = 0)



def unregister():
    if hasattr(bpy.types.Scene, 'floors'):
        delattr(bpy.types.Scene, 'floors')
    if hasattr(bpy.types.Scene, 'active_floor_index'):
        delattr(bpy.types.Scene, 'active_floor_index')
    if hasattr(bpy.types.Scene, 'active_segment_index'):
        delattr(bpy.types.Scene, 'active_segment_index')

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)