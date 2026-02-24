import bpy



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

        floors = context.scene.floors

        column = layout.column(align = True)
        row = column.row(align=True)
        row.operator("blenderrail.add_floor", text="Add Floor", icon="ADD")
        row.operator("blenderrail.remove_floor", text="Remove Floor", icon="REMOVE")

        row = column.row(align=True)
        row.operator("blenderrail.add_curve", text="Add Room", icon="ADD")
        row.operator("blenderrail.remove_curve", text="Remove Room", icon="REMOVE")

        layout.separator()

        if not floors or len(floors) == 0:
            layout.label(text = "No floors added")

        active_floor_index = context.scene.active_floor_index
        active_curve_index = context.scene.active_curve_index

        for i, floor in enumerate(floors):
            row = layout.row(align = True)

            row.separator(factor = 0.5)

            sel_icon = "RADIOBUT_ON" if i == active_floor_index else "RADIOBUT_OFF"
            op = row.operator("blenderrail.set_active_indecies", text = "", icon = sel_icon, emboss=False)
            op.floor_index = i
            icon = "TRIA_DOWN" if floor.is_open else "TRIA_RIGHT"
            row.prop(floor, "is_open", icon = icon, icon_only = True, emboss = False)
            row.prop(floor, "name", text = "Floor")

            if not floor.is_open:
                continue
                
            for j, curve in enumerate(floor.input_curve):
                sub = layout.row(align = True)

                sub.separator(factor = 2.0)

                r_icon = "RADIOBUT_ON" if (i == active_floor_index and j == active_curve_index) else "RADIOBUT_OFF"
                rop = sub.operator("blenderrail.set_active_indecies", text = "", icon = r_icon, emboss = False)
                rop.floor_index = i
                rop.curve_index = j
                sub.prop(curve, "name", text = "Room")
                sub.prop(curve, "element_ID", text = "ID")

        if floors and 0 <= active_floor_index < len(floors):
            floor_entry = floors[active_floor_index]

            box = layout.box()
            box.label(text = "works!")
            box.prop(floor_entry, "element_collection", text = "Elements", icon = 'COLLECTION')