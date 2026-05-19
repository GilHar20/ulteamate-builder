import bpy



# -----------------------
# UILists:
# -----------------------

class BLENDERRAIL_UL_building_list(bpy.types.UIList):
    """UIList for displaying buildings"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        name = item.name if item.name else (item.base_object.name if item.base_object else "- no base object -")
        icon = 'CHECKBOX_HLT' if item.base_object else 'CHECKBOX_DEHLT'
        
        column = layout.column(align = True)

        name_row = column.row(align = True)
        name_row.label(text = str(index + 1) + ": " + name, icon = icon)
        name_row.prop(item, "name", text = "", placeholder = "Building Name", icon = 'FILE_FONT')

        building_row = column.row(align = True)
        building_row.prop(item, "building_collection", text = "", placeholder = "Building Collection")
        building_row.prop(item, "base_object", text = "", placeholder = "Base Object")
        select_object = layout.operator("blenderrail.select_base_object", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
        select_object.building_index = index


class BLENDERRAIL_UL_floor_list(bpy.types.UIList):
    """UIList for displaying displaying floors per building"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        active_floor_index = building.active_floor_index

        column = layout.column()
        floor_label = "#" + str(item.ID) + ", " + item.curves_collection.name

        if item.is_linked == True:
            first_row = column.row(align = True)
            first_row.label(text = floor_label, icon = 'LINKED')
            return

        icon = 'CHECKBOX_HLT' if active_floor_index == index else 'CHECKBOX_DEHLT'
        first_row = column.row(align = True)
        first_row.label(text = floor_label, icon = icon)

        op_row = first_row.row(align = True)
        op_row.alignment = 'RIGHT'

        if item.array < 2:
            select_curve = op_row.operator("blenderrail.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
            select_curve.floor_index = index
            select_curve.curve_index = -1

        if item.array >= 2:
            icon = 'DISCLOSURE_TRI_DOWN' if item.show_array else 'DISCLOSURE_TRI_RIGHT'
            op_row.prop(item, "show_array", text = "", icon = icon, emboss = False)
            select_curve = op_row.operator("blenderrail.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
            select_curve.floor_index = index
            select_curve.curve_index = -1
        
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


        
# ----------
# Main Panel
# ----------

class BLENDERRAIL_PT_control_panel(bpy.types.Panel):
    bl_label = "BlenderRail"
    bl_idname = "VIEW3D_PT_blenderrail"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderRail"


    def draw_collect_objects(self, layout, element_type, elements):
        row = layout.row()
        objects_column = row.column(align = True)
        for index, element in enumerate(elements):
            object_row = objects_column.row(align = True)
            object_row.prop(element, "object", text = "", placeholder = "Object", icon = 'OBJECT_DATA')

            select_object = object_row.operator("blenderrail.select_collect_object", text = "", icon = "RESTRICT_SELECT_OFF")
            select_object.element_type = element_type
            select_object.index = index
            object_row.prop(element, "up_stretched", text = "", toggle = -1, icon = 'CON_SIZELIMIT')
        
        buttons = row.column(align=True)
        add_object = buttons.operator("blenderrail.add_collect_object", text = "", icon = 'ADD')
        add_object.element_type = element_type
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
        # TEMP CODE TO BE REMOVED
        #buildings_box.prop(active_building, "building_collection", text = "")
        #buildings_box.prop(active_building, "floors_collection", text = "")
        #buildings_box.prop(active_building, "elements_collection", text = "")
        buildings_box.label(text = "number of curves in the building: " +str(len(active_building.all_curves)))


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
        '''
        segments_row.template_list(
            "BLENDERRAIL_UL_segment_list",
            "blenderrail_segment_list",
            active_curve,
            "segments",
            active_curve,
            "active_segment_index",
            rows = 4,
            maxrows = 10,
            columns = 5
        )
        '''

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
        data_row = property_column.row(align = True)
        data_row.prop(active_floor, "curves_collection", text = "", icon = 'OUTLINER_COLLECTION')
        data_row.label(text = "Collection:   " + active_floor.curves_collection.name, icon = 'OUTLINER_COLLECTION')
        data_row.label(text = "Curves:   " + str(len(active_floor.curves)) + "# Curves", icon = 'CURVE_DATA')

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
   

        # Segment Settings
        settings_box.separator()
        if len(active_curve.segments) > 0:
            active_segment = active_curve.segments[active_curve.active_segment_index]
            
            settings_box.label(text = "Segment Settings: ", icon = 'DISCLOSURE_TRI_RIGHT')

            property_column = settings_box.column(align = True)
            fit_method = property_column.row(align = True)
            fit_method.label(text = "Fit Method")
            fit_method.prop(active_segment, "fit_method", text = "")
            if active_segment.fit_method == 'FIXED':
                property_column.prop(active_segment, "fixed_number", text = "Fixed Number")


        # Main Elements Settings:
        settings_box.separator()
        main_elements = active_curve.main_elements

        settings_box.label(text = "Main Elements: ", icon = 'DISCLOSURE_TRI_RIGHT')

        main_elements_column = settings_box.column(align = True)
        collect_method_row = main_elements_column.row()
        collect_method_row.prop(main_elements, "collect_method", expand = True)
        if main_elements.collect_method == 'EXISTING':
            main_elements_column.prop(main_elements, "existing_collection", text = "Collection", icon = 'OUTLINER_COLLECTION')
        else:
            self.draw_collect_objects(main_elements_column, "main_elements", main_elements.objects)


        # Corner Elements Settings:
        settings_box.separator()
        corner_elements = active_curve.corner_elements

        settings_box.label(text = "Corner Elements: ", icon = 'DISCLOSURE_TRI_RIGHT')

        corner_elements_column = settings_box.column(align = True)
        collect_method_row = corner_elements_column.row()
        collect_method_row.prop(corner_elements, "collect_method", expand = True)
        if corner_elements.collect_method == 'EXISTING':
            corner_elements_column.prop(corner_elements, "existing_collection", text = "Collection", icon = 'OUTLINER_COLLECTION')
        else:
            self.draw_collect_objects(corner_elements_column, "corner_elements", corner_elements.objects)


        # Interval Elements Settings:
        #settings_box.separator()
        #settings_box.label(text = "Interval: ")

