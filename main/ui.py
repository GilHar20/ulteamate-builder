import bpy
from .. import icons
from .. utilities import resolve_building_object as resolve
from .. utilities.preferences import UTMBUILDER_Preferences
from .. utilities import asset_library_setup as asset_library
from .. viewportgui.operators import UTMBUILDER_OT_viewport_panel



# -----------------------
# UILists:
# -----------------------

class UTMBUILDER_UL_floor_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        building = data
        active_floor_index = building.active_floor_index
        self.use_filter_sort_reverse = True

        if item.is_linked == True:
            label_row = layout.row(align = True)

            icon = 'CHECKBOX_HLT' if active_floor_index == index else 'CHECKBOX_DEHLT'
            label_row.label(text = "", icon = icon)
            label_row.label(text = "Floor #" + str(index) + " -----", icon = 'LINKED')

            op_row = layout.row(align = True)
            op_row.alignment = 'RIGHT'

            realize_floor = op_row.operator("utmbuilder.copy_floor", text = "", icon = 'UNLINKED', emboss = False)
            realize_floor.floor_index = index
            realize_floor.mode = "REALIZE"

            select_curve = op_row.operator("utmbuilder.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
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
            floor_settings = op_row.operator("utmbuilder.floor_settings", text = "", icon = 'PREFERENCES', emboss = False)
            floor_settings.index = index
            select_curve = op_row.operator("utmbuilder.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
            select_curve.floor_index = index
            select_curve.curve_index = -1
            visibility_icon = 'HIDE_OFF' if item.floor_visibility else 'HIDE_ON'
            op_row.prop(item, "floor_visibility", text = "", icon = visibility_icon, emboss = False)
            return

        if item.array >= 2:
            icon = 'DISCLOSURE_TRI_DOWN' if item.show_array else 'DISCLOSURE_TRI_RIGHT'
            op_row.prop(item, "show_array", text = "", icon = icon, emboss = False)
            floor_settings = op_row.operator("utmbuilder.floor_settings", text = "", icon = 'PREFERENCES', emboss = False)
            floor_settings.index = index
            select_curve = op_row.operator("utmbuilder.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
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
            split = row.operator("utmbuilder.copy_floor", text = "", icon = 'AREA_JOIN_DOWN')
            split.floor_index = index
            split.mode = "SPLIT"
            split.level_index = array


class UTMBUILDER_UL_curve_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align = True)
        icon = 'CHECKBOX_HLT' if item.is_selected else 'CHECKBOX_DEHLT'
        row.prop(item, "is_selected" ,text = "", icon = icon, emboss = False)
        curve_name = item.curve_object.name if item.curve_object else "(none)"
        row.label(text = curve_name, icon = 'CURVE_DATA')

        curve_settings = row.operator("utmbuilder.curve_settings", text = "", icon = 'PREFERENCES', emboss = False)
        curve_settings.curve_index = index
        curve_settings.mode = 'SINGLE'

        select_curve = row.operator("utmbuilder.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
        select_curve.floor_index = data.ID
        select_curve.curve_index = index

        replace_curve = row.operator("utmbuilder.replace_curve_object", text = "", icon = 'DECORATE_OVERRIDE', emboss = False)
        replace_curve.index = index


class UTMBUILDER_UL_segment_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon = 'CHECKBOX_HLT' if item.is_selected else 'CHECKBOX_DEHLT'

        row = layout.row(align = True)
        row.prop(item, "is_selected" ,text = "", icon = icon, emboss = False)
        row.prop(item, "element_ID", text = str(index))


class UTMBUILDER_UL_element_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        elements_collection = data

        icon = 'CHECKBOX_HLT' if item.is_selected else 'CHECKBOX_DEHLT'

        row = layout.row(align = True)
        row.prop(item, "is_selected", text = "", icon = icon, emboss = False)
        
        if item.is_empty:
            text = str(item.ID) + "Empty Element"
        else:
            obj_name = item.object.name if item.object else "(none)"
            text = obj_name
        row.label(text = text, icon = 'OBJECT_DATA')

        elements_settings = row.operator("utmbuilder.element_settings", text = "", icon = 'PREFERENCES', emboss = False)
        elements_settings.element_type = item.element_type
        elements_settings.element_index = index
        elements_settings.mode = 'SINGLE'

        select_object = row.operator("utmbuilder.select_element_object", text = "", icon = "RESTRICT_SELECT_OFF", emboss = False)
        select_object.element_type = item.element_type
        select_object.index = index

        replace_object = row.operator("utmbuilder.replace_element_object", text = "", icon = "DECORATE_OVERRIDE", emboss = False)
        replace_object.element_type = item.element_type
        replace_object.index = index



# -----------------------
# Panels
# -----------------------

class UTMBUILDER_PT_building_setup_panel(bpy.types.Panel):
    bl_label = "ULTEAMMATE Builder"
    bl_idname = "UTMBUILDER_PT_building_setup_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ULTEAMMATE"


    def _draw_asset_library_not_setup(self, context):
        asset_library.sync_asset_library_exists_from_filepaths()
        addon = context.preferences.addons.get(UTMBUILDER_Preferences.bl_idname)
        return not addon.preferences.asset_library_exists

    def draw_header(self, context):
        layout = self.layout
        
        title_row = layout.row()
        pcoll = icons.preview_collections.get("main")
        if pcoll:
            title_row.label(text = "", icon_value = pcoll["panel_logo"].icon_id)

    def draw_header_preset(self, context):
        layout = self.layout
        settings_row = layout.row(align = True)
        settings_row.alignment = 'RIGHT'
        settings_row.operator("utmbuilder.open_addon_preferences", text = "", icon = "PREFERENCES")

    def draw(self, context):
        layout = self.layout

        if self._draw_asset_library_not_setup(context):
            lib_box = layout.box()
            lib_box.alert = True
            lib_box.label(text = "Asset library is not set up properly!", icon = 'ERROR')
            lib_box.label(text = "Open preferences to set up the asset library", icon = 'ERROR')
            lib_box.operator("utmbuilder.open_addon_preferences", text = "Open Addon Preferences", icon = "PREFERENCES")
            return

        setup_box = layout.box()
        setup_box.label(text = "Building Setup:", icon = 'HOME')

        setup_column = setup_box.column(align = True)
        add_row = setup_column.row()
        add_row.scale_y = 1.5
        add_row.operator("utmbuilder.generate_building", text = "Add New Building", icon = 'EVENT_NDOF_BUTTON_PLUS')

        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            setup_box.label(text = "No valid building selected", icon = 'INFO')
            setup_box.operator("utmbuilder.sync_from_modifier_stack", text = "Sync from Modifers", icon = 'MODIFIER')
            return
        
        _, building = resolved
        
        row = setup_column.row(align = True)
        row.operator("utmbuilder.remove_building", text = "Remove Building", icon = 'EVENT_NDOF_BUTTON_MINUS')
        row.operator("utmbuilder.evaluate_building", text = "Refresh", icon = 'FILE_REFRESH')

        setup_box.separator()
        setup_box.label(text = "Building: " + building.name, icon = 'HOME')

        building_row = setup_box.row(align = True)
        building_row.operator('utmbuilder.building_settings', text = "Building Settings", icon = 'HOME')
        active_object = context.view_layer.objects.active
        if not resolve._is_utm_building(active_object):
            building_row.operator('utmbuilder.select_base_object', text = "", icon = 'RESTRICT_SELECT_OFF')
        return



class UTMBUILDER_PT_building_settings_panel(bpy.types.Panel):
    bl_label = "Building Settings"
    bl_idname = "UTMBUILDER_PT_building_settings_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ULTEAMMATE"
    bl_parent_id = "UTMBUILDER_PT_building_setup_panel"


    @classmethod
    def poll(cls, context):
        addon = context.preferences.addons.get(UTMBUILDER_Preferences.bl_idname)
        if not addon.preferences.asset_library_exists:
            return False
        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            return False
        else:
            return True

    def draw_collect_objects(self, layout, element_type, elements_group):
        objects_row = layout.row(align = True)
        objects_row.template_list(
            "UTMBUILDER_UL_element_list",
            "UTMBUILDER_elements_list",
            elements_group,
            "objects",
            elements_group,
            "active_element_index",
            rows = 4
        )

        objects_ops_column = objects_row.column()
        objects_addremove = objects_ops_column.column(align=True)
        add_object = objects_addremove.operator("utmbuilder.add_elements", text = "", icon = 'ADD')
        add_object.element_type = element_type
        remove_object = objects_addremove.operator("utmbuilder.remove_element", text = "", icon = 'REMOVE')
        remove_object.element_type = element_type

        objects_ops_column.separator()

        objects_move = objects_ops_column.column(align = True)
        move_down = objects_move.operator("utmbuilder.reorder_element", text = "", icon = 'EVENT_UP_ARROW')
        move_down.element_type = element_type
        move_down.up_down = False

        move_up = objects_move.operator("utmbuilder.reorder_element", text = "", icon = 'EVENT_DOWN_ARROW')
        move_up.element_type = element_type
        move_up.up_down = True

        select_column = layout.column(align = True)
        select_row = select_column.row(align = True)
        select_main = select_row.operator('utmbuilder.select_elements', text = "Select All", icon = 'CHECKBOX_HLT')
        select_main.mode = 'SELECT'
        select_main.element_type = "main_elements"
        deselect_main = select_row.operator('utmbuilder.select_elements', text = "Deselect All", icon = 'CHECKBOX_DEHLT')
        deselect_main.mode = 'DESELECT'
        deselect_main.element_type = "main_elements"

        elements_settings = select_column.operator("utmbuilder.element_settings", text = "Batch Segment Settings")
        elements_settings.element_type = element_type
        elements_settings.element_index = elements_group.active_element_index
        elements_settings.mode = 'BATCH'

    def draw(self, context):
        layout = self.layout
        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            return
        _, building = resolved

        # FLOORS:
        floors_box = layout.box()
        floors_label_row = floors_box.row()
        floors_label_row.scale_y = 1.5
        floors_label_row.label(text = "Floors:", icon = 'DISCLOSURE_TRI_RIGHT')

        refresh_row = floors_label_row.row(align = True)
        refresh_row.alignment = 'RIGHT'
        refresh_row.operator("utmbuilder.evaluate_building", text = "Refresh", icon = 'FILE_REFRESH')
        refresh_row.operator("utmbuilder.viewport_panel", text = "Live Edit", icon = 'MOD_TIME', depress = UTMBUILDER_OT_viewport_panel.is_running())

        floors_column = floors_box.column()
        floors_row = floors_column.row(align = True)
        floors_row.template_list(
            "UTMBUILDER_UL_floor_list",
            "UTMBUILDER_floor_list",
            building,
            "floors",
            building,
            "active_floor_index",
            rows = 4,
            maxrows = 10
        )

        if len(building.floors) <= 0:
            floors_column.label(text = "No floors added", icon = 'INFO')

        floors = building.floors
        floor_index = building.active_floor_index
        active_floor = floors[floor_index]

        floors_ops_column = floors_row.column()

        floors_addremove = floors_ops_column.column(align = True)
        floors_addremove.operator("utmbuilder.add_floor", text = "", icon = "ADD")
        floors_addremove.operator("utmbuilder.remove_floor", text = "", icon = "REMOVE")

        floors_ops_column.separator()
        floors_move = floors_ops_column.column(align = True)
        move_down = floors_move.operator("utmbuilder.reorder_floor", text = "", icon = 'EVENT_UP_ARROW')
        move_down.up_down = True
        move_down.floor_index = floor_index

        move_up = floors_move.operator("utmbuilder.reorder_floor", text = "", icon = 'EVENT_DOWN_ARROW')
        move_up.up_down = False
        move_up.floor_index = floor_index

        floors_ops_column.separator()
        floors_copy = floors_ops_column.column(align = True)
        copy_floor = floors_copy.operator("utmbuilder.copy_floor", text = "", icon = 'DUPLICATE',)
        copy_floor.floor_index = floor_index
        copy_floor.mode = "REALIZE" if active_floor.is_linked else "COPY"
        floors_copy.operator("utmbuilder.link_floor", text = "", icon = 'LINKED')

        if active_floor.is_linked == True:
            linked_box = layout.box()
            linked_column = linked_box.column()
            linked_column.alignment = 'CENTER'
            linked_column.label(text = "Floor is linked!", icon = "INFO")
            linked_column.label(text = "Refer to the floor" + str(active_floor.linked_ID) + "for settings")
            return

        stack_floors_column = floors_box.column(align = True)
        stack_row = stack_floors_column.row(align = True)
        stack_floors = stack_row.operator("utmbuilder.stack_curve_object", text = "Stack Floors", icon = 'TRIA_DOWN_BAR')
        stack_floors.property_to_stack = 'FLOORS'
        stack_curves = stack_row.operator("utmbuilder.stack_curve_object", text = "Stack Floors & Curves", icon = 'TRIA_DOWN_BAR')
        stack_curves.property_to_stack = 'CURVES'

        stack_row2 = stack_floors_column.row(align = True)
        stack_floor = stack_row2.operator("utmbuilder.stack_curve_object", text = "Stack Floor Curves", icon = 'TRIA_DOWN_BAR')
        stack_floor.property_to_stack = 'CURRENTFLOORCURVES'
        stack_curve = stack_row2.operator("utmbuilder.stack_curve_object", text = "Snap Curve", icon = 'TRIA_DOWN_BAR')
        stack_curve.property_to_stack = 'CURRENTCURVE'
        flatten = stack_floors_column.operator("utmbuilder.stack_curve_object", text = "Flatten current Floor", icon = 'TRIA_DOWN_BAR')
        flatten.property_to_stack = 'FLATTENFLOOR'


        # CURVES:
        curves_box = layout.box()

        curves_column = curves_box.column()
        curves_label_row = curves_column.row()
        curves_label_row.scale_y = 1.5
        curves_label_row.label(text = "Curves: ", icon = 'DISCLOSURE_TRI_RIGHT')

        refresh_row = curves_label_row.row(align = True)
        refresh_row.alignment = 'RIGHT'
        refresh_row.operator("utmbuilder.evaluate_building", text = "Refresh", icon = 'FILE_REFRESH')
        refresh_row.operator("utmbuilder.viewport_panel", text = "Live Edit", icon = 'MOD_TIME', depress = UTMBUILDER_OT_viewport_panel.is_running())

        curves_column.separator(factor = 1.0)
        curves_row = curves_column.row(align = True)
        curves_row.template_list(
            "UTMBUILDER_UL_curve_list",
            "UTMBUILDER_curve_list",
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
        curve_addremove.operator("utmbuilder.add_curve_object", text = "", icon = "ADD")
        curve_addremove.operator("utmbuilder.remove_curve_object", text = "", icon = "REMOVE")

        select_column = curves_box.column(align = True)
        select_row = select_column.row(align = True)
        select_segments = select_row.operator('utmbuilder.select_curves', text = "Select All", icon = 'CHECKBOX_HLT')
        select_segments.mode = 'SELECT'
        deselect_segments = select_row.operator('utmbuilder.select_curves', text = "Deselect All", icon = 'CHECKBOX_DEHLT')
        deselect_segments.mode = 'DESELECT'

        curve_settings = select_column.operator("utmbuilder.curve_settings", text = "Batch Segment Settings")
        curve_settings.curve_index = active_floor.active_curve_index
        curve_settings.mode = 'BATCH'

        if len(active_floor.curves) <= 0:
            curves_column.label(text = "No curves added", icon = 'INFO')
            return

        curves = active_floor.curves
        curve_index = active_floor.active_curve_index
        active_curve = curves[curve_index]


        # SEGMENTS:
        segments = active_curve.segments

        segments_box = layout.box()

        segments_label_row = segments_box.row()
        segments_label_row.scale_y = 1.5
        segments_box.label(text = "Segments: ", icon = 'DISCLOSURE_TRI_RIGHT')

        segments_list = segments_box.box()
        segments_row = segments_list.row(align = True)
        segments_row.prop(building, "show_segments_grid", text = "Show Segments Grid", icon = 'VIEW_ORTHO')
        segments_row.prop(building, "segments_grid_columns", text = "Columns", icon = 'GRIP_V')

        if building.show_segments_grid == True and len(segments) > 0:
            grid = segments_list.grid_flow(row_major = True, columns = building.segments_grid_columns)
            for segment in segments:
                icon = 'CHECKBOX_HLT' if segment.is_selected else 'CHECKBOX_DEHLT'
                seg_row = grid.row(align = True)
                seg_row.prop(segment, "is_selected", text = "", icon = icon)
                segment_settings = seg_row.operator("utmbuilder.segment_settings", text = str(segment.ID), depress = segment.is_selected)
                segment_settings.segment_index = segment.ID
                segment_settings.mode = 'SINGLE'

        select_column = segments_list.column(align = True)
        select_row = select_column.row(align = True)
        select_segments = select_row.operator('utmbuilder.select_segments', text = "Select All", icon = 'CHECKBOX_HLT')
        select_segments.mode = 'SELECT'
        deselect_segments = select_row.operator('utmbuilder.select_segments', text = "Deselect All", icon = 'CHECKBOX_DEHLT')
        deselect_segments.mode = 'DESELECT'

        segment_settings = select_column.operator("utmbuilder.segment_settings", text = "Batch Segment Settings")
        segment_settings.segment_index = active_curve.active_segment_index
        segment_settings.mode = 'BATCH'


        # Elements
        main_elements = active_curve.main_elements

        elements_box = layout.box()

        elements_label_row = elements_box.row()
        elements_label_row.scale_y = 1.5
        elements_label_row.label(text = "Main Elements: ", icon = 'DISCLOSURE_TRI_RIGHT')

        refresh_row = elements_label_row.row(align = True)
        refresh_row.alignment = 'RIGHT'
        refresh_row.operator("utmbuilder.evaluate_building", text = "Refresh", icon = 'FILE_REFRESH')
        refresh_row.operator("utmbuilder.viewport_panel", text = "Live Edit", icon = 'MOD_TIME', depress = UTMBUILDER_OT_viewport_panel.is_running())

        main_elements_column = elements_box.column()
        self.draw_collect_objects(main_elements_column, "main_elements", main_elements)


        # Corner Elements Settings:
        corner_elements = active_curve.corner_elements

        elements_box.separator()
        elements_box.label(text = "Corner Elements: ", icon = 'DISCLOSURE_TRI_RIGHT')

        corner_elements_column = elements_box.column()
        self.draw_collect_objects(corner_elements_column, "corner_elements", corner_elements)
            
        # Interval Elements Settings:
        #settings_box.separator()
        #settings_box.label(text = "Interval: ")

