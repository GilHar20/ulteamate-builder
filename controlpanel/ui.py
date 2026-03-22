import bpy



# -----------------------
# Buildings/Floors UIList
# -----------------------

class BLENDERRAIL_UL_building_list(bpy.types.UIList):
    """UIList for displaying buildings"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            name = item.name if item.name else (item.base_object.name if item.base_object else "- no base object -")
            row_icon = 'CHECKBOX_HLT' if item.base_object else 'CHECKBOX_DEHLT'
            layout.label(text = str(index + 1) + ": " + name, icon = row_icon)
            select_object = layout.operator("blenderrail.select_base_object", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
            select_object.building_index = index

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            name = item.name if item.name else (item.base_object.name if item.base_object else "-")
            layout.label(text = name, icon = 'CHECKBOX_HLT')



class BLENDERRAIL_UL_floor_list(bpy.types.UIList):
    """UIList for displaying displaying floors per building"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if len(item.curves) > 0:
                layout.label(text = str(index + 1) + ": " + str(len(item.curves)) + " curves", icon = 'CHECKBOX_HLT')
            else:
                layout.label(text = str(index + 1) + ": " + "- no floors -", icon = 'CHECKBOX_DEHLT')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text = str(len(item.curves)), icon = 'CHECKBOX_HLT')



class BLENDERRAIL_UL_curve_list(bpy.types.UIList):
    """UIList for displaying displaying curves per floor"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "curve_object", text = "", icon = 'CURVE_DATA')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text = str(len(item.curves)), icon = 'CHECKBOX_HLT')



class BLENDERRAIL_UL_segment_list(bpy.types.UIList):
    """UIList for displaying displaying segments per curve"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "element_ID", text = str(index + 1) + ": " + "segment")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text = str(len(item.curves)), icon = 'CHECKBOX_HLT')



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


    def draw_collect_objects(self, layout, collection_name, collection):
        row = layout.row()
        col = row.column(align=True)
        for item in collection:
            col.prop(item, "object", text="", placeholder="Object")
        buttons = row.column(align=True)
        add = buttons.operator("blenderrail.add_collect_object", text="", icon='ADD')
        add.collection_name = collection_name
        remove = buttons.operator("blenderrail.remove_collect_object", text="", icon='REMOVE')
        remove.collection_name = collection_name


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
        floor_index = active_building.active_floor_index
        floors = active_building.floors
        active_floor = floors[floor_index]
        curves = active_floor.curves
        curve_index = active_building.active_curve_index
        active_curve = curves[curve_index]

        buildings_box.template_list(
            "BLENDERRAIL_UL_building_list",
            "blenderrail_building_list",
            context.scene,
            "buildings",
            context.scene,
            "active_building_index",
            rows = 4
        )

        building_column = buildings_box.column(align = True)
        building_column.prop(active_building, "name", icon = 'FILE_FONT', text = "", placeholder = "Building Name")
        building_column.prop(active_building, "base_object", text = "", placeholder = "Base Object")
        building_column.operator("blenderrail.viewport_panel", text = "Enter Edit", icon = 'IMGDISPLAY')
        building_column.operator("blenderrail.evaluate_building", text = "Refresh", icon = 'FILE_REFRESH')


        collections_row = layout.row(align = True)
        

        # FLOORS:
        floors_box = collections_row.box()
        floors_row = floors_box.row(align = True)
        floors_row.template_list(
            "BLENDERRAIL_UL_floor_list",
            "blenderrail_floor_list",
            active_building,
            "floors",
            active_building,
            "active_floor_index",
            rows = 8,           
        )
        floors_column = floors_row.column(align = True)
        floors_column.operator("blenderrail.add_floor", text = "", icon = "ADD")
        remove = floors_column.operator("blenderrail.remove_floor", text = "", icon = "REMOVE")
        remove.floor_index = active_building.active_floor_index

        move_down = floors_column.operator("blenderrail.reorder_floor", text = "", icon = 'EVENT_UP_ARROW', emboss = False)
        move_down.up_down = False
        move_down.floor_index = floor_index

        move_up = floors_column.operator("blenderrail.reorder_floor", text = "", icon = 'EVENT_DOWN_ARROW', emboss = False)
        move_up.up_down = True
        move_up.floor_index = floor_index

        select_curve = floors_column.operator("blenderrail.select_floor_curves", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
        select_curve.floor_index = floor_index


        # CURVES:
        curves_box = collections_row.box()
        curves_row = curves_box.row(align = True)
        curves_row.template_list(
            "BLENDERRAIL_UL_curve_list",
            "blenderrail_curve_list",
            active_floor,
            "curves",
            active_building,
            "active_curve_index",
            rows = 8           
        )
        curves_column = curves_row.column(align = True)
        curves_column.operator("blenderrail.add_curve_object", text = "", icon = "ADD")
        curves_column.operator("blenderrail.remove_curve_object", text = "", icon = "REMOVE")


        # SEGMENTS:
        segments_box = collections_row.box()
        segments_row = segments_box.row(align = True)
        segments_row.template_list(
            "BLENDERRAIL_UL_segment_list",
            "blenderrail_segment_list",
            active_floor,
            "segments",
            active_building,
            "active_curve_index",
            rows = 8           
        )
        segments_column = segments_row.column(align = True)
        segments_column.operator("blenderrail.add_segment", text = "", icon = "ADD")
        segments_column.operator("blenderrail.remove_segment", text = "", icon = "REMOVE")



        '''
        active_floor_index = active_building.active_floor_index
        active_segment_index = active_building.active_segment_index
        level: int = 1

        for floor_index, floor in enumerate(floors):
            floor_row = floors_box.row(align = True)
            flooritemRow.alignment = 'LEFT'

            flooractivateIcon = "RADIOBUT_ON" if floor_index == active_floor_index else "RADIOBUT_OFF"

            activateFloor = flooritemRow.operator("blenderrail.set_active_indecies", text = "", icon = flooractivateIcon, emboss=False)
            activateFloor.floor_index = floor_index

            floor_label = str(level) + "- " + str(len(floor.segments)) + " segments" if len(floor.curves) > 0 else str(floor_index) + "- "
            floorExpandIcon = "TRIA_DOWN" if floor.is_open else "TRIA_RIGHT"
            flooritemRow.prop(floor, "is_open", text = floor_label, icon = floorExpandIcon, emboss = False)



            for array_level in range(floor.array - 1):
                level += 1
                flooritemRow = floors_box.row(align = True)
                flooritemRow.alignment = 'LEFT'
                floor_label = "       " + str(level) + "- " + "Floor array"
                flooritemRow.label(text = floor_label, icon = 'RADIOBUT_OFF')
                split = flooritemRow.operator("blenderrail.split_floor_array", text = "", icon = 'AREA_JOIN_DOWN')
                split.current_floor_index = floor_index
                split.level_index = array_level
            level += 1

            segmentsColumn = floors_box.column(align = True)
            if not floor.is_open:
                continue
            for segment in floor.segments:

                segmentRow = segmentsColumn.row(align = True)
                segmentRow.separator(factor = 2.0, type = 'LINE')

                segmentactivateIcon = "RADIOBUT_ON" if (floor_index == active_floor_index and segment.ID == active_segment_index) else "RADIOBUT_OFF"

                activateSegment = segmentRow.operator("blenderrail.set_active_indecies", text = "", icon = segmentactivateIcon, emboss = False)
                activateSegment.floor_index = floor_index
                activateSegment.segment_index = segment.ID

                segmentRow.label(text = "segment" + " #" + str(segment.ID))
                segmentRow.prop(segment, "element_ID", text = "Element ID")
        '''    

        settings_box = layout.box()

        # Floor Settings
        if floors and 0 <= floor_index < len(floors):
            floor_entry = floors[floor_index]

            settings_box.label(text = "Floor Settings: ")

            propertyColumn = settings_box.column(align = True)
            propertyColumn.prop(floor_entry, "array", text = "", icon = 'ANCHOR_BOTTOM')

        # Curve Settings
        if curves and 0 <= curve_index < len(curves):
            curve_entry = curves[curve_index]

            settings_box.separator()
            settings_box.label(text = "Curve Settings: ")

            property_column = settings_box.column(align = True)
            property_column.prop(curve_entry, "height", text = "", icon = 'ANCHOR_BOTTOM')

            # Main Elements Settings:
            settings_box.separator()
            settings_box.label(text = "Main: ")
            elementsColumn = settings_box.column(align = True)
            elementsColumn.prop(floor_entry, "element_method", text = "")
            if floor_entry.element_method == 'COLLECTION':
                elementsColumn.prop(floor_entry, "element_collection", text = "Collection", icon = 'OUTLINER_COLLECTION')
            else:
                self.draw_collect_objects(elementsColumn, "element_object", floor_entry.element_object)

            # Corner Elements Settings:
            settings_box.separator()
            settings_box.label(text = "Corners: ")

            # Interval Elements Settings:
            settings_box.separator()
            settings_box.label(text = "Interval: ")

