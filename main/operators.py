import bpy
import mathutils
from mathutils.geometry import interpolate_bezier
from bpy.app.handlers import persistent
from ..utilities import find_node_group, gn_sockets, resolve_building_object as resolve



# ----------------
# Helper Functions
# ----------------

def _match_element_id_by_factor(spline_index, factor, old_assignments):
    candidates = [(spl_id, fac, elem_ID, fit, fixed) for (spl_id, fac, elem_ID, fit, fixed) in old_assignments if spl_id == spline_index]
    if not candidates:
        return (0, 'FIT', 1)
    candidates.sort(key = lambda cand: cand[1])
    for cand in candidates:
        if round(cand[1], 3) == round(factor, 3):
            return cand[2], cand[3], cand[4]

    prior = None
    for cand in candidates:
        if cand[1] < factor:
            prior = cand
        else:
            break
    if prior is None:
        return 0, 'FIT', 1
    return prior[2], prior[3], prior[4]


def _spline_cumulative_lengths(count, spline):
    if count == 0:
        return ([], 0.0)
    if count == 1:
        return ([0.0], 0.0)

    segment_lengths = []

    if spline.type == 'BEZIER':
        points = spline.bezier_points
        bezier_arc_resolution = 48
        span_pairs = [(i, i + 1) for i in range(count - 1)]
        if spline.use_cyclic_u:
            span_pairs.append((count - 1, 0))
        for i_from, i_to in span_pairs:
            point0 = points[i_from].co
            point1 = points[i_from].handle_right
            point2 = points[i_to].handle_left
            point3 = points[i_to].co
            samples = interpolate_bezier(point0, point1, point2, point3, bezier_arc_resolution)
            if len(samples) < 2:
                segment_lengths.append((point3 - point0).length)
            else:
                span_len = 0.0
                for k in range(len(samples) - 1):
                    span_len += (samples[k + 1] - samples[k]).length
                segment_lengths.append(span_len)

    else: 
        points = spline.points
        for i in range(count - 1):
            point0 = mathutils.Vector((points[i].co[0], points[i].co[1], points[i].co[2]))
            point1 = mathutils.Vector((points[i + 1].co[0], points[i + 1].co[1], points[i + 1].co[2]))
            segment_lengths.append((point1 - point0).length)
        if spline.use_cyclic_u:
            point0 = mathutils.Vector((points[-1].co[0], points[-1].co[1], points[-1].co[2]))
            point1 = mathutils.Vector((points[0].co[0], points[0].co[1], points[0].co[2]))
            segment_lengths.append((point1 - point0).length)

    total = sum(segment_lengths)
    cumulative = [0.0]

    for length in segment_lengths[:-1]:
        cumulative.append(cumulative[-1] + length)
    if not spline.use_cyclic_u:
        cumulative.append(total)

    return (cumulative, total)


def _sync_segments_to_curves(curve):
    if not curve.curve_object:
        return

    curve_data = curve.curve_object.data
    old_assignments = [(segment.spline_ID, segment.spline_factor, segment.element_index, segment.fit_method, segment.fixed_number) for segment in curve.segments]
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
                length = cumulative[point_index]
                factor = cumulative[point_index] / total
            factors.append((spline_index, factor, length))

    current = len(curve.segments)
    delta = total_points - current

    if delta == 0:
        if curve.active_segment_index > len(curve.segments) - 1:
            curve.active_segment_index = len(curve.segments) - 1
        return
    
    if delta > 0:
        for _ in range(delta):
            curve.segments.add()
    elif delta < 0:
        for _ in range(-delta):
            curve.segments.remove(len(curve.segments) - 1)

    for seg_index, segment in enumerate(curve.segments):
        segment.ID = seg_index
        spline_index, factor, length = factors[seg_index]
        element_ID, fit_method, fixed_number = _match_element_id_by_factor(spline_index, factor, old_assignments)
        segment.element_ID = element_ID if element_ID else 0
        segment.fit_method = fit_method if fit_method else 'FIT'
        segment.fixed_number = fixed_number if fixed_number else 1
        segment.spline_ID = spline_index
        segment.spline_factor = factor
        segment.spline_length = length

    if curve.active_segment_index > len(curve.segments) - 1:
        curve.active_segment_index = len(curve.segments) - 1

    return


_rematch_in_progress = False
@persistent
def on_depsgraph_update(scene, depsgraph):
    global _rematch_in_progress
    if _rematch_in_progress:
        return

    context = bpy.context
    if context.mode != 'EDIT_CURVE':
        return

    active_obj = context.active_object
    if active_obj is None or active_obj.type != 'CURVE':
        return

    resolved = resolve._resolve_building_object(context)
    if resolved is None:
        return
    _, building = resolved

    curve = None
    for floor in building.floors:
        for curve_item in floor.curves:
            if curve_item.curve_object == active_obj:
                curve = curve_item
                break
        if curve is not None:
            break

    if curve is None:
        return

    _rematch_in_progress = True
    _sync_segments_to_curves(curve)
    _rematch_in_progress = False


def _calculate_floors_start_height(context, floors, stacked):
    all_curves = []
    accumulated_height: float = 0

    for floor_index, floor in enumerate(floors):

        if floor.is_linked == True:
            all_curves_collections = [floor.curves_collection for floor in floors]
            link_modifier = gn_sockets.link_floor_modifier(floor.instance_object)
            curves_collection = gn_sockets._get_socket_value(link_modifier, "curves_collection")

            matching_index = all_curves_collections.index(curves_collection)
            source_floor = floors[matching_index]
            z_diff = accumulated_height - floor.start_height
            gn_sockets._set_socket_value(link_modifier, "height_offset", (0.0 ,0.0, z_diff))
            floor.start_height = source_floor.start_height
            floor.total_height = source_floor.total_height
            floor.instance_object.update_tag()

            accumulated_height += floor.total_height
            continue

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

        for index, curve in enumerate(curves_sorted):
            prev_curve = curves_sorted[index - 1] if index > 0 else curve
            z_diff = curve.curve_object.location.z - prev_curve.curve_object.location.z
            
            curve.curve_object.location.z += compensate
            if stacked == False or index == 0 or z_diff < 0.1:
                continue
            curve.curve_object.location.z = prev_curve.curve_object.location.z + prev_curve.height

        for curve_index, curve in enumerate(curves):
            curve.ID = curve_index
            curve.floor_ID = floor_index
        
        z_diff = abs(max_curve_position + max_curve_height - min_curve_position)
        floor.maximum_height = z_diff
        floor.total_height = z_diff * floor.array
        accumulated_height += floor.total_height

        all_curves.extend(curves)

    return all_curves


def _assign_curve_elements(self, context, building, curve, element_type):
    collection = building.elements_collection
    elements_collection = getattr(curve, element_type)

    if len(elements_collection.objects) == 0:
        self.report({'WARNING'}, "No elements assigned. Please provide elements")
        return

    for element_index, element in enumerate(elements_collection.objects):
        element.ID = element_index
        curve_element = curve.curve_object.modifiers.new(name = "UTM.Builder_CurveElements_GN", type = "NODES")
        curve_element_gn = find_node_group.link_gn_from_library("UTM.Builder_CurveElements_GN")[0]
        curve_element.node_group = curve_element_gn
        curve_element.show_expanded = False

        element_name = bpy.data.objects.get(element.object.name) if element.object is not None else None

        gn_sockets._set_socket_value(curve_element, "element_type", element_type)
        gn_sockets._set_socket_value(curve_element, "object", element_name)
        gn_sockets._set_socket_value(curve_element, "is_empty", element.is_empty)
        gn_sockets._set_socket_value(curve_element, "empty_bounds", element.empty_bounds)
        gn_sockets._set_socket_value(curve_element, "correct_uv", element.correct_uv)
        gn_sockets._set_socket_value(curve_element, "up_stretched", element.up_stretched)

        element_object = element.object if element.object else None
        if element_object is None:
            continue
        elif collection not in element.object.users_collection:
            collection.objects.link(element.object)

    return



# --------------------
# Operators: Buildings
# --------------------

class UTMBUILDER_OT_evaluate_building(bpy.types.Operator):
    bl_idname = "utmbuilder.evaluate_building"
    bl_label = "Evaluate building"
    bl_description = "For each floor: set segments, assign its curve with the required modifiers and link elements"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}


    def execute(self, context):
        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            self.report({"ERROR"}, "No building found")
            return {"CANCELLED"}
        base_object, building = resolved

        old_active_floor = building.active_floor_index
        floors = building.floors

        construct_modifier = gn_sockets.construct_modifier(base_object)
        gn_sockets._set_socket_value(construct_modifier, "floors_collection", building.floors_collection)

        if len(floors) == 0:
            self.report({"WARNING"}, "Active building has no floors")
            return {"CANCELLED"}

        all_curves = _calculate_floors_start_height(context, floors, False)

        for floor_index, floor in enumerate(floors):
            instance_empty = floor.instance_object
            if instance_empty is None:
                continue
            link_modifier = gn_sockets.link_floor_modifier(instance_empty)
            gn_sockets._set_socket_value(link_modifier, "floor_visibility", floor.floor_visibility)

        for curve in all_curves:
            curve_obj = curve.curve_object
            if curve_obj is None:
                continue
            if floors[curve.floor_ID].is_linked == True:
                continue

            _sync_segments_to_curves(curve)

            mw = curve_obj.matrix_world.copy()
            curve_obj.parent = base_object
            curve_obj.matrix_world = mw
            curve_obj.modifiers.clear()

            curve_attributes = curve_obj.modifiers.new(name = "UTM.Builder_CurveAttributes_GN", type = "NODES")
            curve_attributes_gn = find_node_group.link_gn_from_library("UTM.Builder_CurveAttributes_GN")[0]
            curve_attributes.node_group = curve_attributes_gn
            curve_attributes.show_expanded = False

            floor = floors[curve.floor_ID]
            gn_sockets._set_socket_value(curve_attributes, "floor_visibility", floor.floor_visibility)
            gn_sockets._set_socket_value(curve_attributes, "array", floor.array)
            gn_sockets._set_socket_value(curve_attributes, "maximum_height", floor.maximum_height)

            gn_sockets._set_socket_value(curve_attributes, "ID", curve.ID)
            gn_sockets._set_socket_value(curve_attributes, "main_inset", curve.main_inset)
            gn_sockets._set_socket_value(curve_attributes, "height", curve.height)

            gn_sockets._set_socket_value(curve_attributes, "floor_ceiling", curve.floor_ceiling)
            gn_sockets._set_socket_value(curve_attributes, "thickness", curve.thickness)
            gn_sockets._set_socket_value(curve_attributes, "direction_bottom", curve.direction_bottom)
            gn_sockets._set_socket_value(curve_attributes, "direction_top", curve.direction_top)

            gn_sockets._set_socket_value(curve_attributes, "top_material", curve.top_material)
            gn_sockets._set_socket_value(curve_attributes, "sides_material", curve.sides_material)
            gn_sockets._set_socket_value(curve_attributes, "bottom_material", curve.bottom_material)


            _assign_curve_elements(self, context, building, curve, "main_elements")
            _assign_curve_elements(self, context, building, curve, "corner_elements")


            for segment_index, segment in enumerate(curve.segments):
                element_id = curve_obj.modifiers.new(name = "UTM.Builder_ElementID_GN", type = "NODES")
                element_id_gn = find_node_group.link_gn_from_library("UTM.Builder_ElementID_GN")[0]
                element_id.node_group = element_id_gn
                segment.ID = segment_index
                gn_sockets._set_socket_value(element_id, "segment_index", segment.ID)
                element_id.show_expanded = False

                gn_sockets._set_socket_value(element_id, "fit_method", segment.fit_method)
                gn_sockets._set_socket_value(element_id, "fixed_number", segment.fixed_number)
                gn_sockets._set_socket_value(element_id, "select_method", segment.select_method)
                gn_sockets._set_socket_value(element_id, "select_per_segment", segment.select_per_segment)
                gn_sockets._set_socket_value(element_id, "sequence_offset", segment.sequence_offset)
                gn_sockets._set_socket_value(element_id, "random_index", segment.random_index)
                gn_sockets._set_socket_value(element_id, "element_index", segment.element_index)

        building.active_floor_index = old_active_floor

        self.report({"INFO"}, "Generated %d floor(s)" % len(floors))
        return {"FINISHED"}



class UTMBUILDER_OT_generate_building(bpy.types.Operator):
    bl_idname = "utmbuilder.generate_building"
    bl_label = "Generate Building"
    bl_description = "Add base object with construct modifier"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}


    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        else:
            return True
        
    def _next_building_name(self):
        count = sum(1 for obj in bpy.data.objects if resolve._is_utm_building(obj))
        return "build_" + str(count + 1)

    def execute(self, context):
        construct = find_node_group.link_gn_from_library("UTM.Builder_Construct_GN")

        if construct[0] is None:
            self.report({"ERROR"}, construct[1])
            return {"CANCELLED"}
        
        bpy.ops.mesh.primitive_cube_add(size = 2, enter_editmode = False, align = 'WORLD', location = context.scene.cursor.location, scale = (1, 1, 1))
        base_object = context.view_layer.objects.active

        modifier = base_object.modifiers.new(name = "UTM.Builder_Construct_GN", type = "NODES")
        modifier.node_group = construct[0]
        modifier.show_expanded = False

        building = base_object.utm_building
        building.is_utm_building = True
        building.name = self._next_building_name()
        base_object.name = building.name + "_Constructor"

        building_collection = bpy.data.collections.new(building.name)
        building.building_collection = building_collection
        context.scene.collection.children.link(building_collection)
        building_collection.objects.link(base_object)
        for parent in base_object.users_collection:
            if parent != building_collection:
                parent.objects.unlink(base_object)


        floors_collection = bpy.data.collections.new(building.name + "_Floors")
        context.scene.collection.children.link(floors_collection)
        building.floors_collection = floors_collection
        building_collection.children.link(floors_collection)
        context.scene.collection.children.unlink(floors_collection)

        elements_collection = bpy.data.collections.new(building.name + "_Elements")
        context.scene.collection.children.link(elements_collection)
        building.elements_collection = elements_collection
        building_collection.children.link(elements_collection)
        context.scene.collection.children.unlink(elements_collection)

        gn_sockets._set_socket_value(modifier, "floors_collection", floors_collection)

        bpy.ops.utmbuilder.add_floor()

        floor = building.floors[0]
        curves_collection = bpy.data.collections.new(building.name + "_Floor_" + str(floor.ID) + "_Curves")
        context.scene.collection.children.link(curves_collection)
        floor.curves_collection = curves_collection
        floors_collection.children.link(curves_collection)
        context.scene.collection.children.unlink(curves_collection)

        context.view_layer.objects.active = base_object
        bpy.ops.utmbuilder.add_curve_object()
        bpy.ops.object.mode_set(mode = 'OBJECT')

        context.view_layer.objects.active = base_object
        base_object.select_set(True)
        bpy.ops.utmbuilder.evaluate_building()
        
        return {"FINISHED"}



class UTMBUILDER_OT_remove_building(bpy.types.Operator):
    bl_idname = "utmbuilder.remove_building"
    bl_label = "Remove Building"
    bl_description = "Unregister the active ULTEAMMATE building (geometry and collections are kept in the file)"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}


    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            return False
        else:
            return True

    def execute(self, context):
        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            return
        _, building = resolved
        building.floors.clear()
        building.active_floor_index = 0
        building.is_utm_building = False

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width = 500)

    def draw(self, context):
        layout = self.layout
        layout.label(text = "Are you ABSOLUTELY CERTAIN you want to delete the active building?", icon = 'ERROR')



class UTMBUILDER_OT_select_base_object(bpy.types.Operator):
    bl_idname = "utmbuilder.select_base_object"
    bl_label = "Select Constructor"
    bl_description = "Select the building constructor object"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}


    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            return False
        else:
            return True

    def execute(self, context):
        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            return
        base_object, _ = resolved

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = base_object
        base_object.select_set(True)

        return {"FINISHED"}



class UTMBUILDER_OT_building_settings(bpy.types.Operator):
    bl_idname = "utmbuilder.building_settings"
    bl_label = "Building Settings"
    bl_description = "Edit building properties"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}


    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        resolved = resolve._resolve_building_object(context)
        if resolved is None:
            return False
        else:
            return True

    def execute(self, context):
        '''This executes NOTHING. Sole purpose of this operator is to expose the active building's properties in a pop-up dialog :)'''
        return {"FINISHED"}

    def invoke(self, context, event):
        resolved = resolve._resolve_building_object(context)
        _, building = resolved
        return context.window_manager.invoke_props_dialog(self, title = building.name, width = 400)

    def draw(self, context):
        building = self._building(context)
        if building is None:
            return

        layout = self.layout
        properties_column = layout.column(align = True)
        properties_column.alignment = 'RIGHT'

        properties_column.prop(building, "name", text = "Building Name", icon = 'FILE_FONT')
        properties_column.prop(building, "building_collection", text = "Building Collection", icon = 'OUTLINER_COLLECTION')
        properties_column.prop(building, "floors_collection", text = "Floors Collection", icon = 'OUTLINER_COLLECTION')
        properties_column.prop(building, "elements_collection", text = "Elements Collection", icon = 'OUTLINER_COLLECTION')