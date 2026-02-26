import bpy



# ----------------
# Operators: Floor
# ----------------

class BLENDERRAIL_OT_iterate_floors(bpy.types.Operator):
    bl_idname = "blenderrail.iterate_floors"
    bl_label = "Apply Floor Heights to Displacement"
    bl_description = "For each floor, assign its curve the Displacement_GN modifier and set height to Socket_8[2] (Z component of vector)"
    bl_options = {"REGISTER", "UNDO"}

    def _combine_element_objects(self, context, floor, collection):
        element_objects = floor.element_object

        for obj in element_objects:
            collection.objects.link(obj.object)

        return collection


    def execute(self, context):
        scene = context.scene
        floors = scene.floors

        if not floors or len(floors) == 0:
            self.report({"WARNING"}, "No floors in collection")
            return {"CANCELLED"}

        for floor_index, floor in enumerate(floors):

            floor.name = "Floor" + " #" + str(floor_index)

            parent_collection = floor.curve.users_collection[0]

            if floor.name + "_elements" not in parent_collection.children:
                floor_element_collection = bpy.data.collections.new(name = floor.name + "_elements")
                parent_collection.children.link(floor_element_collection)
            else:
                floor_element_collection = bpy.data.collections.get(floor.name + "_elements")
            
            curve_obj = floor.curve
            if curve_obj is None:
                self.report({"WARNING"}, "Floor '%s' has no curve assigned" % floor.name)
                continue

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
                split_segments["Socket_2"] = self._combine_element_objects(context, floor, floor_element_collection)
            split_segments.show_expanded = False

            for segment in floor.segments:
                element_id = curve_obj.modifiers.new(name = "BLENDERRAIL_ElementID_GN", type = "NODES")
                element_id.node_group = bpy.data.node_groups.get('BLENDERRAIL_ElementID_GN')
                element_id["Socket_2"] = segment.ID
                element_id.show_expanded = False


        self.report({"INFO"}, "Applied heights to %d floor(s)" % len(floors))
        return {"FINISHED"}



class BLENDERRAIL_OT_iterate_segments(bpy.types.Operator):
    bl_idname = "blenderrail.iterate_segments"
    bl_label = "Register splines as segments"
    bl_description = "Iterate through all spline in curve, register a segment in the floor for each"
    bl_options = {"REGISTER", "UNDO"}

    use_evaluated: bpy.props.BoolProperty(
        name = "Use evaluated (after modifiers)",
        default = False,
        description = "Use curve geometry after modifiers (e.g. Geometry Nodes). Slower and result is temporary"
    )


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
            curve_obj = floor.curve
            if curve_obj is None or curve_obj.type != 'CURVE' or curve_obj.data is None:
                continue

            curve_data = curve_obj.data
            floor.segments.clear()
            context.scene.active_floor_index = floor_index
            index = 0

            for spline_index, spline in enumerate(curve_data.splines):
                n_points = self._spline_control_point_count(context, spline)
                # One segment per span between control points; last point has no "next" segment
                n_segments = max(0, n_points - 1)
                for i in range(n_segments):
                    segment = floor.segments.add()
                    segment.name = "Segment #%d" % index
                    segment.ID = index
                    index += 1

        return {"FINISHED"}
