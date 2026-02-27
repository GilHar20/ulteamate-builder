import bpy



# Todo: attempt to fix this method:
# https://blender.stackexchange.com/questions/213435/how-to-create-a-dynamic-ui-list-similar-to-the-outliner



# -----------------------------------------------------------------------------
# Fake tree panel (viewport sidebar, tab "blenderrail")
# -----------------------------------------------------------------------------

class VIEW3D_PT_treeview(bpy.types.Panel):
    bl_label = "Fake Tree"
    bl_idname = "VIEW3D_PT_blenderrail_tree"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderRail"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        floors = scene.floors

        faketreeBox = layout.box()

        controlsColumn = faketreeBox.column(align = True)
        controlsColumn.alignment = 'CENTER'
        controlsColumn.scale_y = 1.5
        floorRow = controlsColumn.row(align = True)
        floorRow.operator("blenderrail.add_floor", text = "Add Floor", icon = "ADD")
        floorRow.operator("blenderrail.remove_floor", text = "Remove Floor", icon = "REMOVE")

        controlsColumn.operator("blenderrail.generate_building", text = "Generate!")

        faketreeBox.separator()

        if not floors or len(floors) == 0:
            faketreeBox.label(text = "No floors added")

        active_floor_index = scene.active_floor_index
        active_segment_index = scene.active_segment_index

        for floor_index, floor in enumerate(floors):

            flooritemRow = faketreeBox.row(align = True)
            flooritemRow.separator(factor = 0.5, type = 'SPACE')

            flooractivateIcon = "RADIOBUT_ON" if floor_index == active_floor_index else "RADIOBUT_OFF"

            activateFloor = flooritemRow.operator("blenderrail.set_active_indecies", text = "", icon = flooractivateIcon, emboss=False)
            activateFloor.floor_index = floor_index

            floorExpandIcon = "TRIA_DOWN" if floor.is_open else "TRIA_RIGHT"
            flooritemRow.prop(floor, "is_open", text = "Floor" + " #" + str(floor_index), icon = floorExpandIcon, emboss = False)

            segmentsColumn = faketreeBox.column(align = True)


            if not floor.is_open:
                continue
                
            for segment in floor.segments:

                segmentitemRow = segmentsColumn.row(align = True)
                segmentitemRow.separator(factor = 2.0, type = 'LINE')

                segmentactivateIcon = "RADIOBUT_ON" if (floor_index == active_floor_index and segment.ID == active_segment_index) else "RADIOBUT_OFF"

                activateSegment = segmentitemRow.operator("blenderrail.set_active_indecies", text = "", icon = segmentactivateIcon, emboss = False)
                activateSegment.floor_index = floor_index
                activateSegment.segment_index = segment.ID

                segmentitemRow.label(text = "segment" + " #" + str(segment.ID))
                segmentitemRow.prop(segment, "element_ID", text = "Element ID")
            

        if floors and 0 <= active_floor_index < len(floors):
            floor_entry = floors[active_floor_index]

            elementsBox = layout.box()

            elementsBox.prop(floor_entry, "curve", text = "Input Curve", icon = 'CURVE_DATA')
            elementsBox.prop(floor_entry, "element_method", text = "")

            if floor_entry.element_method == 'COLLECTION':
                elementsBox.prop(floor_entry, "element_collection", text = "Collection", icon = 'OUTLINER_COLLECTION')

            else:
                objectAddRemove = elementsBox.row(align = True)
                objectAddRemove.alignment = 'CENTER'
                objectAddRemove.operator("blenderrail.add_element_object", text = "", icon = 'ADD')
                objectAddRemove.operator("blenderrail.remove_element_object", text = "", icon = 'REMOVE')

                objectElements = elementsBox.column(align = True)

                for object in floor_entry.element_object:
                    objectElements.prop(object, "object", text = "", placeholder = "Object")
            elementsBox.prop(floor_entry, "height", icon = 'PMARKER_ACT')

            #box.operator("blenderrail.apply_floor_heights", text = "assign heights")