from operator import index

import bpy
from . import operators
from ..utilities import find_node_group, gn_sockets



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
        
        for floor_index, floor in enumerate(floors):
            floor.ID = floor_index
            if floor_index < len(floors) - 1:
                floors[floor_index + 1].curves_collection.name += "temp"
            floor.curves_collection.name = building.name + "_Floor" + str(floor.ID)

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_floor(bpy.types.Operator):
    bl_idname = "blenderrail.remove_floor"
    bl_label = "Remove Active Floor"
    bl_description = "Delete the active floor"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    new_source_floor : bpy.props.BoolProperty(default = False)

    def _clear_floor_curves(self, context, building, floor):
        for curve_obj in floor.curves_collection.objects:
            building.building_collection.objects.link(curve_obj)
            floor.curves_collection.objects.unlint(curve_obj)
            bpy.ops.object.select_all(action='DESELECT')
            curve_obj.select_set(True)
            context.view_layer.objects.active = curve_obj
            bpy.ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')
        return
    
    def _new_source_floor(self, context, building, floors, active_floor, matching_floors):
        new_source = matching_floors[0]
        matching_floors.pop(0)
        new_source_index = next(i for i, floor in enumerate(floors) if floor == new_source)

        bpy.ops.blenderrail.copy_floor(floor_index = new_source_index, mode = "REALIZE")

        for floor in matching_floors:
            gn_sockets._set_socket_value(floor.instance_object.modifiers[0], "Socket_2", new_source.curves_collection)

        self._clear_floor_curves(context, building, active_floor)

        return

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        active_floor = floors[building.active_floor_index]
        active_floor_index = building.active_floor_index

        linked_floors = [floor for floor in floors if floor.is_linked == True]
        matching_floors = [floor for floor in linked_floors if gn_sockets._get_socket_value(floor.instance_object.modifiers[0] , "Socket_2") == active_floor.curves_collection]
        matching_floors.sort(key = lambda f: next(i for i, floor in enumerate(floors) if floor == f))

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors to remove")
            building.active_floor_index = 0
            return {"CANCELLED"}
        
        if active_floor.is_linked == True:
            bpy.data.objects.remove(active_floor.instance_object, do_unlink=True)

        elif len(matching_floors) > 0:
            self._new_source_floor(context, building, floors, active_floor, matching_floors)

        else:
            self._clear_floor_curves(context, building, active_floor)

        bpy.data.collections.remove(active_floor.curves_collection)
        floors.remove(active_floor_index)

        building.active_floor_index = min(active_floor_index, max(0, len(floors) - 1))

        for floor_index, floor in enumerate(floors):
            floor.ID = floor_index
            if floor_index < len(floors) - 1:
                floors[floor_index + 1].curves_collection.name += "temp"
            floor.curves_collection.name = building.name + "_Floor" + str(floor.ID)

        self.new_source_floor = False
        bpy.ops.blenderrail.evaluate_building()

        return {"FINISHED"}
    
    def invoke(self, context, event):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        active_floor = floors[building.active_floor_index]

        linked_floors = [floor for floor in floors if floor.is_linked == True]
        matching_floors = [floor for floor in linked_floors if gn_sockets._get_socket_value(floor.instance_object.modifiers[0] , "Socket_2") == active_floor.curves_collection]
        
        if len(matching_floors) > 0:
            title = "Floor is a source for linked floors!"
            return context.window_manager.invoke_props_dialog(self, title = title, width = 400)

        else:
            return self.execute(context)

    def draw(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]

        layout = self.layout
        layout.label(text = "Floor " + str(floor.ID) + " " + floor.curves_collection.name + " is a source for linked floors!", icon = 'INFO')
        layout.label(text = "You may choose to make the nearest linked floor the new source")
        layout.label(text = "Toggle on the button bellow and press ok")
        layout.label(text = "Otherwaise, press cancel to abort")
        layout.prop(self, "new_source_floor", toggle = True)


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
        floor = floors[self.floor_index]

        if floor.is_linked == True:
            curves_collections = [floor.curves_collection for floor in floors]
            matching_index = curves_collections.index(gn_sockets._get_socket_value(floor.instance_object.modifiers[0] , "Socket_2"))
            if floor.ID -1 == matching_index:
                self.report({"ERROR"}, "Linked floor cannot be lower in the list than its source floor")
                return{"CANCELLED"}            

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
            moved_floor.curves_collection.name = building.name + "_Floor" + str(moved_floor.ID)
            pushed_floor.ID -= 1
            moved_floor.curves_collection.name = building.name + "_Floor" + str(moved_floor.ID)
            building.active_floor_index = self.floor_index + 1
            building.active_floor_index = min(building.active_floor_index, max(0, len(building.floors) - 1))
        else:
            floors.move(self.floor_index, self.floor_index - 1)
            moved_floor = floors[self.floor_index - 1]
            pushed_floor = floors[self.floor_index]
            moved_floor.ID -= 1
            moved_floor.curves_collection.name = building.name + "_Floor" + str(moved_floor.ID)
            pushed_floor.ID += 1
            moved_floor.curves_collection.name = building.name + "_Floor" + str(moved_floor.ID)
            building.active_floor_index = self.floor_index - 1
            building.active_floor_index = min(building.active_floor_index, max(0, len(building.floors) - 1))

        for floor_index, floor in enumerate(floors):
            floor.ID = floor_index
            if floor_index < len(floors) - 1:
                floors[floor_index + 1].curves_collection.name += "temp"
            floor.curves_collection.name = building.name + "_Floor" + str(floor.ID)

        return {"FINISHED"}


class BLENDERRAIL_OT_select_floor_curves(bpy.types.Operator):
    bl_idname = "blenderrail.select_floor_curves"
    bl_label = "Select Floor Curve"
    bl_description = "Select the curve object assigned to the floor"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    floor_index : bpy.props.IntProperty(default = -1, options = {"HIDDEN"})
    curve_index : bpy.props.IntProperty(default = -1, options = {"HIDDEN"})

    def _select_set(self, context, curve_objects):
        if self.curve_index > -1:
            context.view_layer.objects.active = curve_objects[self.curve_index].curve_object
            curve_objects[self.curve_index].curve_object.select_set(True)
            return

        context.view_layer.objects.active = curve_objects[0].curve_object
        for curve in curve_objects:
            curve.curve_object.select_set(True)
        return

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            self.report({'WARNING'}, "Cannot select curve while in mesh edit mode")
            return {"CANCELLED"}
        
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        if self.floor_index == -1:
            active_floor_index = building.active_floor_index
        else:
            active_floor_index = self.floor_index

        floors = building.floors
        floor = floors[self.floor_index]

        if floor.is_linked == True:
            bpy.ops.object.select_all(action = 'DESELECT')
            curves_collections = [floor.curves_collection for floor in floors]
            matching_index = curves_collections.index(gn_sockets._get_socket_value(floor.instance_object.modifiers[0] , "Socket_2"))
            floor = floors[matching_index]
            curves = floor.curves
            curve_objects = [curve for curve in curves if curve.curve_object is not None]
            self._select_set(context, curve_objects)
            self.report({"INFO"}, "Floor is linked. Selected the curves of the source floor")
            return{"FINISHED"}

        curves = floor.curves
        curve_objects = [curve for curve in curves if curve.curve_object is not None]

        if len(curve_objects) == 0:
            self.report({'INFO'}, "No curve objects assigned")
            return{"CANCELLED"}
            
        elif context.mode == 'EDIT_CURVE':
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.select_all(action = 'DESELECT')
            self._select_set(context, curve_objects)
            bpy.ops.object.mode_set(mode = 'EDIT')

        elif context.mode == 'OBJECT':
            bpy.ops.object.select_all(action = 'DESELECT')
            self._select_set(context, curve_objects)

        building.active_floor_index = active_floor_index
        if self.curve_index > -1:
            building.floors[active_floor_index].active_curve_index = self.curve_index

        return{"FINISHED"}


class BLENDERRAIL_OT_link_floor(bpy.types.Operator):
    bl_idname = "blenderrail.link_floor"
    bl_label = "Link Floor"
    bl_description = "Create a new floor entry with all settings linked to the original"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}    


    def execute(self, context):
        curve_attributes_gn = find_node_group.link_gn_from_library("BLENDERRAIL_LinkFloor_GN")
        if curve_attributes_gn[0] == None:
            self.report({"ERROR"}, curve_attributes_gn[1])
            return{"CANCELLED"}
        
        scene = context.scene
        buildings = scene.buildings
        building_index = scene.active_building_index
        building = buildings[building_index]
        floors = building.floors
        active_floor_index = building.active_floor_index
        source_floor = floors[active_floor_index]

        if source_floor.is_linked == True:
            curves_collections = [floor.curves_collection for floor in floors]
            matching_index = curves_collections.index(gn_sockets._get_socket_value(source_floor.instance_object.modifiers[0] , "Socket_2"))
            source_floor = floors[matching_index]

        floors.add()
        floors.move(len(floors) - 1, active_floor_index + 1)
        building.active_floor_index = active_floor_index + 1
        new_floor = floors[building.active_floor_index]
        new_floor.source_floor = source_floor.ID
        new_floor.ID = active_floor_index + 1
        new_floor.is_linked = True
        
        instance_empty = bpy.data.objects.new(f"{building.name}_Floor{new_floor.ID}", None)
        instance_empty.lock_location = (True,True,True)
        instance_empty.lock_rotation = (True,True,True)
        instance_empty.lock_scale = (True,True,True)

        curve_attributes = instance_empty.modifiers.new(name = "BLENDERRAIL_LinkFloor_GN", type = "NODES")
        curve_attributes.node_group = curve_attributes_gn[0]
        gn_sockets._set_socket_value(curve_attributes, "Socket_2", source_floor.curves_collection)
        curve_attributes.show_expanded = False
        new_floor.instance_object = instance_empty

        new_floor.curves_collection = bpy.data.collections.new(building.name + "_Floor" + str(new_floor.ID))
        new_floor.curves_collection.color_tag = building.floors_collection.color_tag
        building.floors_collection.children.link(new_floor.curves_collection)
        new_floor.curves_collection.objects.link(instance_empty)
        
        new_floor.start_height = source_floor.start_height
        new_floor.total_height = source_floor.total_height
        new_floor.array = source_floor.array

        attribute = gn_sockets._input_driver_path(curve_attributes.name, "Socket_4")
        path = 'buildings[%d].floors[%d].floor_visibility' % (building_index, building.active_floor_index)
        operators._set_attribute_driver(self, context, instance_empty, attribute, path, "floor_visibility")

        for floor_index, floor in enumerate(floors):
            floor.ID = floor_index
            if floor_index < len(floors) - 1:
                floors[floor_index + 1].curves_collection.name += "temp"
            floor.curves_collection.name = building.name + "_Floor" + str(floor.ID)

        bpy.ops.blenderrail.evaluate_building()

        massage = "Created link fron floor " + str(source_floor.ID)
        if source_floor.is_linked == True:
            massage = "Selected floor is linked! Created link from the original floor " + str(source_floor.ID)
        self.report({"INFO"}, massage)

        return{"FINISHED"}


class BLENDERRAIL_OT_copy_floor(bpy.types.Operator):
    bl_idname = "blenderrail.copy_floor"
    bl_label = "Copy Floor"
    bl_description = "Copy the floor with all its settings"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}    

    
    floor_index : bpy.props.IntProperty(options = {"HIDDEN"})
    mode : bpy.props.EnumProperty(
        items = [
            ('COPY', "Copy", "Copy the floor with all its settings", 0),
            ('SPLIT', "Split", "Split the floor into two separate floors", 1),
            ('REALIZE', "Realize", "Make the floor a real flooR", 2),
        ]
    )
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

    def _copy_elements(self, current_curve, new_curve, element_type):
        elements = getattr(current_curve, element_type)
        new_elements = getattr(new_curve, element_type)

        if len(elements.objects) == 0:
            return
        for obj in elements.objects:
            new_obj = new_elements.objects.add()
            new_obj.host_curve = new_curve.curve_object
            new_obj.object = obj.object
            new_obj.element_type = obj.element_type
            new_obj.is_empty = obj.is_empty
            new_obj.empty_bounds = obj.empty_bounds
            new_obj.object.update_tag()
        return

    def _copy_curves(self, context, current_floor, new_floor):
        if len(current_floor.curves) == 0:
            return

        for curve in current_floor.curves:
            obj = curve.curve_object
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()

            z_diff = new_floor.start_height - obj.location.z
            new_obj.location.z += z_diff

            new_curve = new_floor.curves.add()
            new_curve.curve_object = new_obj

            new_curve.inset = curve.inset
            new_curve.height = curve.height
            new_curve.floor_ceiling = curve.floor_ceiling
            new_curve.thickness = curve.thickness
            new_curve.direction_bottom = curve.direction_bottom
            new_curve.direction_top = curve.direction_top
            new_curve.top_material = curve.top_material
            new_curve.sides_material = curve.sides_material
            new_curve.bottom_material = curve.bottom_material
            new_curve.select_method = curve.select_method
            new_curve.select_per_segment = curve.select_per_segment
            new_curve.sequence_offset = curve.sequence_offset
            new_curve.random_index = curve.random_index

            new_floor.curves_collection.objects.link(new_obj)
            
            self._copy_elements(curve, new_curve, "main_elements")
            self._copy_elements(curve, new_curve, "corner_elements")
            self._match_segments(curve, new_curve)

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = scene.buildings[scene.active_building_index].floors
        current_floor = floors[self.floor_index]

        if self.mode == 'REALIZE':
            instance_object = current_floor.instance_object
            if instance_object is None:
                self.report({"ERROR"}, "Linked floor has no valid instance collection")
                return {"CANCELLED"}

            source_collection = gn_sockets._get_socket_value(instance_object.modifiers[0], "Socket_2")
            curves_collections = [floor.curves_collection for floor in floors]
            matching_index = curves_collections.index(source_collection)
            source_floor = floors[matching_index]

            if source_floor is None:
                self.report({"ERROR"}, "Could not find source floor for this instance")
                return {"CANCELLED"}

            current_floor.is_linked = False
            current_floor.curves.clear()
            bpy.data.objects.remove(instance_object, do_unlink=True)
            self._copy_curves(context, source_floor, current_floor)

        else:
            building.floors.add()
            floors.move(len(floors) - 1, self.floor_index + 1)
            building.active_floor_index = self.floor_index + 1
            new_floor = floors[building.active_floor_index]

            new_floor.ID = building.active_floor_index
            new_floor.curves_collection = bpy.data.collections.new(building.name + "_Floor" + str(new_floor.ID))
            new_floor.curves_collection.color_tag = building.floors_collection.color_tag
            building.floors_collection.children.link(new_floor.curves_collection)

            new_floor.floor_visibility = current_floor.floor_visibility
            new_floor.total_height = current_floor.total_height
            new_floor.start_height = current_floor.start_height + current_floor.total_height

        if self.mode == 'COPY':
            new_floor.array = current_floor.array
            self._copy_curves(context, current_floor, new_floor)
        elif self.mode == 'SPLIT':
            new_floor.array = current_floor.array - self.level_index - 1
            current_floor.array = self.level_index + 1
            self._copy_curves(context, current_floor, new_floor)

        for floor_index, floor in enumerate(floors):
            floor.ID = floor_index
            if floor_index < len(floors) - 1:
                floors[floor_index + 1].curves_collection.name += "temp"
            floor.curves_collection.name = building.name + "_Floor" + str(floor.ID)

        bpy.ops.blenderrail.evaluate_building()
        
        return{"FINISHED"}


class BLENDERRAIL_OT_floor_settings(bpy.types.Operator):
    bl_idname = "blenderrail.floor_settings"
    bl_label = "Floor Settings"
    bl_description = "Edit the settings of the active floor"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}    


    index : bpy.props.IntProperty(options = {"HIDDEN"})

    def execute(self, context):
        '''This executes NOTHING. Sole purpose of this operator is to expose the active floor's properties in a pop-up dialog :)'''
        return{"FINISHED"}

    def invoke(self, context, event):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[self.index]

        title = building.name + ", Floor " + str(floor.ID)
        return context.window_manager.invoke_props_dialog(self, title = title)

    def draw(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[self.index]

        layout = self.layout
        property_column = layout.column(align = True)
        property_column.prop(floor, "curves_collection", text = "", icon = 'OUTLINER_COLLECTION')
        property_column.prop(floor, "array", text = "Number of Levels")



# ------------------------------
# Operators: Curves Operators
# ------------------------------

class BLENDERRAIL_OT_add_curve_object(bpy.types.Operator):
    bl_idname = "blenderrail.add_curve_object"
    bl_label = "Add Curve"
    bl_description = "Add a curve object to the active floor"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    def execute(self, context):
        wm = context.window_manager
        curve_obj = wm.blenderrail_add_collect_object
        if curve_obj is None:
            self.report({"WARNING"}, "No object provided, Element not added")
            return {"CANCELLED"}
        if curve_obj.type != 'CURVE' or curve_obj.data.dimensions != '2D':
            self.report({"WARNING"}, "Invalid object! Only 2D curve objects can be assigned")
            return {"CANCELLED"}
        
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor = floors[building.active_floor_index]
        curves = floor.curves

        if len(floors) == 0:
            self.report({"WARNING"}, "No floors — add a floor first")
            return {"CANCELLED"}

        new_curve = curves.add()
        new_curve.curve_object = curve_obj
        floor.active_curve_index = len(floor.curves) - 1 if len(floor.curves) > 0 else 0
        curves.move(len(curves) - 1, floor.active_curve_index + 1)
        if curve_obj.name not in floor.curves_collection.objects:
            floor.curves_collection.objects.link(curve_obj)

        bpy.ops.object.select_all(action='DESELECT')
        curve_obj.select_set(True)
        context.view_layer.objects.active = building.base_object
        bpy.ops.object.parent_no_inverse_set(keep_transform = True)

        wm.blenderrail_add_collect_object = None

        bpy.ops.blenderrail.evaluate_building()

        return {"FINISHED"}

    def invoke(self, context, event):
        title = "Add Curve Object"
        return context.window_manager.invoke_props_dialog(self, title = title)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(context.window_manager, "blenderrail_add_collect_object", text = "Curve Object")


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

        if len(curves) == 0:
            self.report({"WARNING"}, "No curve rows to remove")
            floor.active_curve_index = 0
            return {"CANCELLED"}
        
        active_curve = curves[floor.active_curve_index]
        active_curve_index = floor.active_curve_index
        curve_obj = active_curve.curve_object

        if curve_obj is None:
            self.report({"WARNING"}, "No curve object to remove")
            return {"CANCELLED"}
        
        if curve_obj.name in floor.curves_collection.objects:
            floor.curves_collection.objects.unlink(curve_obj)
        if curve_obj.name not in context.scene.collection.objects:
            building.building_collection.objects.link(curve_obj)

        bpy.ops.object.select_all(action='DESELECT')
        curve_obj.select_set(True)
        context.view_layer.objects.active = curve_obj
        bpy.ops.object.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')

        curves.remove(floor.active_curve_index)
        floor.active_curve_index = min(active_curve_index, max(0, len(curves) - 1))

        bpy.ops.blenderrail.evaluate_building()

        return {"FINISHED"}
    

class BLENDERRAIL_OT_replace_curve_object(bpy.types.Operator):
    bl_idname = "blenderrail.replace_curve_object"
    bl_label = "Replace Curve"
    bl_description = "Replace the active curve object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    index : bpy.props.IntProperty(options = {"HIDDEN"})

    def execute(self, context):
        wm = context.window_manager
        element = wm.blenderrail_add_collect_object
        if element is None:
            self.report({"WARNING"}, "No object provided, Element not added")
            wm.blenderrail_add_collect_object = None
            return {"CANCELLED"}
        if element.type != 'CURVE' or element.data.dimensions != '2D':
            self.report({"WARNING"}, "Invalid element! Only 2D curve objects can be assigned")
            wm.blenderrail_add_collect_object = None
            return {"CANCELLED"}
        
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floors = building.floors
        floor = floors[building.active_floor_index]
        curve = floor.curves[self.index]
        curve_obj = curve.curve_obj

        bpy.ops.object.select_all(action='DESELECT')
        element.select_set(True)
        context.view_layer.objects.active = building.base_object
        bpy.ops.object.parent_no_inverse_set(keep_transform = True)

        bpy.ops.object.select_all(action='DESELECT')
        element.select_set(True)
        context.view_layer.objects.active = curve_obj
        bpy.ops.object.make_links_data(type = 'MODIFIERS')

        if element.name not in floor.curves_collection.objects:
            floor.curves_collection.objects.link(curve_obj)
        floor.curves_collection.objects.unlink(curve_obj)
        context.scene.collection.objects.link(curve_obj)
        curve_obj.parent_clear(type = 'CLEAR_KEEP_TRANSFORM')

        curve.curve_object = element

        wm.blenderrail_add_collect_object = None

        return {"FINISHED"}

    def invoke(self, context, event):
        title = "Replace Curve Object"
        return context.window_manager.invoke_props_dialog(self, title = title)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(context.window_manager, "blenderrail_add_collect_object", text = "Element Object")


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


class BLENDERRAIL_OT_curve_settings(bpy.types.Operator):
    bl_idname = "blenderrail.curve_settings"
    bl_label = "Curve Settings"
    bl_description = "Set curve properties"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    index : bpy.props.IntProperty(default = -1, options = {"HIDDEN"})

    def execute(self, context):
        '''This executes NOTHING. Sole purpose of this operator is to expose the active curve's properties in a pop-up dialog :)'''
        return {"FINISHED"}

    def invoke(self, context, event):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[self.index]

        title = building.name + ", Floor " + str(floor.ID) + ", Curve " + str(curve.ID)
        return context.window_manager.invoke_props_dialog(self, title = title)

    def draw(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[self.index]

        layout = self.layout

        object_column = layout.column()
        object_column.alignment = 'RIGHT'
        object_column.prop(curve.curve_object, "name", text = "Curve object name", icon = "FILE_FONT")

        layout.separator(factor = 4.0, type = 'LINE')
        
        curve_fill_column = layout.column(align = True)
        curve_fill_column.prop(curve, "height", text = "Height")
        curve_fill_column.prop(curve, "inset", text = "Shrink/Expand", )

        layout.separator(factor = 4.0, type = 'LINE')

        floor_ceiling_column = layout.column(align = True)
        floor_ceiling_column.alignment = 'RIGHT'
        floor_ceiling_column.prop(curve, "floor_ceiling", text = "Floor/Ceiling")
        if curve.floor_ceiling != 'NONE':
            floor_ceiling_column.prop(curve, "thickness", text = "Extrude Thickness")
        if curve.floor_ceiling == 'BOTTOM' or curve.floor_ceiling == 'BOTH':
            floor_ceiling_column.prop(curve, "direction_bottom", text = "Bottom Extrude Offset")
        if curve.floor_ceiling == 'TOP' or curve.floor_ceiling == 'BOTH':
            floor_ceiling_column.prop(curve, "direction_top", text = "Top Extrude Offset")

        floor_ceiling_column.prop(curve, "top_material", text = "Top Material", icon = 'MATERIAL')
        floor_ceiling_column.prop(curve, "sides_material", text = "Sides Material", icon = 'MATERIAL')
        floor_ceiling_column.prop(curve, "bottom_material", text = "Bottom Material", icon = 'MATERIAL')

        layout.separator(factor = 4.0, type = 'LINE')

        select_column = layout.column(align = True)
        select_column.alignment = 'RIGHT'
        select_column.prop(curve, "select_method", text = "Select Method")
        if curve.select_method != 'CUSTOM':
            select_column.prop(curve, "select_per_segment", text = "Element per Segment", toggle = True)
        if curve.select_method == 'SEQUENCE':
            select_column.prop(curve, "sequence_offset", text = "Sequence Offset")
        elif curve.select_method == 'RANDOM':
            select_column.prop(curve, "random_index", text = "Random Index")

    

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
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.activw_curve_index]
        curves = floor.curves
        segment_index = curve.active_segment_index

        if len(curves) == 0:
            self.report({"WARNING"}, "No floors added")
            return {"CANCELLED"}

        if len(curve.segments) == 0:
            floor.segments.add()

        else:
            curve.segments.add()
            curve.segments.move(len(floor.segments) - 1, segment_index + 1)
            curve.active_segment_index = segment_index + 1

        return {"FINISHED"}


class BLENDERRAIL_OT_remove_segment(bpy.types.Operator):
    bl_idname = "blenderrail.remove_segment"
    bl_label = "Remove Active Segment"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        curves = floor.curves
        segment_index = curve.active_segment_index

        if len(curves) == 0:
            self.report({"WARNING"}, "No floors")
            return {"CANCELLED"}
        
        segments = curve.segments

        if len(segments) == 0:
            self.report({"WARNING"}, "Active floor has no segments")
            return {"CANCELLED"}
        
        if segment_index < 0 or segment_index >= len(segments):
            curve.active_segment_index = max(0, len(segments) - 1)
            segment_index = curve.active_segment_index

        segments.remove(segment_index)
        curve.active_segment_index = min(segment_index, max(0, len(segments) - 1))
        return {"FINISHED"}
    

class BLENDERRAIL_OT_segment_settings(bpy.types.Operator):
    bl_idname = "blenderrail.segment_settings"
    bl_label = "Segment Settings"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    active_index : bpy.props.IntProperty(options = {"HIDDEN"}, default = 0)
    element_ID : bpy.props.IntProperty(default = 0, min = 0, max = 10000)
    fit_method : bpy.props.EnumProperty(
        items = [
        ('ORIGINAL', "Original", "Keep original length, no scaling, bisect element on spline ends", 0),
        ('FIT', "Fit", "Fit length of elements to the spline length, a=scale if necessary", 1),
        ('FIXED', "Fixed", "Fit fixed number of elements, scale elements accordingly", 2),
        ],
        default = 'FIT'
    )
    fixed_number : bpy.props.IntProperty(default = 5, min = 0, max = 10000)

    def execute(self, context):
        '''This executes NOTHING. Sole purpose of this operator is to expose the active segment's properties in a pop-up dialog :)'''
        return {"FINISHED"}

    def invoke(self, context, event):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]

        title = building.name + ", Floor " + str(floor.ID) + ", Curve " + str(curve.ID) + ", segment " + str(self.active_index) 
        return context.window_manager.invoke_props_dialog(self, title = title)
    
    def draw(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        segment = curve.segments[self.active_index]

        layout = self.layout
        layout.prop(segment, "element_ID", text = "Element ID")
        layout.prop(segment, "fit_method", expand = True)
        if segment.fit_method == 'FIXED':
            layout.prop(segment, "fixed_number", text = "Fixed Number")



# --------------------------------------
# Operators: Collect Object Operators
# --------------------------------------

class BLENDERRAIL_OT_add_collect_object(bpy.types.Operator):
    bl_idname = "blenderrail.add_collect_object"
    bl_label = "Add Collect Object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    element_type : bpy.props.StringProperty(options = {"HIDDEN"})
    is_empty : bpy.props.BoolProperty(default = False)
    empty_bounds : bpy.props.FloatVectorProperty(
        name = "Empty Bounds",
        description = "Bounds of the empty element, used to fill length on the curve",
        default = (1.0, 0.2, 3.4),
        subtype = 'XYZ',
        size = 3,
    )
    correct_uv : bpy.props.BoolProperty(
        name = "Correct UV",
        description = "Stretch the element's UV attribute to match the scaling on the curve",
        default = True,
    )
    up_stretched : bpy.props.BoolProperty(
        name = "Is Stretched",
        description = "When true, the element will scale itself upwards to the height of the curve it is instancing on",
        default = False,
    )

    def _add_curve_element(self, curve, collection, curve_elements_gn):
        curve_object = curve.curve_object
        element = collection.objects[collection.active_element_index]
        position = element.ID
        if self.element_type == "corner_elements":
            position += len(getattr(curve, "main_elements").objects)
        obj = element.object

        bpy.ops.object.select_all(action='DESELECT')
        curve_object.select_set(True)
        bpy.context.view_layer.objects.active = curve_object

        curve_element = curve_object.modifiers.new(name = "BLENDERRAIL_CurveElements_GN", type = "NODES")
        curve_element.node_group = curve_elements_gn
        curve_object.modifiers.move(len(curve_object.modifiers) - 1, position + 1)

        gn_sockets._set_socket_value(curve_element, "Socket_9", self.is_empty)
        gn_sockets._set_socket_value(curve_element, "Socket_10", self.empty_bounds)
        gn_sockets._set_socket_value(curve_element, "Socket_4", obj if self.is_empty == False else None)
        gn_sockets._set_socket_value(curve_element, "Socket_5", self.element_type)
        gn_sockets._set_socket_value(curve_element, "Socket_6", self.up_stretched)
        gn_sockets._set_socket_value(curve_element, "Socket_11", self.correct_uv)
        return

    def execute(self, context):
        curve_elements_gn = find_node_group.link_gn_from_library("BLENDERRAIL_CurveElements_GN")
        if curve_elements_gn[0] is None:
            self.report({"INFO"}, curve_elements_gn[1])
            return{"CANCELLED"}
            
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        collection = getattr(curve, self.element_type)
        active_index = collection.active_element_index if len(collection.objects) > 0 else -1

        wm = context.window_manager
        element = wm.blenderrail_add_collect_object

        assigned_objects = [obj.object for obj in collection.objects]
        if element in assigned_objects:
                self.report({"ERROR"}, "Object already assigned to the curve! Cannot be assigned twice.")
                return {"CANCELLED"}

        new_element = collection.objects.add()
        new_element.object = element
        new_element.host_curve = curve.curve_object
        new_element.element_type = self.element_type
        new_element.is_empty = self.is_empty
        collection.objects.move(len(collection.objects) - 1, active_index + 1)
        collection.active_element_index += 1

        for obj_index, obj in enumerate(collection.objects):
            obj.ID = obj_index
        
        # CASE is_empty is True
        if self.is_empty == True:
            # IMPORTANT!!! IF is_empty, wm.blenderrail_add_collect_object has to be None
            wm.blenderrail_add_collect_object = None
            self._add_curve_element(curve, collection, curve_elements_gn[0])
            curve.curve_object.update_tag()

            self.report({"INFO"}, "Added Empty Element")
            return {"FINISHED"}

        elif element is None:
            wm.blenderrail_add_collect_object = None
            self.report({"WARNING"}, "No object provided, Element not added")
            return {"CANCELLED"}
        elif element.type != 'MESH':
            wm.blenderrail_add_collect_object = None
            self.report({"WARNING"}, "Invalid element! Only mesh objects can be added")
            return {"CANCELLED"}

        # CASE is_empty is False
        self._add_curve_element(curve, collection, curve_elements_gn[0])
        wm.blenderrail_add_collect_object = None
        curve.curve_object.update_tag()

        return {"FINISHED"}

    def invoke(self, context, event):
        title = "Add Element"
        return context.window_manager.invoke_props_dialog(self, title = title)
    
    def draw(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        collection = getattr(curve, self.element_type)

        layout = self.layout

        if len(collection.objects) <= 0:
            layout.prop(context.window_manager, "blenderrail_add_collect_object", text = "", placeholder = "Element Object")
            return

        active_element = collection.objects[collection.active_element_index]
        layout.prop(self, "is_empty", text = "Set Element as Empty", icon = 'EMPTY_DATA', toggle = True)
        if self.is_empty:
            bounds_column = layout.column(align = True)
            bounds_column.prop(active_element, "empty_bounds", text = "Element Bounds", icon = 'FIXED_SIZE')
        else:
            layout.prop(context.window_manager, "blenderrail_add_collect_object", text = "", placeholder = "Element Object")
            layout.prop(self, "correct_uv", text = "Correct UVs", toggle = True)
            layout.prop(self, "up_stretched", text = "Up Stretch", toggle = True)


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
        active_element_index = collection.active_element_index
        
        if len(collection.objects) == 0:
            self.report({"INFO"}, "No objects to remove")
            return {"CANCELLED"}

        host_curve = collection.objects[active_element_index].host_curve
        assigned_modifiers = [modifier for modifier in host_curve.modifiers if modifier.type == "NODES" 
                              and "BLENDERRAIL_CurveElements_GN" in modifier.name 
                              and gn_sockets._get_socket_value(modifier, "Socket_5") == self.element_type]

        host_curve.modifiers.remove(assigned_modifiers[active_element_index])
        collection.objects.remove(collection.active_element_index)
        for obj_index,obj in enumerate(collection.objects):
            obj.ID = obj_index
        collection.active_element_index = min(collection.active_element_index, max(0, len(collection.objects) - 1))

        return {"FINISHED"}
    

class BLENDERRAIL_OT_reorder_collect_object(bpy.types.Operator):
    bl_idname = "blenderrail.reorder_collect_object"
    bl_label = "Reorder Collect Object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

 
    element_type : bpy.props.StringProperty(options = {"HIDDEN"})
    up_down : bpy.props.BoolProperty(
        name = "Up Down",
        description = " Switches between moving floor up or dowm the list (True for down the list, false for up)",
        default = True)

    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        collection = getattr(curve, self.element_type)
        collection_objects = collection.objects
        active_element_index = collection.active_element_index

        host_curve = collection.objects[active_element_index].host_curve
        assigned_modifiers = [modifier for modifier in host_curve.modifiers if modifier.type == "NODES" and "BLENDERRAIL_CurveElements_GN" in modifier.name and gn_sockets._get_socket_value(modifier, "Socket_5") == self.element_type]
        modifier_name = assigned_modifiers[active_element_index].name

        if self.up_down == True:
            collection_objects.move(active_element_index, active_element_index + 1)
            bpy.ops.object.select_all(action='DESELECT')
            host_curve.select_set(True)
            bpy.context.view_layer.objects.active = host_curve
            bpy.ops.object.modifier_move_down(modifier=modifier_name)
            collection.active_element_index = active_element_index + 1
            collection.active_element_index = min(collection.active_element_index, max(0, len(collection.objects) - 1))

        else:
            collection_objects.move(active_element_index, active_element_index - 1)
            bpy.ops.object.select_all(action='DESELECT')
            host_curve.select_set(True)
            bpy.context.view_layer.objects.active = host_curve
            bpy.ops.object.modifier_move_up(modifier=modifier_name)
            collection.active_element_index = active_element_index - 1
            collection.active_element_index = min(collection.active_element_index, max(0, len(collection.objects) - 1))

        for obj_index,obj in enumerate(collection.objects):
            obj.ID = obj_index

        return{"FINISHED"}


class BLENDERRAIL_OT_select_collect_object(bpy.types.Operator):
    bl_idname = "blenderrail.select_collect_object"
    bl_label = "Select Collect Object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

 
    element_type : bpy.props.StringProperty(options = {"HIDDEN"})
    index : bpy.props.IntProperty(default = -1, options = {"HIDDEN"})

    def execute(self, context):
        if bpy.context.mode != 'OBJECT':
            self.report({'INFO'}, "You must leave edit mode to select objects")
            return{"FINISHED"}

        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        main_elements = curve.main_elements 
        corner_elements = curve.corner_elements
        elements_collection = getattr(curve, self.element_type)
        element = None

        if elements_collection.objects[self.index].is_empty == True:
            self.report({"ERROR"}, "Element is set as Empty")
            return{"CANCELLED"}    
        if not elements_collection.objects[self.index].object:
            self.report({"ERROR"}, "Assigned object was deleted")
            return{"CANCELLED"}

        element = elements_collection.objects[self.index].object

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = element
        element.select_set(True)

        if self.element_type == "main_elements":
            main_elements.active_element_index = self.index
        if self.element_type == "corner_elements":
            corner_elements.active_element_index = self.index

        return{"FINISHED"}


class BLENDERRAIL_OT_replace_collect_object(bpy.types.Operator):
    bl_idname = "blenderrail.replace_collect_object"
    bl_label = "Replace Collect Object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    element_type : bpy.props.StringProperty(options = {"HIDDEN"})
    index : bpy.props.IntProperty(options = {"HIDDEN"}, default = 0)
    
    def execute(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        collection = getattr(curve, self.element_type)
        selected_element = collection.objects[self.index]

        if selected_element.is_empty == True:
            self.report({"INFO"}, "Selected element is set as 'Empty'. Please disable 'Empty' and select a viable object")
            return{"CANCELLED"}
        
        wm = context.window_manager
        element = wm.blenderrail_add_collect_object
        if element is None and selected_element.is_empty == False:
            self.report({"WARNING"}, "No object provided, Element not added")
            wm.blenderrail_add_collect_object = None
            return {"CANCELLED"}
        if element.type != 'MESH' and selected_element.is_empty == False:
            self.report({"WARNING"}, "Invalid element! Only mesh objects can be added")
            wm.blenderrail_add_collect_object = None
            return {"CANCELLED"}

        host_curve = selected_element.host_curve
        assigned_modifiers = [modifier for modifier in host_curve.modifiers if modifier.type == "NODES" and "BLENDERRAIL_CurveElements_GN" in modifier.name and gn_sockets._get_socket_value(modifier, "Socket_5") == self.element_type]

        current_modifier = assigned_modifiers[self.index]
        gn_sockets._set_socket_value(current_modifier, "Socket_4", element if not selected_element.is_empty else None)
        gn_sockets._set_socket_value(current_modifier, "Socket_9", selected_element.is_empty if selected_element.is_empty else False)
        gn_sockets._set_socket_value(current_modifier, "Socket_10", selected_element.empty_bounds if selected_element.is_empty else (1.0, 0.2, 3.4))

        selected_element.object = element

        wm.blenderrail_add_collect_object = None
        curve.curve_object.update_tag()

        return{"FINISHED"}

    def invoke(self, context, event):
        title = "Replace Element"
        return context.window_manager.invoke_props_dialog(self, title = title)
    
    def draw(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]
        collection = getattr(curve, self.element_type)
        selected_element = collection.objects[self.index]

        layout = self.layout
        if selected_element.is_empty == True:
            layout.label(text = "Selected element is set as 'EMPTY'!", icon = 'INFO')
            layout.label(text = "Disable 'Empty' if you wish to assign an object")
            layout.prop(self, "is_empty", text = "Set Element as Empty", icon = 'EMPTY_DATA', toggle = True)
        else:
            layout.prop(context.window_manager, "blenderrail_add_collect_object", text = "Element Object")


class BLENDERRAIL_OT_collect_object_settings(bpy.types.Operator):
    bl_idname = "blenderrail.collect_object_settings"
    bl_label = "Collect Object Settings"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

 
    element_type : bpy.props.StringProperty(options = {"HIDDEN"})
    collect_method : bpy.props.BoolProperty(default = False, options = {"HIDDEN"})
    index : bpy.props.IntProperty(default = -1, options = {"HIDDEN"})

    def execute(self, context):
        '''This executes NOTHING. Sole purpose of this operator is to expose the active element's properties in a pop-up dialog :)'''
        return{"FINISHED"}

    def invoke(self, context, event):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]

        title = building.name + ", Floor " + str(floor.ID) + ", Curve " + str(curve.ID) + ", " + self.element_type
        return context.window_manager.invoke_props_dialog(self, title = title)
    
    def draw(self, context):
        scene = context.scene
        building = scene.buildings[scene.active_building_index]
        floor = building.floors[building.active_floor_index]
        curve = floor.curves[floor.active_curve_index]

        layout = self.layout

        elements_collection = getattr(curve, self.element_type)
        element = None
        
        if self.collect_method == False:
            element = elements_collection.objects[self.index]

        else:
            element = elements_collection
        
        if self.collect_method == True:
            layout.prop(element, "correct_uv", text = "Correct UVs", toggle = True)
            layout.prop(element, "up_stretched", text = "Up Stretch", toggle = True)


        else:
            empty_column = layout.column(align = True)
            if element.is_empty == True:
                empty_column.prop(element, "empty_bounds", text = "Element Bounds", icon = 'FIXED_SIZE')

            layout.prop(element, "up_stretched", text = "Up Stretch", toggle = True)
            layout.prop(element, "correct_uv", text = "Correct UVs", toggle = True)
        
        return