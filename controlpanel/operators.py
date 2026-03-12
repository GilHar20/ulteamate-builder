import bpy
import mathutils
from bpy.app.handlers import persistent



# ----------------
# Helper Functions
# ----------------

def _match_element_id_by_factor(spline_index, factor, old_assignments):
    """
    Interval-based matching: find the old segment on the same spline whose factor
    is at or just below the given factor. Exact matches (within epsilon) take priority.
    A new segment inherits from the old segment whose interval it falls within.
    If no match, return None (caller can use segment.ID).
    """
    candidates = [(f, element_ID) for (s_ix, f, element_ID) in old_assignments if s_ix == spline_index]
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    for c in candidates:
        if round(c[0], 3) == round(factor, 3):
            return c[1]
    best = candidates[0]
    for c in candidates:
        if c[0] <= factor:
            best = c
        else:
            break
    return best[1]

def _spline_cumulative_lengths(count, spline):
    """
    Return (cumulative_lengths, total_length) for the spline.
    cumulative_lengths[i] = length from spline start to control point i (0 at index 0).
    total_length = full spline length.
    """
    if count == 0:
        return ([], 0.0)
    if count == 1:
        return ([0.0], 0.0)

    segment_lengths = []

    if spline.type == 'BEZIER':
        pts = spline.bezier_points
        if spline.type == 'BEZIER':
            pts = spline.bezier_points
            for i in range(count - 1):
                segment_lengths.append((pts[i + 1].co - pts[i].co).length)
            if spline.use_cyclic_u:
                segment_lengths.append((pts[0].co - pts[-1].co).length)

    # POLY or NURBS
    else: 
        pts = spline.points
        for i in range(count - 1):
            p0 = mathutils.Vector((pts[i].co[0], pts[i].co[1], pts[i].co[2]))
            p1 = mathutils.Vector((pts[i + 1].co[0], pts[i + 1].co[1], pts[i + 1].co[2]))
            segment_lengths.append((p1 - p0).length)
        if spline.use_cyclic_u:
            p0 = mathutils.Vector((pts[-1].co[0], pts[-1].co[1], pts[-1].co[2]))
            p1 = mathutils.Vector((pts[0].co[0], pts[0].co[1], pts[0].co[2]))
            segment_lengths.append((p1 - p0).length)

    total = sum(segment_lengths)
    cumulative = [0.0]

    # For open curves, last point is at total length; for closed, we have n segments, no extra append
    for L in segment_lengths[:-1]:
        cumulative.append(cumulative[-1] + L)
    if not spline.use_cyclic_u:
        cumulative.append(total)

    return (cumulative, total)

def _sync_segments_to_curve(curve_data, floor):
    """Sync floor.segments to curve topology and re-match element_IDs by curve factor."""
    old_assignments = [
        (seg.spline_ID, seg.spline_factor, seg.element_ID)
        for seg in floor.segments
    ]

    factors = []
    total_points = 0

    for spline_index, spline in enumerate(curve_data.splines):
        if spline.type == 'BEZIER':
            count = len(spline.bezier_points)
        else:
            count = len(spline.points)
        total_points += count

        cumulative, total = _spline_cumulative_lengths(count, spline)
        for point_index in range(count):
            if total <= 0 or point_index >= len(cumulative):
                factor = 0.0
            else:
                factor = cumulative[point_index] / total
            factors.append((spline_index, factor))

    current = len(floor.segments)
    delta = total_points - current
    if delta > 0:
        for _ in range(delta):
            floor.segments.add()
    elif delta < 0:
        for _ in range(-delta):
            floor.segments.remove(len(floor.segments) - 1)

    for seg_index, segment in enumerate(floor.segments):
        segment.ID = seg_index
        spline_index, factor = factors[seg_index]
        matched = _match_element_id_by_factor(spline_index, factor, old_assignments)
        segment.element_ID = matched if matched is not None else segment.ID
        segment.spline_ID = spline_index
        segment.spline_factor = factor

_rematch_in_progress = False

@persistent
def on_depsgraph_update(scene, depsgraph):
    """Re-match segments when a floor's curve topology changes."""
    global _rematch_in_progress
    if _rematch_in_progress:
        return

    if not hasattr(scene, "buildings"):
        return

    _rematch_in_progress = True
    try:
        for building_index, building in enumerate(scene.buildings):
            for floor_index, floor in enumerate(building.floors):
                curve_obj = floor.curve
                if curve_obj is None or curve_obj.type != 'CURVE':
                    continue
                curve_data = curve_obj.data
                required = 0
                for spline in curve_data.splines:
                    if spline.type == 'BEZIER':
                        required += len(spline.bezier_points)
                    else:
                        required += len(spline.points)
                current = len(floor.segments)
                if required == current:
                    continue
                _sync_segments_to_curve(curve_data, floor)
        
    finally:
        _rematch_in_progress = False



# --------------------
# Operators: Buildings
# --------------------

class BLENDERRAIL_OT_evaluate_building(bpy.types.Operator):
    bl_idname = "blenderrail.evaluate_building"
    bl_label = "Evaluate building"
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


    def execute(self, context):
        scene = context.scene
        buildings = scene.buildings
        building_index = scene.active_building_index

        if len(buildings) == 0:
            self.report({"WARNING"}, "No buildings in collection")
            return {"CANCELLED"}

        if building_index < 0 or building_index >= len(buildings):
            building_index = max(0, len(buildings) - 1)
            scene.active_building_index = building_index

        building = buildings[building_index]
        old_active_floor = building.active_floor_index
        floors = building.floors

        if len(floors) == 0:
            self.report({"WARNING"}, "Active building has no floors")
            return {"CANCELLED"}

        generated_floors: int = 0
        total_height: int = 0

        for floor_index, floor in enumerate(floors):
            floor.ID = floor_index
            building.active_floor_index = floor_index

            curve_obj = floor.curve
            if curve_obj is None:
                self.report({"WARNING"}, "Floor '%s' has no curve assigned")
                continue

            curve_data = curve_obj.data

            _sync_segments_to_curve(curve_data, floor)

            parent_collection = floor.curve.users_collection[0]

            if floor.curve.name + "_Elements" not in bpy.data.collections:
                floor_element_collection = bpy.data.collections.new(name = floor.curve.name + "_Elements")
                parent_collection.children.link(floor_element_collection)
            else:
                floor_element_collection = bpy.data.collections.get(floor.curve.name + "_Elements")

            curve_obj.modifiers.clear()

            displacement = curve_obj.modifiers.new(name = "Displacement_GN", type = "NODES")
            displacement.node_group = bpy.data.node_groups.get('Displacement_GN')
            displacement["Socket_14"] = True
            displacement["Socket_8"][2] = total_height          
            displacement.show_expanded = False

            split_segments = curve_obj.modifiers.new(name = "BLENDERRAIL_SplitToSegmenmts_GN", type = "NODES")
            split_segments.node_group = bpy.data.node_groups.get('BLENDERRAIL_SplitToSegmenmts_GN')
            if floor.element_method == 'COLLECTION':
                split_segments["Socket_2"] = floor.element_collection
            else:
                combined_collection = self._combine_element_objects(context, floor, floor_element_collection)
                split_segments["Socket_2"] = combined_collection
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
                var.targets[0].data_path = 'buildings[%d].floors[%d].segments[%d].element_ID' % (building_index, floor_index, seg_index)

            array = curve_obj.modifiers.new(name = "Array_GN", type = "NODES")
            array.node_group = bpy.data.node_groups.get('Array_GN')
            #array["Socket_6"] = floor.array
            fcurve = curve_obj.driver_add('modifiers["%s"]["Socket_6"]' % array.name)
            driver = fcurve.driver
            driver.type = 'AVERAGE'
            var = driver.variables.new()
            var.name = 'Array'
            var.type = 'SINGLE_PROP'
            var.targets[0].id_type = 'SCENE'
            var.targets[0].id = scene
            var.targets[0].data_path = 'buildings[%d].floors[%d].array' % (building_index, floor_index)     
            #array["Socket_18"][2] = floor.height
            fcurve = curve_obj.driver_add('modifiers["%s"]["Socket_18"]' % array.name, 2)
            driver = fcurve.driver
            driver.type = 'AVERAGE'
            var = driver.variables.new()
            var.name = 'Height'
            var.type = 'SINGLE_PROP'
            var.targets[0].id_type = 'SCENE'
            var.targets[0].id = scene
            var.targets[0].data_path = 'buildings[%d].floors[%d].height' % (building_index, floor_index)     
            array.show_expanded = False

            floor.total_height = floor.height * floor.array
            total_height += floor.total_height

            generated_floors += 1

            building.active_floor_index = old_active_floor


        self.report({"INFO"}, "Generated %d floor(s)" % generated_floors)
        return {"FINISHED"}



class BLENDERRAIL_OT_generate_building(bpy.types.Operator):
    bl_idname = "blenderrail.generate_building"
    bl_label = "Generate Building"
    bl_description = "Add base object with construct modifier"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        buildings = scene.buildings

        bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        cube_obj = context.view_layer.objects.active

        node_group = bpy.data.node_groups.get("BLENDERRAIL_Construct_GN")
        if node_group is None:
            self.report({"ERROR"}, "Node group 'BLENDERRAIL_Construct_GN' not found")
            return {"CANCELLED"}

        modifier = cube_obj.modifiers.new(name = "BLENDERRAIL_Construct_GN", type = "NODES")
        modifier.node_group = node_group
        modifier.show_expanded = False

        building = buildings.add()
        building.base_object = cube_obj
        scene.active_building_index = len(buildings) - 1

        bpy.ops.blenderrail.add_floor()

        return {"FINISHED"}



class BLENDERRAIL_OT_remove_building(bpy.types.Operator):
    bl_idname = "blenderrail.remove_building"
    bl_label = "Remove Building"
    bl_description = "Delete active building from list"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        buildings = scene.buildings
        active_building_index = scene.active_building_index

        buildings.remove(active_building_index)

        return{"FINISHED"}



class BLENDERRAIL_OT_select_base_object(bpy.types.Operator):
    bl_idname = "blenderrail.select_base_object"
    bl_label = "Select Base Object"
    bl_description = "Selects the building base object"
    bl_options = {"REGISTER", "UNDO"}

    building_index : bpy.props.IntProperty(options = {"HIDDEN"})

    def execute(self, context):
        scene = context.scene
        buildings = scene.buildings

        object = buildings[self.building_index].base_object

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = object
        object.select_set(True)

        return {"FINISHED"}