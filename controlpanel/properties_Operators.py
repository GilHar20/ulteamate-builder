import bpy
import uuid



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
            floors.add()
        else:
            new_floor = floors.add()
            new_floor.uid = uuid.uuid4().hex
            floors.move(len(floors) - 1, active_floor_index + 1)
            building.active_floor_index = active_floor_index + 1

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_floor(bpy.types.Operator):
    bl_idname = "blenderrail.remove_floor"
    bl_label = "Remove Active Floor"
    bl_description = "Delete the active floor"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

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
        else:
            floors.move(self.floor_index, self.floor_index - 1)

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

    current_floor_index : bpy.props.IntProperty(options = {"HIDDEN"})
    floor_attributes = ["array", "total_height", "start_height", "active_curve_index"]
    curve_attributes = ["height",
                        "floor_ceiling", "thickness", "direction_bottom", "direction_top", "inset",
                        "select_method", "sequence_offset", "random_index"]
    segment_attributes = ["element_ID", "fit_method", "fixed_number"]

    def _copy_objects(self, current_curve, new_curve, element_type):
        elements = getattr(current_curve, element_type)
        new_elements = getattr(new_curve, element_type)

        if len(elements.objects) == 0:
            return
        for obj in elements.objects:
            new_obj = new_elements.objects.add()
            new_obj.object = obj.object
        return
    
    def _link_attribute_driver(self, context, new_item, attr_name, path):
        scene = context.scene

        fcurve = new_item.driver_add(attr_name)
        driver = fcurve.driver
        driver.type = 'AVERAGE'
        var = driver.variables.new()
        var.name = attr_name
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = scene
        var.targets[0].data_path = path
        return

    def execute(self, context):
        scene = context.scene
        building_index = scene.active_building_index
        floors = scene.buildings[scene.active_building_index].floors
        current_floor = floors[self.current_floor_index]
        current_floor_index = self.current_floor_index

        floors.add()
        floors.move(len(floors) - 1, self.current_floor_index + 1)
        new_floor = floors[self.current_floor_index + 1]
        new_floor.uid = uuid.uuid4().hex
        new_floor.source_uid = current_floor.uid

        for attr in self.floor_attributes:
            path = 'buildings[%d].floors[%d].%s' % (building_index, current_floor_index, attr)
            self._link_attribute_driver(context, new_floor, attr, path)
        
        for curve_index, curve in enumerate(current_floor.curves):
            obj = curve.curve_object
            new_obj = obj.copy()
            new_curve = new_floor.curves.add()
            new_curve.curve_object = new_obj

            for attr in self.curve_attributes:
                path = 'buildings[%d].floors[%d].curves[%d].%s' % (building_index, current_floor_index, curve_index, attr)
                self._link_attribute_driver(context, new_curve, attr, path)

            for segment_index, segment in enumerate(curve.segments):
                new_segment = new_curve.segments.add()
                for attr in self.segment_attributes:
                    path = 'buildings[%d].floors[%d].curves[%d].segments[%d].%s' % (building_index, current_floor_index, curve_index, segment_index, attr)
                    self._link_attribute_driver(context, new_segment, attr, path)
            
            self._copy_objects(curve, new_curve, "main_elements")
            self._copy_objects(curve, new_curve, "corner_elements")

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

        floors.add()
        floors.move(len(floors) - 1, self.current_floor_index + 1)
        new_floor = floors[self.current_floor_index + 1]
        new_floor.uid = uuid.uuid4().hex

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
# Operators: add / remove curves
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
            curves.add()
            floor.active_curve_index = 0
        else:
            curves.add()

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

        curves.remove(len(curves) - 1)
        floor.active_curve_index -= 1

        return {"FINISHED"}
    


# --------------------------------
# Operators: add / remove segments
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
# Operators: add / remove collect object
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

        collection.objects.add()

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_collect_object(bpy.types.Operator):
    bl_idname = "blenderrail.remove_collect_object"
    bl_label = "Remove Collect Object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    element_type : bpy.props.StringProperty(options = {"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        collection = getattr(curve, self.element_type)

        if len(collection.objects) == 0:
            self.report({"WARNING"}, "No objects to remove")
            return {"CANCELLED"}

        obj = collection.objects[len(collection.objects) - 1].object

        collection.objects.remove(len(collection.objects) - 1)

        target_collection = None

        if obj is not None:
            target_collection = bpy.data.collections.get(curve.curve_object.name + "_" + self.element_type)
        if target_collection is not None:
            target_collection.objects.unlink(obj)

        return {"FINISHED"}
