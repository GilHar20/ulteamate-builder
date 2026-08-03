import bpy



from . import properties, properties_Operators, operators, ui

classes = [
    properties.BLENDERRAIL_PG_segment,
    properties.BLENDERRAIL_PG_collect_objects,
    properties.BLENDERRAIL_PG_elements_collection,
    properties.BLENDERRAIL_PG_curve,
    properties.BLENDERRAIL_PG_floor,
    properties.BLENDERRAIL_PG_building,

    properties_Operators.BLENDERRAIL_OT_add_floor,
    properties_Operators.BLENDERRAIL_OT_remove_floor,
    properties_Operators.BLENDERRAIL_OT_reorder_floor,
    properties_Operators.BLENDERRAIL_OT_select_floor_curves,
    properties_Operators.BLENDERRAIL_OT_link_floor,
    properties_Operators.BLENDERRAIL_OT_copy_floor,
    properties_Operators.BLENDERRAIL_OT_floor_settings,
    
    properties_Operators.BLENDERRAIL_OT_add_segment,
    properties_Operators.BLENDERRAIL_OT_remove_segment,
    properties_Operators.BLENDERRAIL_OT_segment_settings,

    properties_Operators.BLENDERRAIL_OT_add_curve_object,
    properties_Operators.BLENDERRAIL_OT_remove_curve_object,
    properties_Operators.BLENDERRAIL_OT_replace_curve_object,
    properties_Operators.BLENDERRAIL_OT_stack_curve_object,
    properties_Operators.BLENDERRAIL_OT_curve_settings,

    properties_Operators.BLENDERRAIL_OT_add_collect_object,
    properties_Operators.BLENDERRAIL_OT_remove_collect_object,
    properties_Operators.BLENDERRAIL_OT_reorder_collect_object,
    properties_Operators.BLENDERRAIL_OT_select_collect_object,
    properties_Operators.BLENDERRAIL_OT_replace_collect_object,
    properties_Operators.BLENDERRAIL_OT_collect_object_settings,
    
    operators.BLENDERRAIL_OT_generate_building,
    operators.BLENDERRAIL_OT_remove_building,
    operators.BLENDERRAIL_OT_select_base_object,
    operators.BLENDERRAIL_OT_evaluate_building,
    operators.BLENDERRAIL_OT_building_settings,
    
    ui.BLENDERRAIL_UL_building_list,
    ui.BLENDERRAIL_UL_floor_list,
    ui.BLENDERRAIL_UL_curve_list,
    ui.BLENDERRAIL_UL_segment_list,
    ui.BLENDERRAIL_UL_element_list,
    ui.BLENDERRAIL_PT_control_panel
]



def register():
    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.buildings = bpy.props.CollectionProperty(type = properties.BLENDERRAIL_PG_building)

    bpy.types.Scene.active_building_index = bpy.props.IntProperty(default = 0)
    bpy.types.Scene.show_segments_grid = bpy.props.BoolProperty(default = False)
    bpy.types.Scene.segments_grid_columns = bpy.props.IntProperty(default = 6, min = 1, max = 10)

    bpy.app.handlers.depsgraph_update_post.append(operators.on_depsgraph_update)

    bpy.types.WindowManager.blenderrail_add_collect_object = bpy.props.PointerProperty(
        type = bpy.types.Object,
        name = "Element Object",
        description = "Temporary object picker for Add Element dialog",
    )



def unregister():
    if operators.on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(operators.on_depsgraph_update)

    if hasattr(bpy.types.Scene, 'buildings'):
        delattr(bpy.types.Scene, 'buildings')
    if hasattr(bpy.types.Scene, 'active_building_index'):
        delattr(bpy.types.Scene, 'active_building_index')
    if hasattr(bpy.types.Scene, 'show_segments_grid'):
        delattr(bpy.types.Scene, 'show_segments_grid')
    if hasattr(bpy.types.Scene, 'segments_grid_columns'):
        delattr(bpy.types.Scene, 'segments_grid_columns')

    if hasattr(bpy.types.WindowManager, "blenderrail_add_collect_object"):
        del bpy.types.WindowManager.blenderrail_add_collect_object

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)