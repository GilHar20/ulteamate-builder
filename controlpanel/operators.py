import bpy
import mathutils
from bpy.app.handlers import persistent



# ----------------
# Helper Functions
# ----------------

def _match_element_id_by_factor(spline_index, factor, old_assignments):
    """
    Interval-based matching: find the old segment on the same curve and spline whose factor
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

def _sync_segments_to_curves(curve):
    """Sync floor.segments to combined curve topology and re-match element_IDs by curve factor."""
    if not curve.curve_object:
        return
    
    curve_data = curve.curve_object.data
    
    old_assignments = [
        (seg.spline_ID, seg.spline_factor, seg.element_ID)
        for seg in curve.segments
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

    current = len(curve.segments)
    delta = total_points - current
    if delta > 0:
        for _ in range(delta):
            curve.segments.add()
    elif delta < 0:
        for _ in range(-delta):
            curve.segments.remove(len(curve.segments) - 1)

    for seg_index, segment in enumerate(curve.segments):
        segment.ID = seg_index
        spline_index, factor = factors[seg_index]
        matched = _match_element_id_by_factor(spline_index, factor, old_assignments)
        segment.element_ID = matched if matched else 0
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

    buildings = scene.buildings
    building_index = scene.active_building_index
    active_building = buildings[building_index]
    floors = active_building.floors
    floor_index = active_building.active_floor_index
    active_floor = floors[floor_index]
    curves = active_floor.curves
    curve_index = active_floor.active_curve_index
    active_curve = curves[curve_index]

    try:
        _sync_segments_to_curves(active_curve)
        
    finally:
        _rematch_in_progress = False

def _calculate_floors_start_height(context, floors):
    if not floors:
        scene = context.scene
        floors = scene.buildings[scene.active_building_index].floors
    
    accumulated_height: float = 0
    for floor in floors:
        curve_objects = [curve for curve in floor.curves if curve.curve_object is not None]
        if not curve_objects:
            floor.start_height = accumulated_height
            floor.total_height = 0
            continue

        max_curve = max(curve_objects, key=lambda c: c.curve_object.location.z)
        min_curve = min(curve_objects, key=lambda c: c.curve_object.location.z)
        z_diff = abs(max_curve.curve_object.location.z - min_curve.curve_object.location.z)

        floor.start_height = accumulated_height
        floor.total_height = (z_diff + max_curve.height) * floor.array
        accumulated_height += floor.total_height
    return

def _combine_element_objects(self, curve, elements_collection_name, parent_collection):
    """Assemble custom element collection for a floor"""
    elements_collection = getattr(curve, elements_collection_name)
    
    if len(elements_collection.objects) == 0 and not elements_collection.existing_collection:
        self.report({'WARNING'}, "Please provide elemets!")
        return

    if curve.curve_object.name + "_" + elements_collection_name not in bpy.data.collections:
        target_collection = bpy.data.collections.new(name = curve.curve_object.name + "_" + elements_collection_name)
        parent_collection.children.link(target_collection)
    else:
        target_collection = bpy.data.collections.get(curve.curve_object.name + "_" + elements_collection_name)

    for object in target_collection.objects:
        target_collection.objects.unlink(object)

    if elements_collection.collect_method == 'OBJECTS':
        for obj in elements_collection.objects:
            target_collection.objects.link(obj.object)
    elif elements_collection.collect_method == 'EXISTING':
        for obj in elements_collection.existing_ollection.objects:
            target_collection.objects.link(obj)

    elements_collection.target_collection = target_collection

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

        all_curve_objects = []

        for floor_index, floor in enumerate(floors):
            floor.ID = floor_index
            building.active_floor_index = floor_index

            parent_collection = building.base_object.users_collection[0]

            curve_items = [curve for curve in floor.curves if curve.curve_object is not None]
            for curve_index, curve_item in enumerate(curve_items):
                curve_item.ID = curve_index
                curve_item.floor_ID = floor.ID
            all_curve_objects.extend(curve_items)

        for curve in all_curve_objects:
            curve_obj = curve.curve_object
            if curve_obj is None:
                continue

            _sync_segments_to_curves(curve)

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
            var.targets[0].data_path = 'buildings[%d].floors[%d].start_height' % (building_index, curve.floor_ID)

            _combine_element_objects(self, curve, "main_elements", parent_collection)
            _combine_element_objects(self, curve, "corner_elements", parent_collection)

            curve_obj.modifiers.clear()

            curve_attributes = curve_obj.modifiers.new(name = "BLENDERRAIL_CurveAttributes_GN", type = "NODES")
            curve_attributes.node_group = bpy.data.node_groups.get('BLENDERRAIL_CurveAttributes_GN')
            curve_attributes["Socket_2"] = curve.main_elements.target_collection
            curve_attributes["Socket_9"] = curve.corner_elements.target_collection

            fcurve = curve_obj.driver_add('modifiers["%s"]["Socket_4"]' % curve_attributes.name)
            driver = fcurve.driver
            driver.type = 'AVERAGE'
            var = driver.variables.new()
            var.name = 'height'
            var.type = 'SINGLE_PROP'
            var.targets[0].id_type = 'SCENE'
            var.targets[0].id = scene
            var.targets[0].data_path = 'buildings[%d].floors[%d].curves[%d].height' % (building_index, curve.floor_ID, curve.ID)

            fcurve = curve_obj.driver_add('modifiers["%s"]["Socket_3"]' % curve_attributes.name)
            driver = fcurve.driver
            driver.type = 'AVERAGE'
            var = driver.variables.new()
            var.name = 'array'
            var.type = 'SINGLE_PROP'
            var.targets[0].id_type = 'SCENE'
            var.targets[0].id = scene
            var.targets[0].data_path = 'buildings[%d].floors[%d].array' % (building_index, curve.floor_ID)     

            fcurve = curve_obj.driver_add('modifiers["%s"]["Socket_5"]' % curve_attributes.name)
            driver = fcurve.driver
            driver.type = 'AVERAGE'
            var = driver.variables.new()
            var.name = 'floor_ceiling'
            var.type = 'SINGLE_PROP'
            var.targets[0].id_type = 'SCENE'
            var.targets[0].id = scene
            var.targets[0].data_path = 'buildings[%d].floors[%d].curves[%d].floor_ceiling' % (building_index, curve.floor_ID, curve.ID)        
            curve_attributes.show_expanded = False

            for seg_index, segment in enumerate(curve.segments):
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
                var.targets[0].data_path = 'buildings[%d].floors[%d].curves[%d].segments[%d].element_ID' % (building_index, curve.floor_ID, curve.ID, seg_index)
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