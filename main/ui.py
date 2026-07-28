import bpy



# -----------------------
# UILists:
# -----------------------

class BLENDERRAIL_UL_building_list(bpy.types.UIList):
    """UIList for displaying buildings"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        active_building_index = scene.active_building_index
        icon = 'CHECKBOX_HLT' if active_building_index == index else 'CHECKBOX_DEHLT'
        
        row = layout.row(align = True)
        row.label(text = "", icon = icon)
        row.prop(item, "name", text = "", placeholder = "Building Name", icon = 'FILE_FONT')

        select_object = layout.operator("blenderrail.select_base_object", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
        select_object.building_index = index


class BLENDERRAIL_UL_floor_list(bpy.types.UIList):
    """UIList for displaying displaying floors per building"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        active_floor_index = building.active_floor_index
        self.use_filter_sort_reverse = True

        if item.is_linked == True:
            label_row = layout.row(align = True)

            icon = 'CHECKBOX_HLT' if active_floor_index == index else 'CHECKBOX_DEHLT'
            label_row.label(text = "", icon = icon)
            label_row.label(text = "------------------", icon = 'LINKED')

            op_row = layout.row(align = True)
            op_row.alignment = 'RIGHT'

            select_curve = op_row.operator("blenderrail.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
            select_curve.floor_index = index
            select_curve.curve_index = -1
            visibility_icon = 'HIDE_OFF' if item.floor_visibility else 'HIDE_ON'
            op_row.prop(item, "floor_visibility", text = "", icon = visibility_icon, emboss = False)
            return

        column = layout.column()
        label_row = column.row(align = True)
        icon = 'CHECKBOX_HLT' if active_floor_index == index else 'CHECKBOX_DEHLT'
        label_row.label(text = "", icon = icon)
        label_row.label(text = "Floor #" + str(index))

        op_row = label_row.row(align = True)
        op_row.alignment = 'RIGHT'

        if item.array < 2:
            select_curve = op_row.operator("blenderrail.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
            select_curve.floor_index = index
            select_curve.curve_index = -1
            visibility_icon = 'HIDE_OFF' if item.floor_visibility else 'HIDE_ON'
            op_row.prop(item, "floor_visibility", text = "", icon = visibility_icon, emboss = False)
            return

        if item.array >= 2:
            icon = 'DISCLOSURE_TRI_DOWN' if item.show_array else 'DISCLOSURE_TRI_RIGHT'
            op_row.prop(item, "show_array", text = "", icon = icon, emboss = False)
            select_curve = op_row.operator("blenderrail.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
            select_curve.floor_index = index
            select_curve.curve_index = -1
            visibility_icon = 'HIDE_OFF' if item.floor_visibility else 'HIDE_ON'
            op_row.prop(item, "floor_visibility", text = "", icon = visibility_icon, emboss = False)
        
        if item.show_array == False:
            row = column.row(align = True)
            row.separator(factor = 4.0, type = 'LINE')
            row.label(text = str(item.array - 1) + " Arrayed")
            return

        for array in range(item.array - 1):
            row = column.row(align = True)
            row.separator(factor = 4.0, type = 'LINE')
            row.label(text = str(array + 2) + " Array", icon = 'MOD_ARRAY')
            split = row.operator("blenderrail.copy_floor", text = "", icon = 'AREA_JOIN_DOWN')
            split.current_floor_index = index
            split.split = True
            split.level_index = array


class BLENDERRAIL_UL_curve_list(bpy.types.UIList):
    """UIList for displaying displaying curves per floor"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
            scene = context.scene
            building = scene.buildings[scene.active_building_index]
            active_floor_index = building.active_floor_index
            floor = building.floors[active_floor_index]
            active_curve_index = floor.active_curve_index

            row = layout.row(align = True)
            icon = 'CHECKBOX_HLT' if index == active_curve_index else 'CHECKBOX_DEHLT'
            row.label(text = "", icon = icon)
            row.prop(item, "curve_object", text = "", placeholder = "Curve", icon = 'CURVE_DATA')
            select_curve = row.operator("blenderrail.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF')
            select_curve.floor_index = active_floor_index
            select_curve.curve_index = index


class BLENDERRAIL_UL_segment_list(bpy.types.UIList):
    """UIList for displaying displaying segments per curve"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        active_segment_index = curve.active_segment_index

        icon = 'CHECKBOX_HLT' if active_segment_index == index else 'CHECKBOX_DEHLT'

        row = layout.row(align = True)
        row.label(text = "", icon = icon)
        row.prop(item, "element_ID", text = str(index))


class BLENDERRAIL_UL_element_list(bpy.types.UIList):
    """UIList for displaying displaying segments per curve"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        elements_collection = getattr(curve, item.element_type)
        active_element_index = elements_collection.active_element_index

        icon = 'CHECKBOX_HLT' if active_element_index == index else 'CHECKBOX_DEHLT'

        row = layout.row(align = True)
        row.label(text = "", icon = icon)
        row.label(text = item.object.name, icon = 'OBJECT_DATA')

        select_object = row.operator("blenderrail.select_collect_object", text = "", icon = "RESTRICT_SELECT_OFF")
        select_object.element_type = item.element_type
        select_object.index = index

        settings = row.operator("blenderrail.collect_object_settings", text = "", icon = 'PREFERENCES')
        settings.element_type = item.element_type
        settings.collect_method = False
        settings.index = index



# -----------------------
# Main Panel
# -----------------------

class BLENDERRAIL_PT_control_panel(bpy.types.Panel):
    bl_label = "BlenderRail"
    bl_idname = "VIEW3D_PT_blenderrail_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderRail"


    def draw_collect_objects(self, layout, element_type, elements_colletion):
        row = layout.row(align = True)
        objects_column = row.column(align = True)
        objects_column.template_list(
            "BLENDERRAIL_UL_element_list",
            "blenderrail_elements_list",
            elements_colletion,
            "objects",
            elements_colletion,
            "active_element_index",
            rows = 4
        )
        
        buttons = row.column(align=True)
        add_object = buttons.operator("blenderrail.add_collect_object", text = "", icon = 'ADD')
        add_object.element_type = element_type
        add_object.active_index = elements_colletion.active_element_index
        remove_object = buttons.operator("blenderrail.remove_collect_object", text = "", icon = 'REMOVE')
        remove_object.element_type = element_type


    def draw(self, context):
        layout = self.layout
        scene = context.scene
        buildings = scene.buildings


        # BUILDINGS:
        buildings_box = layout.box()
        buildings_column = buildings_box.column(align = True)
        buildings_row = buildings_column.row()
        buildings_row.scale_y = 2.0
        buildings_row.operator("blenderrail.generate_building", text = "Add Building", icon = 'EVENT_NDOF_BUTTON_PLUS')
        buildings_column.operator("blenderrail.remove_building", text = "Remove Building", icon = 'EVENT_NDOF_BUTTON_MINUS')

        if len(buildings) <= 0:
            buildings_box.label(text = "No buildings added", icon = 'INFO')
            return

        building_index = scene.active_building_index
        active_building = buildings[building_index]

        buildings_box.template_list(
            "BLENDERRAIL_UL_building_list",
            "blenderrail_building_list",
            context.scene,
            "buildings",
            context.scene,
            "active_building_index",
            rows = 2
        )
        building_setting = buildings_box.column(align = True)
        building_setting.prop(active_building, "base_object", text = "", placeholder = "Base Object")
        building_setting.prop(active_building, "building_collection", text = "", placeholder = "Building Collection")
        building_setting.prop(active_building, "floors_collection", text = "", placeholder = "Floors Collection")
        building_setting.prop(active_building, "elements_collection", text = "", placeholder = "Elements Collection")
        building_setting.label(text = "number of curves in the building: " +str(len(active_building.all_curves)))


        collections_box = layout.box()
        collections_column = collections_box.column(align = True)
        
        # FLOORS:
        collections_column.separator()

        floors_column = collections_column.column()
        floors_column.label(text = "Floors:")
        floors_row = floors_column.row(align = True)
        floors_row.template_list(
            "BLENDERRAIL_UL_floor_list",
            "blenderrail_floor_list",
            active_building,
            "floors",
            active_building,
            "active_floor_index",
            rows = 4,
            maxrows = 10
        )

        floors_column = floors_row.column()

        floors_addremove = floors_column.column(align = True)
        floors_addremove.operator("blenderrail.add_floor", text = "", icon = "ADD")
        floors_addremove.operator("blenderrail.remove_floor", text = "", icon = "REMOVE")

        if len(active_building.floors) <= 0:
            floors_column.label(text = "No floors added", icon = 'INFO')
            return

        floors = active_building.floors
        floor_index = active_building.active_floor_index
        active_floor = floors[floor_index]

        floors_column.separator()
        floors_move = floors_column.column(align = True)
        move_down = floors_move.operator("blenderrail.reorder_floor", text = "", icon = 'EVENT_UP_ARROW')
        move_down.up_down = False
        move_down.floor_index = floor_index

        move_up = floors_move.operator("blenderrail.reorder_floor", text = "", icon = 'EVENT_DOWN_ARROW')
        move_up.up_down = True
        move_up.floor_index = floor_index

        floors_column.separator()
        floors_copy = floors_column.column(align = True)
        floors_copy.operator("blenderrail.link_floor", text = "", icon = 'LINKED')
        copy_floor = floors_copy.operator("blenderrail.copy_floor", text = "", icon = 'DUPLICATE',)
        copy_floor.current_floor_index = floor_index

        # CURVES:
        collections_column.separator()

        curves_column = collections_column.column()
        curves_column.label(text = "Curves:")
        curves_row = curves_column.row(align = True)
        curves_row.template_list(
            "BLENDERRAIL_UL_curve_list",
            "blenderrail_curve_list",
            active_floor,
            "curves",
            active_floor,
            "active_curve_index",
            rows = 4,
            maxrows = 10
        )

        if active_floor.is_linked == True:
            settings_box = layout.box()
            settings_box.label(text = "Floor is linked to another floor", icon = "INFO")
            return

        curves_column = curves_row.column()
        curve_addremove = curves_column.column(align = True)
        curve_addremove.operator("blenderrail.add_curve_object", text = "", icon = "ADD")
        curve_addremove.operator("blenderrail.remove_curve_object", text = "", icon = "REMOVE")

        if len(active_floor.curves) <= 0:
            curves_column.label(text = "No curves added", icon = 'INFO')
            return
        
        curves = active_floor.curves
        curve_index = active_floor.active_curve_index
        active_curve = curves[curve_index]


        # SEGMENTS:
        collections_column.separator()

        segments_column = collections_column.column()
        segments_column.label(text = "Segments:")
        segments_row = segments_column.row(align = True)

        segments = active_curve.segments
        segments_row.prop(scene, "show_segments_grid", text = "Show Segments Grid", icon = 'VIEW_ORTHO')
        if scene.show_segments_grid == True and len(segments) > 0:
            segments_row.prop(scene, "segments_grid_columns", text = "Columns", icon = 'GRIP_V')
            grid = segments_column.grid_flow(row_major = True, columns = scene.segments_grid_columns, align = True)
            for segment_index, segment in enumerate(segments):
                segment_settings = grid.operator("blenderrail.segment_settings", text = str(segment_index), icon = 'PARTICLE_PATH')
                segment_settings.active_index = segment_index


        collections_column.separator(factor = 2.0)

        operators_row = collections_box.row(align = True)
        operators_row.scale_y = 2
        operators_row.operator("blenderrail.viewport_panel", text = "Live Edit", icon = 'MOD_TIME')
        refresh_column = operators_row.column(align = True)
        refresh_column.alignment = 'RIGHT'
        refresh_column.operator("blenderrail.evaluate_building", text = "Refresh", icon = 'FILE_REFRESH')


        settings_box = layout.box()


        # Floor Settings
        settings_box.label(text = "Floor Settings: ", icon = 'DISCLOSURE_TRI_RIGHT')

        property_column = settings_box.column(align = True)
        property_column.prop(active_floor, "curves_collection", text = "", icon = 'OUTLINER_COLLECTION')

        property_column.prop(active_floor, "array", text = "Array", icon = 'ANCHOR_BOTTOM')
        
        stack_row = property_column.row(align = True)
        stack_floors = stack_row.operator("blenderrail.stack_curve_object", text = "Stack Floors", icon = 'TRIA_DOWN_BAR')
        stack_floors.property_to_stack = 'FLOORS'
        stack_curves = stack_row.operator("blenderrail.stack_curve_object", text = "Stack Floors & Curves", icon = 'TRIA_DOWN_BAR')
        stack_curves.property_to_stack = 'CURVES'
        
        stack_row2 = property_column.row(align = True)
        stack_floor = stack_row2.operator("blenderrail.stack_curve_object", text = "Stack Floor Curves", icon = 'TRIA_DOWN_BAR')
        stack_floor.property_to_stack = 'CURRENTFLOORCURVES'
        stack_curve = stack_row2.operator("blenderrail.stack_curve_object", text = "Snap Curve", icon = 'TRIA_DOWN_BAR')
        stack_curve.property_to_stack = 'CURRENTCURVE'
        flatten = property_column.operator("blenderrail.stack_curve_object", text = "Flatten current Floor", icon = 'TRIA_DOWN_BAR')
        flatten.property_to_stack = 'FLATTENFLOOR'
        

        # Curve Settings
        settings_box.separator()
        settings_box.label(text = "Curve Settings: ", icon = 'DISCLOSURE_TRI_RIGHT')

        property_column = settings_box.column(align = True)
        property_column.prop(active_curve, "height", text = "Height")
        property_column.prop(active_curve, "inset", text = "Shrink/Expand", )

        floor_ceiling_row = property_column.row(align = True)
        floor_ceiling_row.label(text = "Floor/Ceiling")
        floor_ceiling_row.prop(active_curve, "floor_ceiling", text = "")
        if active_curve.floor_ceiling != 'NONE':
            property_column.prop(active_curve, "thickness", text = "Extrude Thickness")
        if active_curve.floor_ceiling == 'BOTTOM' or active_curve.floor_ceiling == 'BOTH':
            property_column.prop(active_curve, "direction_bottom", text = "Bottom Extrude Offset")
        if active_curve.floor_ceiling == 'TOP' or active_curve.floor_ceiling == 'BOTH':
            property_column.prop(active_curve, "direction_top", text = "Top Extrude Offset")

        select_method = property_column.row(align = True)
        select_method.label(text = "Select Method")
        select_method.prop(active_curve, "select_method", text = "")
        if active_curve.select_method != 'CUSTOM':
            property_column.prop(active_curve, "select_per_segment", text = "Element per Segment", toggle = True)

        if active_curve.select_method == 'SEQUENCE':
            property_column.prop(active_curve, "sequence_offset", text = "Sequence Offset")
        elif active_curve.select_method == 'RANDOM':
            property_column.prop(active_curve, "random_index", text = "Random Index")
   

        # Main Elements Settings:
        settings_box.separator()
        main_elements = active_curve.main_elements

        settings_box.label(text = "Main Elements: ", icon = 'DISCLOSURE_TRI_RIGHT')

        main_elements_column = settings_box.column(align = True)
        collect_method_row = main_elements_column.row()
        collect_method_row.prop(main_elements, "collect_method", expand = True)
        if main_elements.collect_method == 'EXISTING':
            existing_collection_row = main_elements_column.row(align = True)
            existing_collection_row.prop(main_elements, "existing_collection", text = "Collection", icon = 'OUTLINER_COLLECTION')
            settings = existing_collection_row.operator("blenderrail.collect_object_settings", text = "", icon = 'PREFERENCES')
            settings.element_type = "main_elements"
            settings.collect_method = True
        else:
            self.draw_collect_objects(main_elements_column, "main_elements", main_elements)


        # Corner Elements Settings:
        settings_box.separator()
        corner_elements = active_curve.corner_elements

        settings_box.label(text = "Corner Elements: ", icon = 'DISCLOSURE_TRI_RIGHT')

        corner_elements_column = settings_box.column(align = True)
        collect_method_row = corner_elements_column.row()
        collect_method_row.prop(corner_elements, "collect_method", expand = True)
        if corner_elements.collect_method == 'EXISTING':
            existing_collection_row = corner_elements_column.row(align = True)
            existing_collection_row.prop(corner_elements, "existing_collection", text = "Collection", icon = 'OUTLINER_COLLECTION')
            settings = existing_collection_row.operator("blenderrail.collect_object_settings", text = "", icon = 'PREFERENCES')
            settings.element_type = "corner_elements"
            settings.collect_method = True
        else:
            self.draw_collect_objects(corner_elements_column, "corner_elements", corner_elements)


        # Interval Elements Settings:
        #settings_box.separator()
        #settings_box.label(text = "Interval: ")

