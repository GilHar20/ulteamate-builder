import bpy



from . import properties, ui, operators

classes = [
    properties.BLENDERRAIL_PG_segment,
    properties.BLENDERRAIL_PG_collect_objects,
    #properties.BLENDERRAIL_PG_elements_collection,
    properties.BLENDERRAIL_PG_floor,
    properties.BLENDERRAIL_PG_building,

    properties.BLENDERRAIL_OT_set_active_indecies,

    properties.BLENDERRAIL_OT_add_floor,
    properties.BLENDERRAIL_OT_remove_floor,
    properties.BLENDERRAIL_OT_reorder_floor,
    properties.BLENDERRAIL_OT_select_floor_curves,
    properties.BLENDERRAIL_OT_split_floor_array,
    
    properties.BLENDERRAIL_OT_add_segment,
    properties.BLENDERRAIL_OT_remove_segment,

    properties.BLENDERRAIL_OT_add_collect_object,
    properties.BLENDERRAIL_OT_remove_collect_object,

    operators.BLENDERRAIL_OT_generate_building,
    operators.BLENDERRAIL_OT_remove_building,
    operators.BLENDERRAIL_OT_select_base_object,
    operators.BLENDERRAIL_OT_evaluate_building,
    
    ui.BLENDERRAIL_UL_building_list,
    ui.BLENDERRAIL_UL_floor_list,
    ui.BLENDERRAIL_PT_controlpanel
]



def register():
    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.buildings = bpy.props.CollectionProperty(type = properties.BLENDERRAIL_PG_building)

    bpy.types.Scene.active_building_index = bpy.props.IntProperty(default = 0)

    bpy.app.handlers.depsgraph_update_post.append(operators.on_depsgraph_update)



def unregister():
    if operators.on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(operators.on_depsgraph_update)

    if hasattr(bpy.types.Scene, 'buildings'):
        delattr(bpy.types.Scene, 'buildings')
    if hasattr(bpy.types.Scene, 'active_building_index'):
        delattr(bpy.types.Scene, 'active_building_index')

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)