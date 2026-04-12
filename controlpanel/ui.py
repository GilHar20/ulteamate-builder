import bpy



# -----------------------
# Buildings/Floors UIList
# -----------------------

class BLENDERRAIL_UL_building_list(bpy.types.UIList):
    """UIList for displaying buildings"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        name = item.name if item.name else (item.base_object.name if item.base_object else "- no base object -")
        row_icon = 'CHECKBOX_HLT' if item.base_object else 'CHECKBOX_DEHLT'
        layout.label(text = str(index + 1) + ": " + name, icon = row_icon)
        layout.prop(item, "name", icon = 'FILE_FONT', text = "", placeholder = "Building Name")
        layout.prop(item, "base_object", text = "", placeholder = "Base Object")
        select_object = layout.operator("blenderrail.select_base_object", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
        select_object.building_index = index



class BLENDERRAIL_UL_floor_list(bpy.types.UIList):
    """UIList for displaying displaying floors per building"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        active_floor_index = building.active_floor_index
        icon = 'CHECKBOX_HLT' if active_floor_index == index else 'CHECKBOX_DEHLT'

        column = layout.column()
        first_row = column.row(align = True)

        first_row.label(text = str(index + 1) + ": " + str(len(item.curves)) + "curves", icon = icon)

        op_row = first_row.row(align = True)
        op_row.alignment = 'RIGHT'
        select_curve = op_row.operator("blenderrail.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
        select_curve.floor_index = index
        if item.array > 2:
            icon = 'DISCLOSURE_TRI_DOWN' if item.show_array else 'DISCLOSURE_TRI_RIGHT'
            op_row.prop(item, "show_array", text = "", icon = icon, emboss = False)

        if item.array == 1:
            return
        elif item.array >= 2 and item.show_array == False:
            row = column.row(align = True)
            row.separator(factor = 4.0, type = 'LINE')
            row.label(text = str(item.array - 1) + " Arrayed")
            return
        for array in range(item.array - 1):
            row = column.row(align = True)
            row.separator(factor = 4.0, type = 'LINE')
            row.label(text = str(array + 2) + " Array")
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
        row.prop(item, "element_ID", text = str(index) + ": " + "segment")



# ----------
# Main Panel
# ----------

class BLENDERRAIL_PT_controlpanel(bpy.types.Panel):
    bl_label = "BlenderRail"
    bl_idname = "VIEW3D_PT_blenderrail_tree"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderRail"
    bl_options = {"DEFAULT_CLOSED"}


    def draw_collect_objects(self, layout, elements_type, objects):
        row = layout.row()
        col = row.column(align=True)
        for obj in objects:
            col.prop(obj, "object", text = "", placeholder = "Object", icon = 'OBJECT_DATA')
        buttons = row.column(align=True)
        add_object = buttons.operator("blenderrail.add_collect_object", text = "", icon = 'ADD')
        add_object.element_type = elements_type
        remove_object = buttons.operator("blenderrail.remove_collect_object", text = "", icon = 'REMOVE')
        remove_object.element_type = elements_type


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
        #buildings_box.prop(active_building, "building_collection", text = "")
        #buildings_box.prop(active_building, "floors_collection", text = "")
        #buildings_box.prop(active_building, "elements_collection", text = "")


        collections_row = layout.row(align = True)
        
        # FLOORS:
        floors_box = collections_row.box()

        floors_box.label(text = "Floors:")
        floors_row = floors_box.row(align = True)
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
        floors_column = floors_row.column(align = True)
        floors_column.operator("blenderrail.add_floor", text = "", icon = "ADD")
        remove = floors_column.operator("blenderrail.remove_floor", text = "", icon = "REMOVE")
        remove.floor_index = active_building.active_floor_index

        if len(active_building.floors) <= 0:
            floors_box.label(text = "No floors added", icon = 'INFO')
            return

        floors = active_building.floors
        floor_index = active_building.active_floor_index
        active_floor = floors[floor_index]

        move_down = floors_column.operator("blenderrail.reorder_floor", text = "", icon = 'EVENT_UP_ARROW', emboss = False)
        move_down.up_down = False
        move_down.floor_index = floor_index

        move_up = floors_column.operator("blenderrail.reorder_floor", text = "", icon = 'EVENT_DOWN_ARROW', emboss = False)
        move_up.up_down = True
        move_up.floor_index = floor_index

        new_floor = floors_column.operator("blenderrail.copy_floor", text = "", icon = 'DUPLICATE',)
        new_floor.current_floor_index = floor_index


        # CURVES:
        curves_box = collections_row.box()

        curves_box.label(text = "Curves:")
        curves_row = curves_box.row(align = True)
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
        curves_column = curves_row.column(align = True)
        curves_column.operator("blenderrail.add_curve_object", text = "", icon = "ADD")
        curves_column.operator("blenderrail.remove_curve_object", text = "", icon = "REMOVE")

        if len(active_floor.curves) <= 0:
            curves_box.label(text = "No curves added", icon = 'INFO')
            return
        
        curves = active_floor.curves
        curve_index = active_floor.active_curve_index
        active_curve = curves[curve_index]


        # SEGMENTS:
        segments_box = collections_row.box()
        segments_box.label(text = "Segments:")
        segments_row = segments_box.row(align = True)
        segments_row.template_list(
            "BLENDERRAIL_UL_segment_list",
            "blenderrail_segment_list",
            active_curve,
            "segments",
            active_curve,
            "active_segment_index",
            rows = 4,
            maxrows = 10
        )

        settings_box = layout.box()
        operators_column = settings_box.column(align = True)
        operators_column.operator("blenderrail.viewport_panel", text = "Enter Edit", icon = 'IMGDISPLAY')
        operators_column.operator("blenderrail.evaluate_building", text = "Refresh", icon = 'FILE_REFRESH')

        # Floor Settings
        settings_box.label(text = "Floor Settings: ", icon = 'DISCLOSURE_TRI_RIGHT')

        property_column = settings_box.column(align = True)
        property_column.prop(active_floor, "array", text = "Array", icon = 'ANCHOR_BOTTOM')

        # Curve Settings
        settings_box.label(text = "Curve Settings: ", icon = 'DISCLOSURE_TRI_RIGHT')

        property_column = settings_box.column(align = True)
        property_column.prop(active_curve, "height", text = "Height")
        property_column.prop(active_curve, "inset", text = "Shrink/Expand")
        floor_ceiling_row = property_column.row()
        floor_ceiling_row.label(text = "Floor/Ceiling")
        floor_ceiling_row.prop(active_curve, "floor_ceiling", expand = True)
        select_method = property_column.row()
        select_method.label(text = "Select Method")
        select_method.prop(active_curve, "select_method", expand = True)

        if active_curve.select_method == 'SEQUENCE':
            property_column.prop(active_curve, "sequence_offset", text = "Sequence Offset")
        elif active_curve.select_method == 'RANDOM':
            property_column.prop(active_curve, "random_index", text = "Random Index")
   

        # Segment Settings
        if len(active_curve.segments) > 0:
            active_segment = active_curve.segments[active_curve.active_segment_index]
            
            settings_box.label(text = "Segment Settings: ", icon = 'DISCLOSURE_TRI_RIGHT')

            property_column = settings_box.column(align = True)
            fit_method = property_column.row()
            fit_method.label(text = "Fit Method")
            fit_method.prop(active_segment, "fit_method", expand = True)
            if active_segment.fit_method == 'FIXED':
                property_column.prop(active_segment, "fixed_number", text = "Fixed Number")


        # Main Elements Settings:
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

