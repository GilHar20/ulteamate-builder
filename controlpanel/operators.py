import bpy



# ----------------
# Operators: Floor
# ----------------

class BLENDERRAIL_OT_generate_building(bpy.types.Operator):
    bl_idname = "blenderrail.generate_building"
    bl_label = "Generate building"
    bl_description = "For each floor: set segments, assign its curve with the required modifiers and link elements"
    bl_options = {"REGISTER", "UNDO"}

    def _combine_element_objects(self, context, floor, collection):
        """Assemble custom element collection for a floor"""
        element_objects = floor.element_object

        for object in collection.objects:
            collection.objects.unlink(object)

        for object in element_objects:
            collection.objects.link(object.object)

        return collection


    def _spline_control_point_count(self, context,spline):
        """Return number of control points in the spline (for segment count, use this - 1)."""
        if spline.type == 'BEZIER':
            return len(spline.bezier_points)
        # POLY, NURBS, etc.
        return len(spline.points)


    def execute(self, context):
        scene = context.scene
        floors = scene.floors

        if not floors or len(floors) == 0:
            self.report({"WARNING"}, "No floors in collection")
            return {"CANCELLED"}

        for floor_index, floor in enumerate(floors):

            floor.name = "Floor" + " #" + str(floor_index)
            
            curve_obj = floor.curve
            if curve_obj is None:
                self.report({"WARNING"}, "Floor '%s' has no curve assigned" % floor.name)
                continue

            # Loop through all curve points and assign segments
            # Last point has no "next" segment
            curve_data = curve_obj.data
            floor.segments.clear()
            context.scene.active_floor_index = floor_index

            for spline in curve_data.splines:
                control_points = self._spline_control_point_count(context, spline)
                for index in range(control_points - 1):
                    segment = floor.segments.add()
                    segment.ID = index
                    segment.cruve_ID = floor_index
                    index += 1

            # Assign modifiers
            # First create a custom element collection
            parent_collection = floor.curve.users_collection[0]

            if floor.name + "_elements" not in parent_collection.children:
                floor_element_collection = bpy.data.collections.new(name = floor.name + "_elements")
                parent_collection.children.link(floor_element_collection)
            else:
                floor_element_collection = bpy.data.collections.get(floor.name + "_elements")

            curve_obj.modifiers.clear()

            displacement = curve_obj.modifiers.new(name = "Displacement_GN", type = "NODES")
            displacement.node_group = bpy.data.node_groups.get('Displacement_GN')
            displacement["Socket_14"] = True
            displacement["Socket_8"][2] = floor.height * floor_index
            displacement.show_expanded = False

            split_segments = curve_obj.modifiers.new(name = "BLENDERRAIL_SplitToSegmenmts_GN", type = "NODES")
            split_segments.node_group = bpy.data.node_groups.get('BLENDERRAIL_SplitToSegmenmts_GN')
            if floor.element_method == 'COLLECTION':
                split_segments["Socket_2"] = floor.element_collection
            else:
                floor.element_object = self._combine_element_objects(context, floor, floor_element_collection)
                split_segments["Socket_2"] = self.element_object
            split_segments.show_expanded = False

            for seg_index, segment in enumerate(floor.segments):
                element_id = curve_obj.modifiers.new(name = "BLENDERRAIL_ElementID_GN", type = "NODES")
                element_id.node_group = bpy.data.node_groups.get('BLENDERRAIL_ElementID_GN')
                element_id["Socket_2"] = segment.ID
                element_id.show_expanded = False
                fcurve = curve_obj.driver_add('modifiers["%s"]["Socket_3"]' % element_id.name)
                driver = fcurve.driver
                driver.type = 'AVERAGE'
                var = driver.variables.new()
                var.name = "element_ID"
                var.type = 'SINGLE_PROP'
                var.targets[0].id_type = 'SCENE'
                var.targets[0].id = scene
                var.targets[0].data_path = 'floors[%d].segments[%d].element_ID' % (floor_index, seg_index)


        self.report({"INFO"}, "Generated %d floor(s)" % len(floors))
        return {"FINISHED"}
