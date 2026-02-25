import bpy



# -----------------------------------------------------------------------------
# Property groups: Room (child), Floor (parent with rooms)
# -----------------------------------------------------------------------------

class BLENDERRAIL_PG_RoomItem(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(
        name = "Room",
        default = "Room")
    
    element_ID : bpy.props.IntProperty(
        name = "Element ID",
        default = 0,
        min = 0,
        max = 100
    )


class BLENDERRAIL_PG_FloorItem(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(
        name = "Floor",
        default = "Floor")

    is_open : bpy.props.BoolProperty(
        name = "Open",
        default = False,
        description = "Show/hide rooms")
    
    curve : bpy.props.PointerProperty(
        name = "Input curve object",
        description = "Input curve geometry",
        type = bpy.types.Object
    )
    
    element_collection : bpy.props.PointerProperty(
        name = "Elements Collection",
        description = "Collection of elements to instance along the floor spline.",
        type = bpy.types.Collection
    )

    '''
    input_curve : bpy.props.CollectionProperty(
    name = "Rooms",
    description = "Floor input properties",
    type = BLENDERRAIL_PG_RoomItem
    )
    '''


# -----------------------------------------------------------------------------
# Operators: set active floor / room (so remove works on selection)
# -----------------------------------------------------------------------------

class BLENDERRAIL_OT_set_active_indecies(bpy.types.Operator):
    bl_idname = "blenderrail.set_active_indecies"
    bl_label = "Set Active Room"
    bl_options = {"REGISTER", "UNDO"}

    floor_index : bpy.props.IntProperty(options = {"HIDDEN"})
    curve_index : bpy.props.IntProperty(options = {"HIDDEN"})

    def execute(self, context):
        context.scene.active_floor_index = self.floor_index
        context.scene.active_curve_index = self.curve_index
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
        floors = scene.floors
        floor_index = scene.active_floor_index

        if len(floors) == 0:
            floors.add()

        else:
            floors.add()
            floors.move(len(floors) - 1, floor_index + 1)
            scene.active_floor_index = floor_index + 1

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_floor(bpy.types.Operator):
    bl_idname = "blenderrail.remove_floor"
    bl_label = "Remove Active Floor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        floors = scene.floors
        floor_index = scene.active_floor_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors to remove")
            scene.active_floor_index = 0
            return {"CANCELLED"}
        
        if floor_index < 0 or floor_index >= len(floors):
            scene.active_floor_index = max(0, len(floors) - 1)
            self.report({"WARNING"}, "Active index out of range, adjusted")

        floors.remove(floor_index)
        # Clamp active so it stays valid
        scene.active_floor_index = min(floor_index, max(0, len(floors) - 1))
        return {"FINISHED"}


# ------------------------------
# Operators: add / remove curves
# ------------------------------

class BLENDERRAIL_OT_add_curve(bpy.types.Operator):
    bl_idname = "blenderrail.add_curve"
    bl_label = "Add Room to Last Floor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        floors = scene.floors
        floor_index = scene.active_floor_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors added")
            return {"CANCELLED"}
        
        floor = floors[floor_index]
        floor.is_open = True

        curve = floor.input_curve.add()
        curve.name = "Room"

        #TODO: Make the last added the active index
        #TODO: Add new not as last, but right after active
        return {"FINISHED"}


class BLENDERRAIL_OT_remove_curve(bpy.types.Operator):
    bl_idname = "blenderrail.remove_curve"
    bl_label = "Remove Active Room"
    bl_options = {"REGISTER", "UNDO"}


    def execute(self, context):
        scene = context.scene
        floors = scene.floors
        floor_index = scene.active_floor_index
        curve_index = scene.active_curve_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors")
            return {"CANCELLED"}
        
        if floor_index < 0 or floor_index >= len(floors):
            self.report({"WARNING"}, "Active floor index out of range")
            return {"CANCELLED"}
        
        input_curves = floors[floor_index].input_curve
        if len(input_curves) == 0:
            self.report({"WARNING"}, "Active floor has no rooms")
            return {"CANCELLED"}
        
        if curve_index < 0 or curve_index >= len(input_curves):
            scene.active_curve_index = max(0, len(input_curves) - 1)
            curve_index = scene.active_curve_index

        input_curves.remove(curve_index)
        # Clamp room index
        scene.active_curve_index = min(curve_index, max(0, len(input_curves) - 1))
        return {"FINISHED"}



