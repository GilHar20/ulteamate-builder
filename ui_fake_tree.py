# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import bpy


# -----------------------------------------------------------------------------
# Property groups: Room (child), Floor (parent with rooms)
# -----------------------------------------------------------------------------

class BlenderRailRoomItem(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(
        name = "Room",
        default = "Room")
    
    element_ID : bpy.props.IntProperty(
        name = "Element ID",
        default = 0,
        min = 0,
        max = 100
    )


class BlenderRailFloorItem(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(
        name = "Floor",
        default = "Floor")

    is_open : bpy.props.BoolProperty(
        name = "Open",
        default = False,
        description = "Show/hide rooms")
    
    rooms : bpy.props.CollectionProperty(
        type = BlenderRailRoomItem,
        name = "Rooms")


# -----------------------------------------------------------------------------
# Fake tree panel (viewport sidebar, tab "blenderrail")
# -----------------------------------------------------------------------------

class VIEW3D_PT_blenderrail_tree(bpy.types.Panel):
    bl_label = "Fake Tree"
    bl_idname = "VIEW3D_PT_blenderrail_tree"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "blenderrail"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        floors = getattr(scene, "blenderrail_floors", None)
        has_floors = floors and len(floors) > 0

        column = layout.column(align = True)
        row = column.row(align=True)
        row.operator("blenderrail.add_floor", text="Add Floor", icon="ADD")
        row.operator("blenderrail.remove_active_floor", text="Remove Floor", icon="REMOVE")

        row = column.row(align=True)
        row.enabled = has_floors
        row.operator("blenderrail.add_room_last_floor", text="Add Room", icon="ADD")
        row.operator("blenderrail.remove_active_room", text="Remove Room", icon="REMOVE")

        layout.separator()

        if not floors or len(floors) == 0:
            layout.label(text = "No floors added")

        active_floor_idx = getattr(scene, "blenderrail_active_floor_index", 0)
        active_room_idx = getattr(scene, "blenderrail_active_room_index", 0)

        for i, floor in enumerate(floors):
            row = layout.row(align = True)

            row.separator(factor = 0.5)

            sel_icon = "RADIOBUT_ON" if i == active_floor_idx else "RADIOBUT_OFF"
            op = row.operator("blenderrail.set_active_indecies", text = "", icon = sel_icon, emboss=False)
            op.floor_index = i
            icon = "TRIA_DOWN" if floor.is_open else "TRIA_RIGHT"
            row.prop(floor, "is_open", icon = icon, icon_only = True, emboss = False)
            row.prop(floor, "name", text = "Floor")

            if not floor.is_open:
                continue
                
            for j, room in enumerate(floor.rooms):
                sub = layout.row(align = True)

                sub.separator(factor = 2.0)

                r_icon = "RADIOBUT_ON" if (i == active_floor_idx and j == active_room_idx) else "RADIOBUT_OFF"
                rop = sub.operator("blenderrail.set_active_indecies", text = "", icon = r_icon, emboss = False)
                rop.floor_index = i
                rop.room_index = j
                sub.prop(room, "name", text = "Room")
                sub.prop(room, "element_ID", text = "ID")



# -----------------------------------------------------------------------------
# Operators: set active floor / room (so remove works on selection)
# -----------------------------------------------------------------------------

class BLENDERRAIL_OT_set_active_indecies(bpy.types.Operator):
    bl_idname = "blenderrail.set_active_indecies"
    bl_label = "Set Active Room"
    bl_options = {"REGISTER", "UNDO"}

    floor_index: bpy.props.IntProperty(options = {"HIDDEN"})
    room_index: bpy.props.IntProperty(options = {"HIDDEN"})

    def execute(self, context):
        context.scene.blenderrail_active_floor_index = self.floor_index
        context.scene.blenderrail_active_room_index = self.room_index
        return {"FINISHED"}


# -----------------------------------------------------------------------------
# Operators: add floor / remove active floor
# -----------------------------------------------------------------------------

class BLENDERRAIL_OT_add_floor(bpy.types.Operator):
    bl_idname = "blenderrail.add_floor"
    bl_label = "Add Floor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        floors = scene.blenderrail_floors
        floors.add()
        return {"FINISHED"}


class BLENDERRAIL_OT_remove_active_floor(bpy.types.Operator):
    bl_idname = "blenderrail.remove_active_floor"
    bl_label = "Remove Active Floor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        floors = scene.blenderrail_floors
        active = scene.blenderrail_active_floor_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors to remove")
            return {"CANCELLED"}
        
        if active < 0 or active >= len(floors):
            scene.blenderrail_active_floor_index = max(0, len(floors) - 1)
            self.report({"WARNING"}, "Active index out of range, adjusted")

        active = scene.blenderrail_active_floor_index
        floors.remove(active)
        # Clamp active so it stays valid
        scene.blenderrail_active_floor_index = min(active, max(0, len(floors) - 1))
        return {"FINISHED"}


# -----------------------------------------------------------------------------
# Operators: add / remove room on last floor
# -----------------------------------------------------------------------------

class BLENDERRAIL_OT_add_room_last_floor(bpy.types.Operator):
    bl_idname = "blenderrail.add_room_last_floor"
    bl_label = "Add Room to Last Floor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        floors = scene.blenderrail_floors
        floor_index = scene.blenderrail_active_floor_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors — add a floor first")
            return {"CANCELLED"}
        
        floor = floors[floor_index]
        room = floor.rooms.add()
        room.name = "Room"
        return {"FINISHED"}


class BLENDERRAIL_OT_remove_active_room(bpy.types.Operator):
    bl_idname = "blenderrail.remove_active_room"
    bl_label = "Remove Active Room"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        floors = getattr(scene, "blenderrail_floors", None)
        if not floors or len(floors) == 0:
            return False
        
        fi = scene.blenderrail_active_floor_index
        if fi < 0 or fi >= len(floors):
            return False
        
        rooms = floors[fi].rooms
        return len(rooms) > 0

    def execute(self, context):
        scene = context.scene
        floors = scene.blenderrail_floors
        fi = scene.blenderrail_active_floor_index
        ri = scene.blenderrail_active_room_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors")
            return {"CANCELLED"}
        
        if fi < 0 or fi >= len(floors):
            self.report({"WARNING"}, "Active floor index out of range")
            return {"CANCELLED"}
        
        rooms = floors[fi].rooms
        if len(rooms) == 0:
            self.report({"WARNING"}, "Active floor has no rooms")
            return {"CANCELLED"}
        
        if ri < 0 or ri >= len(rooms):
            scene.blenderrail_active_room_index = max(0, len(rooms) - 1)
            ri = scene.blenderrail_active_room_index

        rooms.remove(ri)
        # Clamp room index
        scene.blenderrail_active_room_index = min(ri, max(0, len(rooms) - 1))
        return {"FINISHED"}


# -----------------------------------------------------------------------------
# Registration: attach collection to Scene (classes are registered by auto_load)
# -----------------------------------------------------------------------------

def register():
    bpy.types.Scene.blenderrail_floors = bpy.props.CollectionProperty(type=BlenderRailFloorItem)
    bpy.types.Scene.blenderrail_active_floor_index = bpy.props.IntProperty(default = 0)
    bpy.types.Scene.blenderrail_active_room_index = bpy.props.IntProperty(default=0)


def unregister():
    del bpy.types.Scene.blenderrail_active_room_index
    del bpy.types.Scene.blenderrail_active_floor_index
    del bpy.types.Scene.blenderrail_floors
