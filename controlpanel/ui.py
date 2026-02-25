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
        floorRow = controlsColumn.row(align = True)
        floorRow.operator("blenderrail.add_floor", text="Add Floor", icon="ADD")
        floorRow.operator("blenderrail.remove_floor", text="Remove Floor", icon="REMOVE")

        #curveRow = controlsColumn.row(align=True)
        #curveRow.operator("blenderrail.add_curve", text="Add Room", icon="ADD")
        #curveRow.operator("blenderrail.remove_curve", text="Remove Room", icon="REMOVE")

        faketreeBox.separator()

        if not floors or len(floors) == 0:
            faketreeBox.label(text = "No floors added")

        active_floor_index = scene.active_floor_index
        active_curve_index = scene.active_curve_index

        for i, floor in enumerate(floors):

            flooritemRow = faketreeBox.row(align = True)
            flooritemRow.separator(factor = 0.5)

            flooractivateIcon = "RADIOBUT_ON" if i == active_floor_index else "RADIOBUT_OFF"

            activateFloor = flooritemRow.operator("blenderrail.set_active_indecies", text = "", icon = flooractivateIcon, emboss=False)
            activateFloor.floor_index = i

            floorExpandIcon = "TRIA_DOWN" if floor.is_open else "TRIA_RIGHT"
            flooritemRow.prop(floor, "is_open", text = "#" + str(i) + " Floor", icon = floorExpandIcon, emboss = False)
            #flooritemRow.prop(floor, "name", text = "#" + str(i) + " Floor")

            '''
            if not floor.is_open:
                continue
                
            for j, curve in enumerate(floor.input_curve):

                curveitemRow = layout.row(align = True)
                curveitemRow.separator(factor = 2.0)

                curveactivateIcon = "RADIOBUT_ON" if (i == active_floor_index and j == active_curve_index) else "RADIOBUT_OFF"

                activateCurve = curveitemRow.operator("blenderrail.set_active_indecies", text = "", icon = curveactivateIcon, emboss = False)
                activateCurve.floor_index = i
                activateCurve.curve_index = j

                curveitemRow.prop(curve, "name", text = "Room")
                curveitemRow.prop(curve, "element_ID", text = "ID")
            '''


        if floors and 0 <= active_floor_index < len(floors):
            floor_entry = floors[active_floor_index]

            box = layout.box()

            box.prop(floor_entry, "curve", text = "Input Curve", icon = 'CURVE_DATA')
            box.prop(floor_entry, "element_collection", text = "Elements", icon = 'OUTLINER_COLLECTION')