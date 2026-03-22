import bpy
from . import operators



# ------------------------
# Property groups: Segment
# ------------------------

class BLENDERRAIL_PG_collect_objects(bpy.types.PropertyGroup):   
    object : bpy.props.PointerProperty(
        name = "Element Object",
        type = bpy.types.Object
    )


class BLENDERRAIL_PG_elements_collection(bpy.types.PropertyGroup):   
    collect_method : bpy.props.EnumProperty(
        name = "Collect Method",
        description = "Method of assigning elements to the Target Collection of the floor",
        items = [
        ('OBJECTS', "Objects", "Select objects and create a collection", 0),
        ('EXISTING', "Existing", "Choose existing Target Collection", 1),
        ],
        default = 'OBJECTS'
    )

    objects : bpy.props.CollectionProperty(
        name = "Element Object",
        description = "Objects to insert into the Tartget Collection",
        type = BLENDERRAIL_PG_collect_objects
    )

    existing_collection : bpy.props.PointerProperty(
        name = "Existing Collection",
        description = "Collection of objects to insert into the Tartget Collection",
        type = bpy.types.Collection
    )


    target_collection : bpy.props.PointerProperty(
        name = "Target Collection",
        description = "Collection of elements to instance along the curve splines",
        type = bpy.types.Collection
    )


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

    curve_ID : bpy.props.IntProperty(
        name = "Curve ID",
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


class BLENDERRAIL_PG_curve(bpy.types.PropertyGroup):
    def _update_total_height(self, context):
        operators._calculate_floors_start_height(context, None)
        return

    floor_ID : bpy.props.IntProperty(
        name = "Floor ID",
        default = 0,
        min = 0,
        max = 10000
    )

    height : bpy.props.FloatProperty(
        name = "Height",
        default = 3.4,
        min = 0.0,
        max = 100.0,
        update = _update_total_height
    )

    floor_ceiling : bpy.props.EnumProperty(
        name = "Floor Ceiling",
        description = "Select adding floor, ceiling or both",
        items = [
        ('NONE', "None", "None", 0),
        ('TOP', "Top", "Add ceiling", 1),
        ('BOTTOM', "Bottom", "Add floor", 2),
        ('BOTH', "Both", "Add ceiling and floor", 3),
        ],
        default = 'TOP'
    )

    curve_object : bpy.props.PointerProperty(
        name = "Input curve object",
        description = "Input curve geometry",
        type = bpy.types.Object
    )

    segments : bpy.props.CollectionProperty(
        name = "Segments",
        description = "Segments of the curve object",
        type = BLENDERRAIL_PG_segment
    )




class BLENDERRAIL_PG_floor(bpy.types.PropertyGroup):
    def _update_total_height(self, context):
        operators._calculate_floors_start_height(context, None)
        return

    def _update_element_method(self, context):
        operators._set_element_collection()
        return
    
    ID : bpy.props.IntProperty(
        name = "Building ID",
        default = 0,
        min = 0,
        max = 10000
    )

    array : bpy.props.IntProperty(
        name = "Floor Array",
        default = 1,
        min = 1,
        max = 1000,
        update = _update_total_height
    )

    total_height : bpy.props.FloatProperty(
        name = "Total Height",
        default = 0,
        min = 0.0,
        max = 10000.0
    )

    start_height : bpy.props.FloatProperty(
        name = "Total Height",
        default = 0,
        min = 0.0,
        max = 10000.0
    )

    curves : bpy.props.CollectionProperty(
        name = "Input curve object",
        description = "Input curve geometry",
        type = BLENDERRAIL_PG_curve
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
        type = BLENDERRAIL_PG_collect_objects
    )

    '''
    main_elements : bpy.props.CollectionProperty(
        name = "Main Elements",
        description = "Collection of main elements",
        type = BLENDERRAIL_PG_elements_collection
    )

    corner_elements : bpy.props.CollectionProperty(
        name = "Main Elements",
        description = "Collection of main elements",
        type = BLENDERRAIL_PG_elements_collection
    )

    interval_elements : bpy.props.CollectionProperty(
        name = "Main Elements",
        description = "Collection of main elements",
        type = BLENDERRAIL_PG_elements_collection
    )
    '''


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

    active_curve_index : bpy.props.IntProperty(
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

    active_element_index : bpy.props.IntProperty(
        name = "Active Floor Index",
        default = 0,
        min = 0,
        max = 10000
    )



# --------------------------------
# Property Group Actions Operators
# --------------------------------

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
# Operators: Floor Operators
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
        active_floor_index = building.active_floor_index

        if len(floors) == 0:
            floors.add()
        else:
            floors.add()
            floors.move(len(floors) - 1, active_floor_index + 1)
            building.active_floor_index = active_floor_index + 1

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
    bl_description = "Move the floor up or down the list (True for down the list, false for up)"
    bl_options = {"REGISTER", "UNDO"}

    floor_index : bpy.props.IntProperty(options = {"HIDDEN"})
    up_down : bpy.props.BoolProperty(
        name = "Up Down",
        description = " Switches between moving floor up or dowm the list (True for down the list, false for up)",
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


class BLENDERRAIL_OT_select_floor_curves(bpy.types.Operator):
    bl_idname = "blenderrail.select_floor_curves"
    bl_label = "Select Floor Curve"
    bl_description = "Select the curve object assigned to the floor"
    bl_options = {"REGISTER", "UNDO"}

    floor_index : bpy.props.IntProperty(options = {"HIDDEN"})
    curve_index : bpy.props.IntProperty(default = -1 ,options = {"HIDDEN"})

    def _select_set(self, context, curves):
        if self.curve_index != -1:
            context.view_layer.objects.active = curves[self.curve_index].object
            curves[self.curve_index].object.select_set(True)
            return

        context.view_layer.objects.active = curves[0].object
        for curve in curves:
            curve.object.select_set(True)
        return

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        active_floor_index = building.active_floor_index
        curves = building.floors[active_floor_index].curves
        curve_objects = [curve for curve in curves if curve.curve_object is not None]

        if len(curve_objects) == 0:
            self.report({'INFO'}, "No curve objects assigned")
            return{"CANCELLED"}

        if context.mode == 'EDIT_MESH':
            self.report({'WARNING'}, "Cannot select curve while in mesh edit mode")
            return {"CANCELLED"}
            
        elif context.mode == 'EDIT_CURVE':
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            self._select_set(context, curve_objects)
            bpy.ops.object.mode_set(mode='EDIT')

        elif context.mode == 'OBJECT':
            bpy.ops.object.select_all(action='DESELECT')
            self._select_set(context, curve_objects)

        return{"FINISHED"}



class BLENDERRAIL_OT_split_floor_array(bpy.types.Operator):
    bl_idname = "blenderrail.split_floor_array"
    bl_label = "Split Floor Array"
    bl_description = "Split the floor array in a given position into to floors with the same curve object and the correct array amount"
    bl_options = {"REGISTER", "UNDO"}

    current_floor_index : bpy.props.IntProperty(options = {"HIDDEN"})
    level_index : bpy.props.IntProperty(options = {"HIDDEN"})

    def _copy_curve(self, current_floor, new_floor):
        curve_objects = [obj for obj in current_floor.curves.curve_object if obj is not None]
        for curve_object in curve_objects:
            new_curve = curve_object.copy()
            new_curve.data = curve_object.data.copy()
            curve_object.users_collection[0].objects.link(new_curve)
            new_floor.curves.add().object = new_curve

    def execute(self, context):
        scene = context.scene
        floors = scene.buildings[scene.active_building_index].floors
        current_floor = floors[self.current_floor_index]
        current_floor_array: int = current_floor.array

        floors.add()
        floors.move(len(floors) - 1, self.current_floor_index + 1)
        new_floor = floors[self.current_floor_index + 1]
        current_floor.array = self.level_index + 1
        new_floor.array = current_floor_array - self.level_index - 1

        self._copy_curve(current_floor, new_floor)

        skip_props = {'rna_type', 'name', 'array', 'curves'}
        for prop in current_floor.bl_rna.properties:
            if prop.identifier in skip_props:
                continue
            if prop.type == 'COLLECTION':
                src_collection = getattr(current_floor, prop.identifier)
                dst_collection = getattr(new_floor, prop.identifier)
                for src_item in src_collection:
                    dst_item = dst_collection.add()
                    for item_prop in src_item.bl_rna.properties:
                        if item_prop.identifier == 'rna_type':
                            continue
                        setattr(dst_item, item_prop.identifier, getattr(src_item, item_prop.identifier))
            else:
                setattr(new_floor, prop.identifier, getattr(current_floor, prop.identifier))
        
        bpy.ops.blenderrail.evaluate_building()

        return {"FINISHED"}



# --------------------------------
# Operators: add / remove segments
# --------------------------------

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
    


# ------------------------------
# Operators: add / remove curves
# ------------------------------

class BLENDERRAIL_OT_add_curve_object(bpy.types.Operator):
    bl_idname = "blenderrail.add_curve_object"
    bl_label = "Add Curve"
    bl_description = "Add a curve object to the active floor"
    bl_options = {"REGISTER", "UNDO"}


    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor = floors[building.active_floor_index]
        curves = floor.curves
        active_curve_index = building.active_curve_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors — add a floor first")
            return {"CANCELLED"}

        if len(curves) == 0:
            curves.add()
            building.active_curve_index = 0
        else:
            curves.add()

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_curve_object(bpy.types.Operator):
    bl_idname = "blenderrail.remove_curve_object"
    bl_label = "Remove Curve"
    bl_description = "Remove a curve object from the active floor"
    bl_options = {"REGISTER", "UNDO"}


    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor = floors[building.active_floor_index]
        curves = floor.curves

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors")
            return {"CANCELLED"}

        if len(curves) == 0:
            self.report({"WARNING"}, "No curve rows to remove")
            building.active_curve_index = 0
            return {"CANCELLED"}

        curves.remove(len(curves) - 1)

        return {"FINISHED"}



# --------------------------------------
# Operators: add / remove collect object
# --------------------------------------

class BLENDERRAIL_OT_add_collect_object(bpy.types.Operator):
    bl_idname = "blenderrail.add_collect_object"
    bl_label = "Add Collect Object"
    bl_options = {"REGISTER", "UNDO"}

    collection_name : bpy.props.StringProperty(options = {"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        collection = getattr(floor, self.collection_name)

        collection.add()

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_collect_object(bpy.types.Operator):
    bl_idname = "blenderrail.remove_collect_object"
    bl_label = "Remove Collect Object"
    bl_options = {"REGISTER", "UNDO"}

    collection_name : bpy.props.StringProperty(options = {"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        collection = getattr(floor, self.collection_name)

        if len(collection) == 0:
            self.report({"WARNING"}, "No objects to remove")
            return {"CANCELLED"}

        collection.remove(len(collection) - 1)

        return {"FINISHED"}
