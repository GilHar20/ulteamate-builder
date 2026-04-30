import bpy
import mathutils
from mathutils.geometry import interpolate_bezier
from bpy.app.handlers import persistent
from ..preferences import find_node_group



# ----------------
# Helper Functions
# ----------------

def _match_element_id_by_factor(spline_index, factor, old_assignments):
    candidates = [(fac, element_ID) for (spl_ix, fac, element_ID) in old_assignments if spl_ix == spline_index]
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    for c in candidates:
        if round(c[0], 3) == round(factor, 3):
            return c[1]

    prior = None
    for c in candidates:
        if c[0] < factor:
            prior = c
        else:
            break
    return prior[1] if prior is not None else None


def _spline_cumulative_lengths(count, spline):
    if count == 0:
        return ([], 0.0)
    if count == 1:
        return ([0.0], 0.0)

    segment_lengths = []

    if spline.type == 'BEZIER':
        pts = spline.bezier_points
        bezier_arc_resolution = 48
        span_pairs = [(i, i + 1) for i in range(count - 1)]
        if spline.use_cyclic_u:
            span_pairs.append((count - 1, 0))
        for i_from, i_to in span_pairs:
            p0 = pts[i_from].co
            p1 = pts[i_from].handle_right
            p2 = pts[i_to].handle_left
            p3 = pts[i_to].co
            samples = interpolate_bezier(p0, p1, p2, p3, bezier_arc_resolution)
            if len(samples) < 2:
                segment_lengths.append((p3 - p0).length)
            else:
                span_len = 0.0
                for k in range(len(samples) - 1):
                    span_len += (samples[k + 1] - samples[k]).length
                segment_lengths.append(span_len)

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
    if not curve.curve_object:
        return
    
    curve_data = curve.curve_object.data
    old_assignments = [(segment.spline_ID, segment.spline_factor, segment.element_ID) for segment in curve.segments]
    factors = []
    total_points = 0

    for spline_index, spline in enumerate(curve_data.splines):
        if spline.type == 'BEZIER':
            count = len(spline.bezier_points)
        else:
            count = len(spline.points)
        segment_count = count if spline.use_cyclic_u else max(count - 1, 0)
        total_points += segment_count        

        cumulative, total = _spline_cumulative_lengths(count, spline)

        for point_index in range(segment_count):
            if total <= 0 or point_index >= len(cumulative):
                factor = 0.0
            else:
                factor = cumulative[point_index] / total
            factors.append((spline_index, factor))

    current = len(curve.segments)
    delta = total_points - current

    if delta == 0:
        return
    
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

    if bpy.context.mode != 'EDIT_CURVE':
        return

    _rematch_in_progress = True

    building = scene.buildings[scene.active_building_index]
    floor = building.floors[building.active_floor_index]
    curve = floor.curves[floor.active_curve_index]

    _sync_segments_to_curves(curve)
        
    _rematch_in_progress = False


def _calculate_floors_start_height(context, floors, stacked):
    all_curves = []
    accumulated_height: float = 0

    for floor_index, floor in enumerate(floors):
        #floor.ID = floor_index

        curves = [curve for curve in floor.curves if curve.curve_object is not None]
        if not curves:
            floor.start_height = accumulated_height
            floor.total_height = 0
            continue
        curves_sorted = sorted(curves, key=lambda c: c.curve_object.location.z)

        min_curve = min(curves, key=lambda c: c.curve_object.location.z)
        min_curve_position = min_curve.curve_object.location.z
        max_curve = max(curves, key=lambda c: c.curve_object.location.z + c.height)
        max_curve_position = max_curve.curve_object.location.z
        max_curve_height = max_curve.height

        floor.start_height = accumulated_height
        compensate = floor.start_height - min_curve_position

        for index, curve in enumerate(curves):
            sorted_index = curves_sorted.index(curve)
            prev_curve = curves_sorted[sorted_index - 1] if sorted_index > 0 else curve
            z_diff = curve.curve_object.location.z - prev_curve.curve_object.location.z
            prev_floor = floors[floor_index - 1] if floor_index > 0 else floor

            if z_diff < 0.1:
                curve.curve_object.location.z = prev_curve.curve_object.location.z
            
            elif stacked == True:
                curve.curve_object.location.z = accumulated_height #prev_curve.curve_object.location.z + prev_curve.height
            
            else:
                curve.curve_object.location.z = accumulated_height #curve.curve_object.location.z + compensate

            curve.ID = index
            curve.floor_ID = floor.ID
        
        z_diff = abs(max_curve_position + max_curve_height - min_curve_position)
        floor.total_height = z_diff * floor.array
        accumulated_height += floor.total_height

        all_curves.extend(curves)
    
    return all_curves


def _set_attribute_driver(self, context, item, attribute, path, var_name):
    scene = context.scene

    fcurve = item.driver_add(attribute)
    driver = fcurve.driver
    driver.type = 'AVERAGE'
    var = driver.variables.new()
    var.name = var_name
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'SCENE'
    var.targets[0].id = scene
    var.targets[0].data_path = path
    return


def _assign_curve_elements(self, context, curve, element_type):
    scene = context.scene
    building = scene.buildings[scene.active_building_index]
    collection = building.elements_collection
    elements_collection = getattr(curve, element_type)
    
    collect_method = 0
    match element_type:
        case "main_elements":
            collect_method = 0
        case "corner_elements":
            collect_method = 1

    if elements_collection.collect_method == 'OBJECTS':
        if len(elements_collection.objects) == 0:
            self.report({'WARNING'}, "No elements assigned. Please provide elements")
            return

        for element in elements_collection.objects:
            if not element.object:
                continue
            
            # TEMP CODE TO BE REMOVED
            element.element_type = element_type

            curve_elements = curve.curve_object.modifiers.new(name = "BLENDERRAIL_CurveElements_GN", type = "NODES")
            curve_elements_gn = find_node_group.link_gn_from_library("BLENDERRAIL_CurveElements_GN")[0]
            curve_elements.node_group = curve_elements_gn
            
            curve_elements["Socket_5"] = collect_method
            curve_elements["Socket_4"] = bpy.data.objects.get(element.object.name)
            curve_elements["Socket_6"] = element.up_stretched

            if collection not in element.object.users_collection:
                collection.objects.link(element.object)

            curve_elements.show_expanded = False

    elif elements_collection.collect_method == 'COLLECTION':
        if len(elements_collection.existing_collection.objects) == 0:
            self.report({'WARNING'}, "No elements are linked into the assigned collection")
            return
        
        for element in elements_collection.exiiting_collection:
            if not element.object:
                continue

            # TEMP CODE TO BE REMOVED
            element.element_type = element_type

            curve_elements = curve.curve_object.modifiers.new(name = "BLENDERRAIL_CurveElements_GN", type = "NODES")
            curve_elements_gn = find_node_group.link_gn_from_library("BLENDERRAIL_CurveElements_GN")[0]
            curve_elements.node_group = curve_elements_gn
            
            curve_elements["Socket_5"] = collect_method
            curve_elements["Socket_4"] = bpy.data.objects.get(element.object.name)

            if collection not in element.object.users_collection:            
                collection.objects.link(element.object)

            # TEMO CODE TO BE REMOVED
            element.host_curve = curve.curve_object

            curve_elements.show_expanded = False

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

        floors_collection = building.floors_collection

        # TEMP CODE TO BE REMOVED
        for floor in floors:
            if floor.curves_collection == None:
                floor.curves_collection = bpy.data.collections.new(building.name + "_" + str(floor.ID))
                building.floors_collection.children.link(floor.curves_collection)

        all_curves = _calculate_floors_start_height(context, floors, False)

        for curve in all_curves:
            curve_obj = curve.curve_object
            if curve_obj is None:
                continue
            if floors[curve.floor_ID].is_linked == True:
                continue

            # TEMP CODE TO BE REMOVED
            floor = floors[curve.floor_ID]
            target = floor.curves_collection
            # Copy first, then unlink (don't mutate while iterating original collection list)
            for col in list(curve_obj.users_collection):
                if col != target:
                    col.objects.unlink(curve_obj)
            if target not in curve_obj.users_collection:
                target.objects.link(curve_obj)

            _sync_segments_to_curves(curve)


            if curve_obj.parent != building.base_object:
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = building.base_object
                building.base_object.select_set(True)
                curve_obj.select_set(True)
                bpy.ops.object.parent_no_inverse_set(keep_transform = True)

            curve_obj.modifiers.clear()

            curve_attributes = curve_obj.modifiers.new(name = "BLENDERRAIL_CurveAttributes_GN", type = "NODES")
            curve_attributes_gn = find_node_group.link_gn_from_library("BLENDERRAIL_CurveAttributes_GN")[0]
            curve_attributes.node_group = curve_attributes_gn
            curve_attributes.show_expanded = False

            attribute = 'modifiers["%s"]["Socket_11"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].curves[%d].select_method' % (building_index, curve.floor_ID, curve.ID)
            _set_attribute_driver(self, context, curve_obj, attribute, path, "select_method")

            attribute = 'modifiers["%s"]["Socket_14"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].curves[%d].select_per_segment' % (building_index, curve.floor_ID, curve.ID)
            _set_attribute_driver(self, context, curve_obj, attribute, path, "select_per_segment")
            
            attribute = 'modifiers["%s"]["Socket_12"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].curves[%d].sequence_offset' % (building_index, curve.floor_ID, curve.ID)
            _set_attribute_driver(self, context, curve_obj, attribute, path, "sequence_offset")

            attribute = 'modifiers["%s"]["Socket_13"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].curves[%d].random_index' % (building_index, curve.floor_ID, curve.ID)
            _set_attribute_driver(self, context, curve_obj, attribute, path, "random_index")

            attribute = 'modifiers["%s"]["Socket_3"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].array' % (building_index, curve.floor_ID)
            _set_attribute_driver(self, context, curve_obj, attribute, path, "array")

            attribute = 'modifiers["%s"]["Socket_4"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].curves[%d].height' % (building_index, curve.floor_ID, curve.ID)
            _set_attribute_driver(self, context, curve_obj, attribute, path, "height")

            attribute = 'modifiers["%s"]["Socket_10"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].curves[%d].inset' % (building_index, curve.floor_ID, curve.ID)
            _set_attribute_driver(self, context, curve_obj, attribute, path, "inset")

            attribute = 'modifiers["%s"]["Socket_5"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].curves[%d].floor_ceiling' % (building_index, curve.floor_ID, curve.ID)      
            _set_attribute_driver(self, context, curve_obj, attribute, path, "floor_ceiling")

            attribute = 'modifiers["%s"]["Socket_15"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].curves[%d].thickness' % (building_index, curve.floor_ID, curve.ID)          
            _set_attribute_driver(self, context, curve_obj, attribute, path, "thickness")

            attribute = 'modifiers["%s"]["Socket_16"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].curves[%d].direction_bottom' % (building_index, curve.floor_ID, curve.ID)
            _set_attribute_driver(self, context, curve_obj, attribute, path, "direction_bottom")

            attribute = 'modifiers["%s"]["Socket_17"]' % curve_attributes.name
            path = 'buildings[%d].floors[%d].curves[%d].direction_top' % (building_index, curve.floor_ID, curve.ID) 
            _set_attribute_driver(self, context, curve_obj, attribute, path, "direction_top")


            _assign_curve_elements(self, context, curve, "main_elements")
            _assign_curve_elements(self, context, curve, "corner_elements")


            for seg_index, segment in enumerate(curve.segments):
                element_id = curve_obj.modifiers.new(name = "BLENDERRAIL_ElementID_GN", type = "NODES")
                element_id_gn = find_node_group.link_gn_from_library("BLENDERRAIL_ElementID_GN")[0]
                element_id.node_group = element_id_gn
                element_id["Socket_2"] = segment.ID
                element_id.show_expanded = False

                attribute = 'modifiers["%s"]["Socket_4"]' % element_id.name
                path = 'buildings[%d].floors[%d].curves[%d].segments[%d].fit_method' % (building_index, curve.floor_ID, curve.ID, seg_index)
                _set_attribute_driver(self, context, curve_obj, attribute, path, "fit_method")

                attribute = 'modifiers["%s"]["Socket_5"]' % element_id.name
                path = 'buildings[%d].floors[%d].curves[%d].segments[%d].fixed_number' % (building_index, curve.floor_ID, curve.ID, seg_index)
                _set_attribute_driver(self, context, curve_obj, attribute, path, "fixed_number")

                attribute = 'modifiers["%s"]["Socket_3"]' % element_id.name
                path = 'buildings[%d].floors[%d].curves[%d].segments[%d].element_ID' % (building_index, curve.floor_ID, curve.ID, seg_index)
                _set_attribute_driver(self, context, curve_obj, attribute, path, "element_ID")

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

        bpy.ops.mesh.primitive_cube_add(size = 2, enter_editmode = False, align = 'WORLD', location = context.scene.cursor.location, scale = (1, 1, 1))
        cube_obj = context.view_layer.objects.active

        construct = find_node_group.link_gn_from_library("BLENDERRAIL_Construct_GN")[0]

        if construct is None:
            self.report({"ERROR"}, "Node group 'BLENDERRAIL_Construct_GN' not found")
            return {"CANCELLED"}

        modifier = cube_obj.modifiers.new(name = "BLENDERRAIL_Construct_GN", type = "NODES")
        modifier.node_group = construct
        modifier.show_expanded = False

        building = buildings.add()
        building.name += "_" + str(len(context.scene.buildings))
        building.base_object = cube_obj
        cube_obj.name = building.name + "_Constructor"
        scene.active_building_index = len(buildings) - 1

        building_collection = bpy.data.collections.new(building.name)
        building.building_collection = building_collection
        context.scene.collection.children.link(building_collection)
        building_collection.objects.link(cube_obj)

        floors_collection = bpy.data.collections.new(building.name + "_Floors")
        building.floors_collection = floors_collection
        building_collection.children.link(floors_collection)

        elements_collection = bpy.data.collections.new(building.name + "_Elements")
        building.elements_collection = elements_collection
        building_collection.children.link(elements_collection)

        modifier["Socket_2"] = floors_collection

        bpy.ops.blenderrail.add_floor()
        floor = building.floors[0]

        curve = bpy.ops.blenderrail.add_curve_object()
        floor.curves_collection.objects.link(curve)

        bpy.ops.curve.primitive_bezier_circle_add(enter_editmode = False, align = 'WORLD', location = context.scene.cursor.location, scale = (1, 1, 1))
        bpy.ops.transform.resize(value = (10.0, 10.0, 10.0), orient_type = 'GLOBAL')
        bpy.ops.object.transform_apply(location = False, rotation = False, scale = True)
        curve_obj = context.view_layer.objects.active
        building.floors[0].curves[0].curve_object = curve_obj

        bpy.ops.blenderrail.evaluate_building()

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