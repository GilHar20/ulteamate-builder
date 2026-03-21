import bpy
import mathutils
from bpy.app.handlers import persistent



# ----------------
# Helper Functions
# ----------------

def _match_element_id_by_factor(curve_index, spline_index, factor, old_assignments):
    """
    Interval-based matching: find the old segment on the same curve and spline whose factor
    is at or just below the given factor. Exact matches (within epsilon) take priority.
    A new segment inherits from the old segment whose interval it falls within.
    If no match, return None (caller can use segment.ID).
    """
    candidates = [(f, element_ID) for (c_ix, s_ix, f, element_ID) in old_assignments if c_ix == curve_index and s_ix == spline_index]
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

def _sync_segments_to_curves(curve_data_list, floor):
    """Sync floor.segments to combined curve topology and re-match element_IDs by curve factor."""
    old_assignments = [
        (seg.curve_ID, seg.spline_ID, seg.spline_factor, seg.element_ID)
        for seg in floor.segments
    ]

    factors = []
    total_points = 0

    for curve_index, curve_data in enumerate(curve_data_list):
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
                factors.append((curve_index, spline_index, factor))

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
        curve_index, spline_index, factor = factors[seg_index]
        matched = _match_element_id_by_factor(curve_index, spline_index, factor, old_assignments)
        segment.element_ID = matched if matched is not None else segment.ID
        segment.curve_ID = curve_index
        segment.spline_ID = spline_index
        segment.spline_factor = factor

def _collect_floor_curves(floor):
    """Collect valid curve data, sync segments when combined topology changes."""
    curve_data_list = []
    required = 0

    curve_objects = [curve for curve in floor.curves if curve.curve_object is not None]
    for curve_object in curve_objects:
        if curve_object is None or curve_object.type != 'CURVE':
            continue

        curve_data = curve_object.data
        curve_data_list.append(curve_data)
        _sync_segments_to_curves(curve_data_list, floor)

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
                _collect_floor_curves(floor)
        
    finally:
        _rematch_in_progress = False

def _calculate_floors_start_height(context, floors):
    if not floors:
        scene = context.scene
        floors = scene.buildings[scene.active_building_index].floors
    
    accumulated_height: float = 0
    for floor in floors:
        floor.start_height = accumulated_height
        floor.total_height = floor.height * floor.array
        accumulated_height += floor.total_height
    return

def _combine_element_objects(floor, collection):
    """Assemble custom element collection for a floor"""
    if not floor.element_object:
        return
    
    element_objects = floor.element_object

    for object in collection.objects:
        collection.objects.unlink(object)

    for object in element_objects:
        collection.objects.link(object.object)

    return collection

def _set_element_collection(floor, modifier, element_collection):
    if floor.element_method == 'COLLECTION':
        modifier["Socket_2"] = floor.element_collection
    else:
        modifier["Socket_2"] = element_collection
    return



# --------------------
# Operators: Buildings
# --------------------

class BLENDERRAIL_OT_evaluate_building(bpy.types.Operator):
    bl_idname = "blenderrail.evaluate_building"
    bl_label = "Evaluate building"
    bl_description = "For each floor: set segments, assign its curve with the required modifiers and link elements"
    bl_options = {"REGISTER", "UNDO"}


    def execute(self, context):
        scene = context.scene
        buildings = scene.buildings
        building_index = scene.active_building_index
        building = buildings[building_index]
        old_active_floor = building.active_floor_index
        floors = building.floors

        if len(buildings) == 0:
            self.report({"WARNING"}, "No buildings in collection")
            return {"CANCELLED"}

        if len(floors) == 0:
            self.report({"WARNING"}, "Active building has no floors")
            return {"CANCELLED"}

        _calculate_floors_start_height(context, floors)

        for floor_index, floor in enumerate(floors):
            floor.ID = floor_index
            building.active_floor_index = floor_index

            _collect_floor_curves(floor)

            parent_collection = building.base_object.users_collection[0]

            if str(floor.ID) + "_Elements" not in bpy.data.collections:
                floor_element_collection = bpy.data.collections.new(name = str(floor.ID) + "_Elements")
                parent_collection.children.link(floor_element_collection)
            else:
                floor_element_collection = bpy.data.collections.get(str(floor.ID) + "_Elements")
            _combine_element_objects(floor, floor_element_collection)

            for curve in floor.curves:
                curve_obj = curve.curve_object
                if curve_obj is None:
                    continue

                if curve_obj.parent != building.base_object:
                    bpy.ops.object.select_all(action='DESELECT')
                    context.view_layer.objects.active = building.base_object
                    building.base_object.select_set(True)
                    curve_obj.select_set(True)
                    bpy.ops.object.parent_no_inverse_set(keep_transform=False)
                curve_obj.driver_remove('location', 2)
                fcurve = curve_obj.driver_add('location', 2)
                driver = fcurve.driver
                driver.type = 'AVERAGE'
                var = driver.variables.new()
                var.name = 'start_height'
                var.type = 'SINGLE_PROP'
                var.targets[0].id_type = 'SCENE'
                var.targets[0].id = scene
                var.targets[0].data_path = 'buildings[%d].floors[%d].start_height' % (building_index, floor_index)

                curve_obj.modifiers.clear()

                curve_attributes = curve_obj.modifiers.new(name = "BLENDERRAIL_CurveAttributes_GN", type = "NODES")
                curve_attributes.node_group = bpy.data.node_groups.get('BLENDERRAIL_CurveAttributes_GN')
                _set_element_collection(floor, curve_attributes, floor_element_collection)

                fcurve = curve_obj.driver_add('modifiers["%s"]["Socket_4"]' % curve_attributes.name)
                driver = fcurve.driver
                driver.type = 'AVERAGE'
                var = driver.variables.new()
                var.name = 'height'
                var.type = 'SINGLE_PROP'
                var.targets[0].id_type = 'SCENE'
                var.targets[0].id = scene
                var.targets[0].data_path = 'buildings[%d].floors[%d].height' % (building_index, floor_index)

                fcurve = curve_obj.driver_add('modifiers["%s"]["Socket_3"]' % curve_attributes.name)
                driver = fcurve.driver
                driver.type = 'AVERAGE'
                var = driver.variables.new()
                var.name = 'array'
                var.type = 'SINGLE_PROP'
                var.targets[0].id_type = 'SCENE'
                var.targets[0].id = scene
                var.targets[0].data_path = 'buildings[%d].floors[%d].array' % (building_index, floor_index)     

                fcurve = curve_obj.driver_add('modifiers["%s"]["Socket_5"]' % curve_attributes.name)
                driver = fcurve.driver
                driver.type = 'AVERAGE'
                var = driver.variables.new()
                var.name = 'floor_ceiling'
                var.type = 'SINGLE_PROP'
                var.targets[0].id_type = 'SCENE'
                var.targets[0].id = scene
                var.targets[0].data_path = 'buildings[%d].floors[%d].floor_ceiling' % (building_index, floor_index)        
                curve_attributes.show_expanded = False

                for seg_index, segment in enumerate(floor.segments):
                    element_id = curve_obj.modifiers.new(name = "BLENDERRAIL_ElementID_GN", type = "NODES")
                    element_id.node_group = bpy.data.node_groups.get('BLENDERRAIL_ElementID_GN')
                    element_id["Socket_2"] = segment.ID
                    fcurve = curve_obj.driver_add('modifiers["%s"]["Socket_3"]' % element_id.name)
                    driver = fcurve.driver
                    driver.type = 'AVERAGE'
                    var = driver.variables.new()
                    var.name = "element_ID"
                    var.type = 'SINGLE_PROP'
                    var.targets[0].id_type = 'SCENE'
                    var.targets[0].id = scene
                    var.targets[0].data_path = 'buildings[%d].floors[%d].segments[%d].element_ID' % (building_index, floor_index, seg_index)
                    element_id.show_expanded = False

        building.active_floor_index = old_active_floor

        self.report({"INFO"}, "Generated %d floor(s)" % len(floors))
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