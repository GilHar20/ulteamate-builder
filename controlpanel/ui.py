import bpy



# Todo: attempt to fix this method:
# https://blender.stackexchange.com/questions/213435/how-to-create-a-dynamic-ui-list-similar-to-the-outliner



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
            if item.curve:
                layout.label(text = str(index + 1) + ": " + item.curve.name, icon = 'CHECKBOX_HLT')
            else:
                layout.label(text = str(index + 1) + ": " + "- no curve assigned -", icon = 'CHECKBOX_DEHLT')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text = item.curve.name, icon = 'CHECKBOX_HLT')



# -----------------------------------------------------------------------------
# Fake tree panel (viewport sidebar, tab "blenderrail")
# -----------------------------------------------------------------------------

class BLENDERRAIL_PT_treeview(bpy.types.Panel):
    bl_label = "BlenderRail"
    bl_idname = "VIEW3D_PT_blenderrail_tree"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderRail"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        buildings = scene.buildings
        building_index = scene.active_building_index
        active_building = None

        buildingBox = layout.box()
        addbuildingRow = buildingBox.row()
        addbuildingRow.scale_y = 1.5
        addbuildingRow.operator("blenderrail.generate_building", text = "Add Building")
        buildingBox.operator("blenderrail.remove_building", text = "Remove Building")


        active_building = buildings[building_index]
        floors = active_building.floors

        if len(buildings) <= 0:
            floors = None

        buildingBox.template_list(
            "BLENDERRAIL_UL_building_list",
            "blenderrail_building_list",
            context.scene,
            "buildings",
            context.scene,
            "active_building_index",
            rows = 2
        )

        buildingColumn = buildingBox.column(align = True)
        buildingColumn.prop(active_building, "name", icon = 'FILE_FONT', text = "", placeholder = "Building Name")
        buildingColumn.prop(active_building, "base_object", text = "", placeholder = "Base Object")
        refreshColumn = buildingBox.column()
        refreshColumn.scale_y = 2
        refreshColumn.operator("blenderrail.evaluate_building", text = "Refresh", icon = 'FILE_REFRESH')


        floorsBox = layout.box()

        if active_building == None:
            floorsBox.label(text = "There are no buildings yet", icon = 'INFO')
            return

        '''
        floorsBox.template_list(
            "BLENDERRAIL_UL_floor_list",
            "blenderrail_floor_list",
            context.scene,
            "floors",
            context.scene,
            "active_floor_index",
            rows = 4           
        )
        '''

        floorColumn = floorsBox.column(align = True)
        floorRow = floorColumn.row(align = True)
        floorRow.operator("blenderrail.add_floor", text = "Add Floor", icon = "ADD")
        remove = floorRow.operator("blenderrail.remove_floor", text = "Remove Floor", icon = "REMOVE")
        remove.floor_index = active_building.active_floor_index
        segmentRow = floorsBox.row(align = True)
        segmentRow.operator("blenderrail.add_segment", text = "Add Segment", icon = "ADD")
        segmentRow.operator("blenderrail.remove_segment", text = "Remove Segment", icon = "REMOVE")


        floorsBox.separator()

        if len(floors) == 0:
            floorsBox.label(text = "No floors added")
            return

        active_floor_index = active_building.active_floor_index
        active_segment_index = active_building.active_segment_index

        for floor_index, floor in enumerate(floors):

            flooritemRow = floorsBox.row(align = True)
            flooritemRow.separator(factor = 0.5, type = 'SPACE')

            flooractivateIcon = "RADIOBUT_ON" if floor_index == active_floor_index else "RADIOBUT_OFF"

            activateFloor = flooritemRow.operator("blenderrail.set_active_indecies", text = "", icon = flooractivateIcon, emboss=False)
            activateFloor.floor_index = floor_index

            floor_label = str(floor_index) + "- " + floor.curve.name + ", " + str(len(floor.segments)) + " segments" if floor.curve else str(floor_index) + "- "
            floorExpandIcon = "TRIA_DOWN" if floor.is_open else "TRIA_RIGHT"
            flooritemRow.prop(floor, "is_open", text = floor_label, icon = floorExpandIcon, emboss = False)

            select_curve = flooritemRow.operator("blenderrail.select_floor_curve", text = "", icon = 'RESTRICT_SELECT_OFF', emboss = False)
            select_curve.floor_index = floor_index

            move_up = flooritemRow.operator("blenderrail.reorder_floor", text = "", icon = 'EVENT_DOWN_ARROW', emboss = False)
            move_up.up_down = True
            move_up.floor_index = floor_index

            move_down = flooritemRow.operator("blenderrail.reorder_floor", text = "", icon = 'EVENT_UP_ARROW', emboss = False)
            move_down.up_down = False
            move_down.floor_index = floor_index

            remove_self = flooritemRow.operator("blenderrail.remove_floor", text = "", icon = "REMOVE")
            remove_self.floor_index = floor_index

            segmentsColumn = floorsBox.column(align = True)


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
            

        if floors and 0 <= active_floor_index < len(floors):
            floor_entry = floors[active_floor_index]

            floorentryBox = floorsBox.box()

            floorentryBox.prop(floor_entry, "curve", text = "Input Curve", icon = 'CURVE_DATA')
            floorentryBox.prop(floor_entry, "height", icon = 'PMARKER_ACT')
            floorentryBox.prop(floor_entry, "array", icon = 'ANCHOR_BOTTOM')
            floorentryBox.prop(floor_entry, "element_method", text = "")

            if floor_entry.element_method == 'COLLECTION':
                floorentryBox.prop(floor_entry, "element_collection", text = "Collection", icon = 'OUTLINER_COLLECTION')

            else:
                objectsRow = floorentryBox.row()
                objectColumn = objectsRow.column(align = True)

                for object in floor_entry.element_object:
                    objectColumn.prop(object, "object", text = "", placeholder = "Object")

                objectAddRemove = objectsRow.column(align = True)
                objectAddRemove.operator("blenderrail.add_element_object", text = "", icon = 'ADD')
                objectAddRemove.operator("blenderrail.remove_element_object", text = "", icon = 'REMOVE')


