import bpy



from . import properties, properties_Operators, operators, sync_from_modifier_stack, ui


classes = [
    properties.UTMBUILDER_PG_utm_element,
    properties.UTMBUILDER_PG_utm_elements_group,
    properties.UTMBUILDER_PG_utm_curve_segment,
    properties.UTMBUILDER_PG_utm_curve,
    properties.UTMBUILDER_PG_utm_floor,
    properties.UTMBUILDER_PG_utm_building,

    properties_Operators.UTMBUILDER_OT_add_floor,
    properties_Operators.UTMBUILDER_OT_remove_floor,
    properties_Operators.UTMBUILDER_OT_reorder_floor,
    properties_Operators.UTMBUILDER_OT_select_floor_curves,
    properties_Operators.UTMBUILDER_OT_link_floor,
    properties_Operators.UTMBUILDER_OT_copy_floor,
    properties_Operators.UTMBUILDER_OT_floor_settings,
    
    properties_Operators.UTMBUILDER_OT_add_segment,
    properties_Operators.UTMBUILDER_OT_remove_segment,
    properties_Operators.UTMBUILDER_OT_segment_settings,

    properties_Operators.UTMBUILDER_OT_add_curve_object,
    properties_Operators.UTMBUILDER_OT_remove_curve_object,
    properties_Operators.UTMBUILDER_OT_replace_curve_object,
    properties_Operators.UTMBUILDER_OT_stack_curve_object,
    properties_Operators.UTMBUILDER_OT_curve_settings,

    properties_Operators.UTMBUILDER_OT_add_collect_object,
    properties_Operators.UTMBUILDER_OT_remove_collect_object,
    properties_Operators.UTMBUILDER_OT_reorder_collect_object,
    properties_Operators.UTMBUILDER_OT_select_collect_object,
    properties_Operators.UTMBUILDER_OT_replace_collect_object,
    properties_Operators.UTMBUILDER_OT_collect_object_settings,

    operators.UTMBUILDER_OT_evaluate_building,
    operators.UTMBUILDER_OT_generate_building,
    operators.UTMBUILDER_OT_remove_building,
    operators.UTMBUILDER_OT_select_base_object,

    sync_from_modifier_stack.UTMBUILDER_OT_sync_from_modifier_stack,
    
    ui.UTMBUILDER_UL_floor_list,
    ui.UTMBUILDER_UL_curve_list,
    ui.UTMBUILDER_UL_segment_list,
    ui.UTMBUILDER_UL_element_list,
    ui.UTMBUILDER_PT_building_setup_panel,
    ui.UTMBUILDER_PT_building_settings_panel,
]



def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.utm_building = bpy.props.PointerProperty(type = properties.UTMBUILDER_PG_utm_building)

    bpy.app.handlers.depsgraph_update_post.append(operators.on_depsgraph_update)

    bpy.types.WindowManager.utmbuilder_select_object = bpy.props.PointerProperty(type = bpy.types.Object, name = "Select Object", description = "Object picker")
    bpy.types.WindowManager.utmbuilder_select_collection = bpy.props.PointerProperty(type = bpy.types.Collection, name = "Select Collection", description = "Collection picker")



def unregister():
    if operators.on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(operators.on_depsgraph_update)

    if hasattr(bpy.types.Object, "utm_building"):
        delattr(bpy.types.Object, "utm_building")

    if hasattr(bpy.types.Scene, 'buildings'):
        delattr(bpy.types.Scene, 'buildings')
    if hasattr(bpy.types.Scene, 'active_building_index'):
        delattr(bpy.types.Scene, 'active_building_index')
    if hasattr(bpy.types.WindowManager, "utmbuilder_select_object"):
        del bpy.types.WindowManager.utmbuilder_select_object
    if hasattr(bpy.types.WindowManager, "utmbuilder_select_collection"):
        del bpy.types.WindowManager.utmbuilder_select_collection

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)