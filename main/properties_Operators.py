import bpy
from . import operators
from ..preferences import find_node_group



# ---------------------------------
# Operators: Floor Operators
# ---------------------------------

class BLENDERRAIL_OT_add_floor(bpy.types.Operator):
    bl_idname = "blenderrail.add_floor"
    bl_label = "Add Floor"
    bl_description = "Add floor to the list right after the active one"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        active_floor_index = building.active_floor_index

        if len(floors) == 0:
            new_floor = floors.add()
            new_floor.ID = 0
            return{"FINISHED"}

        else:
            floors.add()
            floors.move(len(floors) - 1, active_floor_index + 1)
            building.active_floor_index = active_floor_index + 1
            new_floor = floors[building.active_floor_index]

        new_floor.ID = building.active_floor_index
        new_floor.curves_collection = bpy.data.collections.new(building.name + "_Floor" + str(new_floor.ID))
        new_floor.curves_collection.color_tag = building.floors_collection.color_tag
        building.floors_collection.children.link(new_floor.curves_collection)

        if len(floors) <= 2:
            return{"FINISHED"}
        
        for index, floor in enumerate(floors):
            floor.ID = floor.ID + 1 if index > building.active_floor_index else floor.ID
            floor.curves_collection.name = building.name + "_Floor" + str(floor.ID)

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_floor(bpy.types.Operator):
    bl_idname = "blenderrail.remove_floor"
    bl_label = "Remove Active Floor"
    bl_description = "Delete the active floor"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor = floors[building.active_floor_index]
        floor_index = building.active_floor_index

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors to remove")
            building.active_floor_index = 0
            return {"CANCELLED"}

        if floor.curves_collection:
            bpy.data.collections.remove(floor.curves_collection)
        floors.remove(building.active_floor_index)

        building.active_floor_index = min(floor_index, max(0, len(floors) - 1))

        for index, floor in enumerate(floors):
            floor.ID = index
            floor.curves_collection.name = building.name + "_Floor" + str(floor.ID)

        return {"FINISHED"}


class BLENDERRAIL_OT_reorder_floor(bpy.types.Operator):
    bl_idname = "blenderrail.reorder_floor"
    bl_label = "Reorder Floor"
    bl_description = "Move the floor up or down the list (True for down the list, false for up)"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

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
            moved_floor = floors[self.floor_index + 1]
            pushed_floor = floors[self.floor_index]
            moved_floor.ID += 1
            moved_floor.collection.name = building.name + "_Floor" + str(moved_floor.ID)
            pushed_floor.ID -= 1
            moved_floor.collection.name = building.name + "_Floor" + str(moved_floor.ID)
        else:
            floors.move(self.floor_index, self.floor_index - 1)
            moved_floor = floors[self.floor_index - 1]
            pushed_floor = floors[self.floor_index]
            moved_floor.ID -= 1
            moved_floor.collection.name = building.name + "_Floor" + str(moved_floor.ID)
            pushed_floor.ID += 1
            moved_floor.collection.name = building.name + "_Floor" + str(moved_floor.ID)
        return {"FINISHED"}


class BLENDERRAIL_OT_select_floor_curves(bpy.types.Operator):
    bl_idname = "blenderrail.select_floor_curves"
    bl_label = "Select Floor Curve"
    bl_description = "Select the curve object assigned to the floor"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    floor_index : bpy.props.IntProperty(default = -1, options = {"HIDDEN"})
    curve_index : bpy.props.IntProperty(default = -1, options = {"HIDDEN"})

    def _select_set(self, context, curve_items):
        if self.curve_index > -1:
            context.view_layer.objects.active = curve_items[self.curve_index].curve_object
            curve_items[self.curve_index].curve_object.select_set(True)
            return

        context.view_layer.objects.active = curve_items[0].curve_object
        for curve in curve_items:
            curve.curve_object.select_set(True)
        return

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        if self.floor_index == -1:
            active_floor_index = building.active_floor_index
        else:
            active_floor_index = self.floor_index
        curves = building.floors[active_floor_index].curves
        curve_items = [curve for curve in curves if curve.curve_object is not None]

        if len(curve_items) == 0:
            self.report({'INFO'}, "No curve objects assigned")
            return{"CANCELLED"}

        if context.mode == 'EDIT_MESH':
            self.report({'WARNING'}, "Cannot select curve while in mesh edit mode")
            return {"CANCELLED"}
            
        elif context.mode == 'EDIT_CURVE':
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            self._select_set(context, curve_items)
            bpy.ops.object.mode_set(mode='EDIT')

        elif context.mode == 'OBJECT':
            bpy.ops.object.select_all(action='DESELECT')
            self._select_set(context, curve_items)

        return{"FINISHED"}


class BLENDERRAIL_OT_link_floor(bpy.types.Operator):
    bl_idname = "blenderrail.link_floor"
    bl_label = "Link Floor"
    bl_description = "Create a new floor entry with all settings linked to the original"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}    


    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        
        floor_index = building.active_floor_index
        floor = floors[floor_index]
        if floor.is_linked == True:
            self.report({"ERROR"}, "Cannot link an already linked floor! Please select original floor")
            return{"FINISHED"}

        bpy.ops.blenderrail.add_floor()
        new_floor = floors[building.active_floor_index]
        if not new_floor.curves_collection:
            self.report({"ERROR"}, "There is no collection to the floor. Current floor: " + str(building.active_floor_index))
            return{"FINISHED"}
        new_floor.is_linked = True

        for index, curve in enumerate(floor.curves):
            bpy.ops.blenderrail.add_curve_object()
            new_curve = new_floor.curves[index]

            bpy.ops.curve.primitive_bezier_circle_add(enter_editmode = False, align = 'WORLD', location = context.scene.cursor.location, scale = (1, 1, 1))
            curve_obj = context.view_layer.objects.active
            new_floor.curves_collection.objects.link(curve_obj)
            context.scene.collection.objects.unlink(curve_obj)

            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = building.base_object
            building.base_object.select_set(True)
            curve_obj.select_set(True)
            bpy.ops.object.parent_no_inverse_set(keep_transform = True)
            curve_obj.location = curve.curve_object.location

            new_curve.curve_object = curve_obj
            curve_attributes = curve_obj.modifiers.new(name = "BLENDERRAIL_LinkFloor_GN", type = "NODES")
            curve_attributes_gn = find_node_group.link_gn_from_library("BLENDERRAIL_LinkFloor_GN")[0]
            curve_attributes.node_group = curve_attributes_gn
            curve_attributes["Socket_2"] = curve.curve_object
            curve_attributes.show_expanded = False

        operators._calculate_floors_start_height(context, floors, False)
        #bpy.ops.blenderrail.evaluate_building()

        return{"FINISHED"}


class BLENDERRAIL_OT_copy_floor(bpy.types.Operator):
    bl_idname = "blenderrail.copy_floor"
    bl_label = "Copy Floor"
    bl_description = "Copy the floor with all its settings"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}    
    
    current_floor_index : bpy.props.IntProperty(options = {"HIDDEN"})
    split : bpy.props.BoolProperty(name = "Split", default = False, options = {"HIDDEN"})
    level_index : bpy.props.IntProperty(options = {"HIDDEN"})

    def _match_segments(self, current_curve, new_curve):
        for segment in current_curve.segments:
            new_segment = new_curve.segments.add()
            new_segment.spline_ID = segment.spline_ID
            new_segment.spline_factor = segment.spline_factor
            new_segment.element_ID = segment.element_ID
            new_segment.fit_method = segment.fit_method
            new_segment.fixed_number = segment.fixed_number
        return

    def _copy_objects(self, current_curve, new_curve, element_type):
        elements = getattr(current_curve, element_type)
        new_elements = getattr(new_curve, element_type)

        if len(elements.objects) == 0:
            return
        for obj in elements.objects:
            new_obj = new_elements.objects.add()
            new_obj.object = obj.object
        return

    def _copy_curve(self, current_floor, new_floor):
        if len(current_floor.curves) == 0:
            return
        
        for curve in current_floor.curves:
            obj = curve.curve_object
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()

            new_curve = new_floor.curves.add()
            new_curve.curve_object = new_obj
            
            new_curve.floor_ceiling = curve.floor_ceiling
            new_curve.select_method = curve.select_method
            new_curve.height = curve.height
            
            self._copy_objects(curve, new_curve, "main_elements")
            self._copy_objects(curve, new_curve, "corner_elements")

            self._match_segments(curve, new_curve)


    def execute(self, context):
        scene = context.scene
        floors = scene.buildings[scene.active_building_index].floors
        current_floor = floors[self.current_floor_index]

        bpy.ops.blenderrail.add_floor()
        new_floor = floors[self.current_floor_index + 1]

        new_floor.total_height = current_floor.total_height
        new_floor.start_height = current_floor.start_height
        if self.split:
            new_floor.array = current_floor.array - self.level_index - 1
            current_floor.array = self.level_index + 1
        else:
            new_floor.array = current_floor.array

        self._copy_curve(current_floor, new_floor)

        bpy.ops.blenderrail.evaluate_building()
        
        return{"FINISHED"}



# ------------------------------
# Operators: Curves Operators
# ------------------------------

class BLENDERRAIL_OT_add_curve_object(bpy.types.Operator):
    bl_idname = "blenderrail.add_curve_object"
    bl_label = "Add Curve"
    bl_description = "Add a curve object to the active floor"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor = floors[building.active_floor_index]
        curves = floor.curves

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors — add a floor first")
            return {"CANCELLED"}

        if len(curves) == 0:
            new_curve = curves.add()
            floor.active_curve_index = 0
        else:
            new_curve = curves.add()
            floor.active_curve_index = len(floor.curves) - 1

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_curve_object(bpy.types.Operator):
    bl_idname = "blenderrail.remove_curve_object"
    bl_label = "Remove Curve"
    bl_description = "Remove a curve object from the active floor"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


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
            floor.active_curve_index = 0
            return {"CANCELLED"}

        floor.curves_collection.objects.link(curves[(len(curves) - 1)].curve_object)
        curves.remove(len(curves) - 1)
        floor.active_curve_index -= 1

        return {"FINISHED"}
    

class BLENDERRAIL_OT_stack_curve_object(bpy.types.Operator):
    bl_idname = "blenderrail.stack_curve_object"
    bl_label = "Stack Curve Object"
    bl_description = "Set height (location z value)"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    property_to_stack : bpy.props.EnumProperty(
        name = "property_to_stack",
        description = "Select what curves to stack",
        items = [
        ('FLOORS', "Floors", "All floors", 0),
        ('CURVES', "Curves", "All floors and curves", 1),
        ('CURRENTFLOORCURVES', "Current floor curves", "Current floor curves", 2),
        ('CURRENTCURVE', "Cuurnet curve", "Current curve", 3),
        ('FLATTENFLOOR', "Flatten floor", "Flatten current floor", 4),
        ],
        default = 'FLOORS'
    )

    def _set_cruve_location_z(self, context, curve, curves_sorted):
        sorted_index = curves_sorted.index(curve)
        if sorted_index == 0:
            self.report({"INFO"}, "This is the lowest curve in the floor")
            return({"CANCELLED"})
        sorted_index = curves_sorted.index(curve)
        prev_curve = curves_sorted[sorted_index - 1]
        z_diff = curve.curve_object.location.z - prev_curve.curve_object.location.z
        if curve.curve_object.location.z < prev_curve.curve_object.location.z + prev_curve.height:
            curve.curve_object.location.z  = prev_curve.curve_object.location.z
        else:
            curve.curve_object.location.z = prev_curve.curve_object.location.z + prev_curve.height
        return

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor = floors[building.active_floor_index]
        curves = floor.curves
        curve = floor.curves[floor.active_curve_index]
        curves_sorted = sorted(curves, key=lambda c: c.curve_object.location.z)

        if self.property_to_stack == 'FLOORS':
            operators._calculate_floors_start_height(context, floors, False)

        if self.property_to_stack == 'CURVES':
            operators._calculate_floors_start_height(context, floors, True)

        if self.property_to_stack == 'CURRENTFLOORCURVES':
            for curve in curves:
                self._set_cruve_location_z(context, curve, curves_sorted)
        
        if self.property_to_stack == 'CURRENTCURVE':
            self._set_cruve_location_z(context, curve, curves_sorted)

        if self.property_to_stack == 'FLATTENFLOOR':
            for curve in curves:
                curve.curve_object.location.z = floor.start_height

        curves_sorted = sorted(curves, key=lambda c: c.curve_object.location.z)
        z_diff = curves_sorted[len(curves_sorted) - 1].curve_object.location.z - curves_sorted[0].curve_object.location.z
        floor.total_height = z_diff * floor.array

        return{"FINISHED"}
    
    @classmethod    
    def description(cls, context, properties):
        description = "Set height (location z value)"

        property_to_stack = properties.property_to_stack

        match property_to_stack:
            case 'FLOORS':
                description += " of all floors"
            case 'CURVES':
                description += " of all floors and their respective curves"
            case 'CURRENTFLOORCURVES':
                description += " of the current floor curves"
            case 'CURRENTCURVE':
                description += " of the current active curve"
            case 'FLATTENFLOOR':
                description += " of all floor curves to the floor start height"

        return description
    


# --------------------------------
# Operators: segments Operators
# --------------------------------

class BLENDERRAIL_OT_add_segment(bpy.types.Operator):
    bl_idname = "blenderrail.add_segment"
    bl_label = "Add Segment to Floor"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

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
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

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
    


# --------------------------------------
# Operators: Collect Object Operators
# --------------------------------------

class BLENDERRAIL_OT_add_collect_object(bpy.types.Operator):
    bl_idname = "blenderrail.add_collect_object"
    bl_label = "Add Collect Object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    element_type : bpy.props.StringProperty(options = {"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        collection = getattr(curve, self.element_type)

        new_element = collection.objects.add()
        new_element.host_curve = curve.curve_object
        new_element.element_type = self.element_type

        #bpy.ops.blenderrail.evaluate_building()

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_collect_object(bpy.types.Operator):
    bl_idname = "blenderrail.remove_collect_object"
    bl_label = "Remove Collect Object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    element_type : bpy.props.StringProperty(options = {"HIDDEN"})

    def _remove_curve_element(self, context, host_curve, modifier, object):
        if modifier.type != "NODES" or "BLENDERRAIL_CurveElements_GN" not in modifier.name:
            return
        if modifier["Socket_4"] == object:
            host_curve.modifiers.remove(modifier)
        return

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        collection = getattr(curve, self.element_type)

        if len(collection.objects) == 0:
            self.report({"INFO"}, "No objects to remove")
            return {"CANCELLED"}

        object = collection.objects[len(collection.objects) - 1].object
        host_curve = collection.objects[len(collection.objects) - 1].host_curve
        for modifier in host_curve.modifiers:
            self._remove_curve_element(context, host_curve, modifier, object)

        collection.objects.remove(len(collection.objects) - 1)

        #bpy.ops.blenderrail.evaluate_building()

        return {"FINISHED"}
    

class BLENDERRAIL_OT_select_collect_object(bpy.types.Operator):
    bl_idname = "blenderrail.select_collect_object"
    bl_label = "Select Collect Object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
 
    element_type : bpy.props.StringProperty(options = {"HIDDEN"})
    index : bpy.props.IntProperty(default = -1, options = {"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        main_elements = curve.main_elements 
        corner_elements = curve.corner_elements
        element = None


        if self.element_type == "main_elements":
            element = main_elements.objects[self.index].object
        if self.element_type == "corner_elements":
            element = corner_elements.objects[self.index].object
        if element == None:
            self.report({"ERROR"}, "No object provided")
            return{"CANCELLED"}

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = element
        element.select_set(True)

        return{"FINISHED"}
