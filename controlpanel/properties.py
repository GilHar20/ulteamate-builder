import bpy



# ------------------------
# Property groups: Segment
# ------------------------

class BLENDERRAIL_PG_segment(bpy.types.PropertyGroup):   
    def _element_ID_update(self, context):
        """While technically works, quite heavy on preformance."""
        bpy.context.view_layer.update()
        return
    
    ID : bpy.props.IntProperty(
        name = "Segment ID",
        default = 0,
        min = 0,
        max = 10000
    )

    spline_ID : bpy.props.IntProperty(
        name = "Spline ID",
        default = 0,
        min = 0,
        max = 10000
    )

    spline_factor : bpy.props.FloatProperty(
        name = "Curve Factor",
        default = 0.0,
        min = 0.0,
        max = 1.0
    )

    element_ID : bpy.props.IntProperty(
        name = "Element ID",
        default = 0,
        min = 0,
        max = 10000
        #update = _element_ID_update
    )



# ------------------------
# Property groups: Objects
# ------------------------

class BLENDERRAIL_PG_elements_objects(bpy.types.PropertyGroup):   
    object : bpy.props.PointerProperty(
        name = "Element Object",
        type = bpy.types.Object
    )



# ----------------------
# Property groups: Floor
# ----------------------

class BLENDERRAIL_PG_floor(bpy.types.PropertyGroup):
    ID : bpy.props.IntProperty(
        name = "Building ID",
        default = 0,
        min = 0,
        max = 10000
    )

    is_open : bpy.props.BoolProperty(
        name = "Open",
        default = False,
        description = "Show/hide rooms")

    height : bpy.props.FloatProperty(
        name = "Height",
        default = 3.4,
        min = 0.0,
        max = 100.0
    )

    total_height : bpy.props.FloatProperty(
        name = "Total Height",
        default = 0,
        min = 0.0,
        max = 10000.0
    )

    curve : bpy.props.PointerProperty(
        name = "Input curve object",
        description = "Input curve geometry",
        type = bpy.types.Object
    )

    array : bpy.props.IntProperty(
        name = "Floor Array",
        default = 1,
        min = 1,
        max = 1000
    )

    segments : bpy.props.CollectionProperty(
        name = "Segments",
        description = "Segments of the curve object",
        type = BLENDERRAIL_PG_segment
    )

    element_method : bpy.props.EnumProperty(
        name = "Element Method",
        description = "Method of assigning elements to the floor",
        items = [
        ('COLLECTION', "Collection", "Input collection", 0),
        ('OBJECTS', "Objects", "Select objects", 1),
        ],
        default = 'COLLECTION'
    )

    element_collection : bpy.props.PointerProperty(
        name = "Elements Collection",
        description = "Collection of elements to instance along the floor spline.",
        type = bpy.types.Collection
    )

    element_object : bpy.props.CollectionProperty(
        name = "Segments",
        description = "Element to assign to the floor",
        type = BLENDERRAIL_PG_elements_objects
    )



# -------------------------
# Property groups: Building
# -------------------------

class BLENDERRAIL_PG_building(bpy.types.PropertyGroup):
    def _update_base_object_name(self, context):
        object = self.base_object
        object.name = self.name + "_Constructor"
        return
    
    ID : bpy.props.IntProperty(
        name = "Building ID",
        default = 0,
        min = 0,
        max = 10000
    )

    name : bpy.props.StringProperty(
        name = "Building Name",
        description = "Name of the building",
        default = "",
        update = _update_base_object_name
    )
    
    base_object : bpy.props.PointerProperty(
        name = "Building",
        description = "Input base geometry to hold the constract modifier",
        type = bpy.types.Object
    )

    floors : bpy.props.CollectionProperty(
        name = "Floors",
        description = "List of all the floors in the building",
        type = BLENDERRAIL_PG_floor
    )

    active_floor_index : bpy.props.IntProperty(
        name = "Active Floor Index",
        default = 0,
        min = 0,
        max = 10000
    )

    active_segment_index : bpy.props.IntProperty(
        name = "Active Segment Index",
        default = 0,
        min = 0,
        max = 10000
    )



# -----------------------------------------------------------------------------
# Operators: set active floor / room (so remove works on selection)
# -----------------------------------------------------------------------------

class BLENDERRAIL_OT_set_active_indecies(bpy.types.Operator):
    bl_idname = "blenderrail.set_active_indecies"
    bl_label = "Set Active Segment"
    bl_options = {"REGISTER", "UNDO"}

    floor_index : bpy.props.IntProperty(options = {"HIDDEN"})
    segment_index : bpy.props.IntProperty(options = {"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        buildings = scene.buildings
        building_index = scene.active_building_index
        building = buildings[building_index]

        building.active_floor_index = self.floor_index
        building.active_segment_index = self.segment_index

        return {"FINISHED"}



# ---------------------------------
# Operators: active floor operators
# ---------------------------------

class BLENDERRAIL_OT_add_floor(bpy.types.Operator):
    bl_idname = "blenderrail.add_floor"
    bl_label = "Add Floor"
    bl_description = "Add floor to the list right after the active one"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor_index = building.active_floor_index

        if len(floors) == 0:
            floors.add()
        else:
            floors.add()
            floors.move(len(floors) - 1, floor_index + 1)
            building.active_floor_index = floor_index + 1

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_floor(bpy.types.Operator):
    bl_idname = "blenderrail.remove_floor"
    bl_label = "Remove Active Floor"
    bl_description = "Delete the active floor"
    bl_options = {"REGISTER", "UNDO"}

    floor_index : bpy.props.IntProperty(options = {"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor_index = self.floor_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors to remove")
            building.active_floor_index = 0
            return {"CANCELLED"}

        floors.remove(floor_index)
        building.active_floor_index = min(floor_index, max(0, len(floors) - 1))
        return {"FINISHED"}


class BLENDERRAIL_OT_reorder_floor(bpy.types.Operator):
    bl_idname = "blenderrail.reorder_floor"
    bl_label = "Reorder Floor"
    bl_description = "Move the floor up and down the list"
    bl_options = {"REGISTER", "UNDO"}

    floor_index : bpy.props.IntProperty(options = {"HIDDEN"})
    up_down : bpy.props.BoolProperty(
        name = "Up Down",
        description = " Switches between moving floor up or dowm the list",
        default = True)

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors

        if self.floor_index == 0 and self.up_down == False:
            self.report({"INFO"}, "Floor is the first item in the list")
            return{"CANCELLED"}

        if self.floor_index == len(floors) - 1 and self.up_down == True:
            self.report({"INFO"}, "Floor is the last item in the list")
            return{"CANCELLED"}
        
        if self.up_down == True:
            floors.move(self.floor_index, self.floor_index + 1)
        else:
            floors.move(self.floor_index, self.floor_index - 1)

        return {"FINISHED"}


class BLENDERRAIL_OT_select_floor_curve(bpy.types.Operator):
    bl_idname = "blenderrail.select_floor_curve"
    bl_label = "Select Floor Curve"
    bl_description = "Select the curve object assigned to the floor"
    bl_options = {"REGISTER", "UNDO"}

    floor_index : bpy.props.IntProperty(options = {"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        object = scene.buildings[scene.active_building_index].floors[self.floor_index].curve

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = object
        object.select_set(True)

        return{"FINISHED"}



# ------------------------------
# Operators: add / remove segments
# ------------------------------

class BLENDERRAIL_OT_add_segment(bpy.types.Operator):
    bl_idname = "blenderrail.add_segment"
    bl_label = "Add Segment to Floor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor_index = building.active_floor_index
        segment_index = building.active_segment_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors added")
            return {"CANCELLED"}
        
        floor = floors[floor_index]
        floor.is_open = True

        if len(floor.segments) == 0:
            floor.segments.add()

        else:
            floor.segments.add()
            floor.segments.move(len(floor.segments) - 1, segment_index + 1)
            building.active_segment_index = segment_index + 1

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_segment(bpy.types.Operator):
    bl_idname = "blenderrail.remove_segment"
    bl_label = "Remove Active Segment"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor_index = building.active_floor_index
        segment_index = building.active_segment_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors")
            return {"CANCELLED"}
        
        segments = floors[floor_index].segments
        if len(segments) == 0:
            self.report({"WARNING"}, "Active floor has no segments")
            return {"CANCELLED"}
        
        if segment_index < 0 or segment_index >= len(segments):
            building.active_segment_index = max(0, len(segments) - 1)
            segment_index = building.active_segment_index

        segments.remove(segment_index)
        building.active_segment_index = min(segment_index, max(0, len(segments) - 1))
        return {"FINISHED"}
    


    # ----------------------------------------
# Operators: add floor / remove element object
# --------------------------------------------

class BLENDERRAIL_OT_add_element_object(bpy.types.Operator):
    bl_idname = "blenderrail.add_element_object"
    bl_label = "Add Element Object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        element_objects = floors[building.active_floor_index].element_object

        element_objects.add()

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_element_object(bpy.types.Operator):
    bl_idname = "blenderrail.remove_element_object"
    bl_label = "Remove Element Object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        element_objects = floors[building.active_floor_index].element_object

        if len(element_objects) == 0:
            self.report({"WARNING"}, "No objects to remove")
            return {"CANCELLED"}

        element_objects.remove(len(element_objects) - 1)

        return {"FINISHED"}
